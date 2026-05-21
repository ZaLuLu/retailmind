import React, { useState, useEffect } from 'react'
import OnboardingWizard from './components/OnboardingWizard'
import AdvisorChat from './components/AdvisorChat'
import Login from './components/Login'
import Register from './components/Register'
import IntelligenceDashboard from './components/IntelligenceDashboard'
import { api } from './services/api'
import { useToast } from './components/Toast'
import './App.css'

const EMPTY_SUMMARY = {
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
  ai_insight: 'Connecting to intelligence bureau…',
}

function App() {
  const { showToast } = useToast()
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'))
  const [authView, setAuthView] = useState('login') // 'login' | 'register'
  const [isOnboarded, setIsOnboarded] = useState(false)

  const [showSettings, setShowSettings] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [user, setUser] = useState({ fullName: '', storeName: '', currency: 'INR' })
  const [sales, setSales] = useState([])
  const [summary, setSummary] = useState(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(false)
  const [stores, setStores] = useState([])
  const [selectedStore, setSelectedStore] = useState(null)

  // Listen for forced logout from token refresh failure
  useEffect(() => {
    const handleForcedLogout = () => {
      handleLogout()
      showToast('warning', 'Your session expired. Please log in again.')
    }
    window.addEventListener('auth:logout', handleForcedLogout)
    return () => window.removeEventListener('auth:logout', handleForcedLogout)
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      fetchUserData()
    }
  }, [isAuthenticated])

  const fetchUserData = async (period, dateFrom, dateTo, storeIdOverride) => {
    setLoading(true)
    try {
      // 1. User profile
      const data = await api.get('/users/me')
      setUser({
        fullName: data.full_name || '',
        storeName: data.store_name || '',
        currency: data.currency || 'INR',
      })
      setIsOnboarded(data.is_onboarded)

      if (data.is_onboarded) {
        // 1.5 Fetch stores
        let fetchedStores = []
        try {
          fetchedStores = await api.getStores()
        } catch (storeErr) {
          console.error("Failed to fetch stores", storeErr)
        }

        let activeStore = null
        if (storeIdOverride) {
          activeStore = fetchedStores.find(s => s.id === storeIdOverride) || null
        } else if (selectedStore) {
          activeStore = fetchedStores.find(s => s.id === selectedStore.id) || null
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
        } else if (!activeStore) {
          activeStore = fetchedStores[0]
        }

        setStores(fetchedStores)
        setSelectedStore(activeStore)

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
    // Preserve current filters when switching stores
    await fetchUserData(summary?.period, summary?.date_from, summary?.date_to, storeId)
  }

  const handleCreateStore = async (name, location) => {
    try {
      const newStore = await api.createStore({ name, location })
      await fetchUserData(summary?.period, summary?.date_from, summary?.date_to, newStore.id)
      showToast('success', `Store "${name}" created successfully!`)
    } catch (err) {
      showToast('error', err.message || 'Failed to create store.')
    }
  }

  // ── Auth handlers ──────────────────────────────────────────────────────────
  const handleLogin = async (email, password) => {
    await api.login(email, password)
    setIsAuthenticated(true)
  }

  const handleRegister = async (email, password) => {
    await api.register(email, password)
    setAuthView('login')
  }

  const handleLogout = () => {
    api.logout()
    setIsAuthenticated(false)
    setUser({ fullName: '', storeName: '', currency: 'INR' })
    setSales([])
    setSummary(EMPTY_SUMMARY)
  }

  // ── Onboarding ─────────────────────────────────────────────────────────────
  const handleOnboardingComplete = async (data) => {
    try {
      await api.post('/onboarding/complete', {
        full_name: data.fullName,
        store_name: data.storeName,
        initial_balance: 0,
        currency: data.currency || 'INR',
        budgets: {},
      })
      await fetchUserData()
    } catch (err) {
      showToast('error', err.message || 'Onboarding failed. Please try again.')
    }
  }

  // ── Settings ───────────────────────────────────────────────────────────────
  const handleSettingsSave = async (updatedData) => {
    try {
      await api.patch('/users/me', {
        full_name: updatedData.fullName,
        store_name: updatedData.storeName,
        currency: updatedData.currency,
      })
      await fetchUserData()
      setShowSettings(false)
      showToast('success', 'Settings saved.')
    } catch (err) {
      showToast('error', err.message || 'Failed to update settings.')
    }
  }

  // ── Routing ────────────────────────────────────────────────────────────────
  if (!isAuthenticated) {
    return authView === 'login'
      ? <Login onLogin={handleLogin} onSwitch={() => setAuthView('register')} />
      : <Register onRegister={handleRegister} onSwitch={() => setAuthView('login')} />
  }

  if (!isOnboarded) {
    return <OnboardingWizard onComplete={handleOnboardingComplete} />
  }

  return (
    <div className="app-root">
      {/* Settings modal — inline, lightweight */}
      {showSettings && (
        <div className="settings-overlay">
          <div className="settings-modal">
            <div className="settings-header">
              <h2>Store Settings</h2>
              <button className="close-btn" onClick={() => setShowSettings(false)}>✕</button>
            </div>
            <SettingsForm user={user} onSave={handleSettingsSave} onCancel={() => setShowSettings(false)} />
          </div>
        </div>
      )}

      {showChat && (
        <AdvisorChat
          summary={summary}
          onClose={() => setShowChat(false)}
        />
      )}

      <IntelligenceDashboard
        summary={summary}
        sales={sales}
        user={user}
        currency={user.currency}
        loading={loading}
        stores={stores}
        selectedStore={selectedStore}
        onSelectStore={handleSelectStore}
        onCreateStore={handleCreateStore}
        onShowSettings={() => setShowSettings(true)}
        onLogout={handleLogout}
        onShowChat={() => setShowChat(true)}
        onRefresh={fetchUserData}
      />
    </div>
  )
}

// ── Inline Settings Form ───────────────────────────────────────────────────
const CURRENCIES = [
  { code: 'INR', label: '₹ INR — Indian Rupee' },
  { code: 'USD', label: '$ USD — US Dollar' },
  { code: 'EUR', label: '€ EUR — Euro' },
  { code: 'GBP', label: '£ GBP — British Pound' },
  { code: 'AED', label: 'د.إ AED — UAE Dirham' },
]

const SettingsForm = ({ user, onSave, onCancel }) => {
  const [fullName, setFullName] = useState(user.fullName || '')
  const [storeName, setStoreName] = useState(user.storeName || '')
  const [currency, setCurrency] = useState(user.currency || 'INR')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    await onSave({ fullName, storeName, currency });
    setIsSubmitting(false);
  }

  return (
    <form className="settings-form" onSubmit={handleSubmit}>
      <label className="settings-label">
        <span>Full Name</span>
        <input className="settings-input" value={fullName} onChange={e => setFullName(e.target.value)} disabled={isSubmitting} />
      </label>
      <label className="settings-label">
        <span>Store Name</span>
        <input className="settings-input" value={storeName} onChange={e => setStoreName(e.target.value)} disabled={isSubmitting} />
      </label>
      <label className="settings-label">
        <span>Currency</span>
        <select className="settings-input" value={currency} onChange={e => setCurrency(e.target.value)} disabled={isSubmitting}>
          {CURRENCIES.map(c => (
            <option key={c.code} value={c.code}>{c.label}</option>
          ))}
        </select>
      </label>
      <div className="settings-actions">
        <button type="button" className="mono-btn" onClick={onCancel} disabled={isSubmitting}>Cancel</button>
        <button type="submit" className={`mono-btn ${isSubmitting ? 'btn-ghost-loading' : ''}`} disabled={isSubmitting} style={{ background: 'var(--ink)', color: 'var(--paper)' }}>
          Save Settings
        </button>
      </div>
    </form>
  )
}

export default App
