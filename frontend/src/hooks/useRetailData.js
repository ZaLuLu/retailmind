import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { IS_DEMO, DEMO_USER } from '../config'

export const EMPTY_SUMMARY = {
  total_revenue: 0,
  total_cogs: 0,
  gross_profit: 0,
  overall_margin_pct: 0,
  mom_revenue_change_pct: 0,
  num_sales: 0,
  top_products: [],
  category_breakdown: [],
  demand_signals: [],
  dead_stock_alerts: [],
  margin_erosion_alerts: [],
  ai_insight: 'Analyzing sales data…',
}

export function useRetailData(isAuthenticated, showToast, handleLogout) {
  const [user, setUser] = useState(
    IS_DEMO
      ? { fullName: DEMO_USER.fullName, storeName: DEMO_USER.storeName, currency: DEMO_USER.currency }
      : { fullName: '', storeName: '', currency: 'INR' }
  )
  const [sales, setSales] = useState([])
  const [summary, setSummary] = useState(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(false)
  const [stores, setStores] = useState([])
  const [selectedStore, setSelectedStore] = useState(null)
  const [hasCustomData, setHasCustomData] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [isOnboarded, setIsOnboarded] = useState(IS_DEMO)

  useEffect(() => {
    if (isAuthenticated) {
      fetchUserData()
    }
  }, [isAuthenticated])

  // Automatically reset all data states when logging out
  useEffect(() => {
    if (!isAuthenticated) {
      setUser(IS_DEMO
        ? { fullName: DEMO_USER.fullName, storeName: DEMO_USER.storeName, currency: DEMO_USER.currency }
        : { fullName: '', storeName: '', currency: 'INR' }
      )
      setSales([])
      setSummary(EMPTY_SUMMARY)
      setStores([])
      setSelectedStore(null)
      setHasCustomData(false)
      setIsOnboarded(IS_DEMO)
    }
  }, [isAuthenticated])

  const fetchUserData = async (period, dateFrom, dateTo, storeIdOverride, forceRefresh = false) => {
    setLoading(true)
    try {
      let data = { full_name: user.fullName, store_name: user.storeName, currency: user.currency, is_onboarded: isOnboarded }
      let fetchedStores = stores
      let activeStore = selectedStore

      const skipProfileAndStores = !forceRefresh && user.fullName !== '' && stores.length > 0

      if (!skipProfileAndStores) {
        // 1. User profile
        const profileData = await api.get('/users/me')
        data = profileData
        setUser({
          fullName: profileData.full_name || '',
          storeName: profileData.store_name || '',
          currency: profileData.currency || 'INR',
        })
        setIsOnboarded(profileData.is_onboarded)
      }

      if (data.is_onboarded) {
        if (!skipProfileAndStores) {
          // 1.5 Fetch stores
          try {
            fetchedStores = await api.getStores()
          } catch (storeErr) {
            console.error("Failed to fetch stores", storeErr)
          }

          // If no stores exist, create one from user's storeName
          if (fetchedStores.length === 0) {
            try {
              const defaultStore = await api.createStore({
                name: data.store_name || 'My First Store',
                location: 'Primary'
              })
              fetchedStores = [defaultStore]
              activeStore = defaultStore
            } catch (createErr) {
              console.error("Failed to create default store", createErr)
            }
          } else {
            activeStore = fetchedStores[0]
          }

          setStores(fetchedStores)
          setSelectedStore(activeStore)
        }

        if (storeIdOverride) {
          activeStore = fetchedStores.find(s => s.id === storeIdOverride) || null
          setSelectedStore(activeStore)
        } else if (selectedStore) {
          activeStore = fetchedStores.find(s => s.id === selectedStore.id) || null
          setSelectedStore(activeStore)
        }

        const activeStoreId = activeStore?.id || null

        // 2. Retail intelligence summary
        const summaryData = await api.getRetailSummary(period, dateFrom, dateTo, activeStoreId)
        setSummary(summaryData)

        // 3. Sales ledger
        const salesData = await api.getRetailSales(200, 0, '', '', dateFrom, dateTo, activeStoreId)
        setSales(salesData)
      }
    } catch (err) {
      console.error('Failed to fetch user data', err)
      if (err.status === 401) {
        handleLogout()
      } else if (err.type === 'server') {
        showToast('error', 'Server error — could not load your data. Please try again.')
      } else if (!err.status) {
        showToast('error', 'Connection failed — check your network.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSelectStore = async (storeId) => {
    await fetchUserData(summary?.period, summary?.date_from, summary?.date_to, storeId)
  }

  const handleCreateStore = async (name, location) => {
    try {
      const newStore = await api.createStore({ name, location })
      await fetchUserData(summary?.period, summary?.date_from, summary?.date_to, newStore.id, true)
      showToast('success', `Store "${name}" created successfully!`)
    } catch (err) {
      showToast('error', err.message || 'Failed to create store.')
    }
  }

  const handleOnboardingComplete = async (data) => {
    try {
      await api.post('/onboarding/complete', {
        full_name: data.fullName,
        store_name: data.storeName,
        initial_balance: 0,
        currency: data.currency || 'INR',
        budgets: {},
      })
      await fetchUserData(undefined, undefined, undefined, undefined, true)
    } catch (err) {
      showToast('error', err.message || 'Onboarding failed. Please try again.')
    }
  }

  const handleSettingsSave = async (updatedData, onSavedCallback) => {
    try {
      await api.patch('/users/me', {
        full_name: updatedData.fullName,
        store_name: updatedData.storeName,
        currency: updatedData.currency,
      })
      await fetchUserData(summary?.period, summary?.date_from, summary?.date_to, selectedStore?.id, true)
      showToast('success', 'Settings saved.')
      if (onSavedCallback) onSavedCallback()
    } catch (err) {
      showToast('error', err.message || 'Failed to update settings.')
    }
  }

  const handleDemoUploadComplete = () => {
    setHasCustomData(true)
    setShowImport(false)
    fetchUserData(undefined, undefined, undefined, undefined, true)
    showToast('success', 'Your data is live! Showing your insights.')
  }

  const handleDemoRestore = async () => {
    try {
      await api.demoRestore()
      setHasCustomData(false)
      await fetchUserData(undefined, undefined, undefined, undefined, true)
      showToast('success', 'Demo data restored.')
    } catch (err) {
      showToast('error', err.message || 'Restore failed.')
    }
  }

  return {
    user,
    setUser,
    sales,
    setSales,
    summary,
    setSummary,
    loading,
    setLoading,
    stores,
    setStores,
    selectedStore,
    setSelectedStore,
    hasCustomData,
    setHasCustomData,
    showImport,
    setShowImport,
    isOnboarded,
    setIsOnboarded,
    fetchUserData,
    handleSelectStore,
    handleCreateStore,
    handleOnboardingComplete,
    handleSettingsSave,
    handleDemoUploadComplete,
    handleDemoRestore,
  }
}
