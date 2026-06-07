import { useState, useEffect, useCallback } from 'react'
import OnboardingWizard from './components/OnboardingWizard'
import AdvisorChat from './components/AdvisorChat'
import Login from './components/Login'
import Register from './components/Register'
import IntelligenceDashboard from './components/IntelligenceDashboard'
import DemoModeBanner from './components/DemoModeBanner'
import DemoResetUploadModal from './components/DemoResetUploadModal'
import SplashScreen from './components/SplashScreen'
import GuidedTour from './components/GuidedTour'
import AdminConsoleModal from './components/AdminConsoleModal'
import { api } from './services/api'
import { useToast } from './components/Toast'
import { IS_DEMO } from './config'
import { useRetailData } from './hooks/useRetailData'
import './App.css'

function App() {
  const { showToast } = useToast()

  // ── Auth & Routing state ─────────────────────────────────────────────────
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  )
  const [authView, setAuthView] = useState('login') // 'login' | 'register'
  const [splashDone, setSplashDone] = useState(false)

  // ── Modals & Chat state ──────────────────────────────────────────────────
  const [showSettings, setShowSettings] = useState(false)
  const [showAdmin, setShowAdmin] = useState(false)
  const [adminPin, setAdminPin] = useState('')
  const [showChat, setShowChat] = useState(false)
  const [chatPrefill, setChatPrefill] = useState('')

  const handleAskAdvisor = (promptText) => {
    setChatPrefill(promptText)
    setShowChat(true)
  }

  // ── Auth handlers ──────────────────────────────────────────────────────────
  const handleLogin = async (email, password) => {
    await api.login(email, password)
    setIsAuthenticated(true)
  }

  const handleDemoLogin = async () => {
    await api.demoLogin()
    setIsAuthenticated(true)
  }

  const handleRegister = async (email, password) => {
    await api.register(email, password)
    setAuthView('login')
  }

  const handleLogout = useCallback(() => {
    api.logout()
    setIsAuthenticated(false)
    setAdminPin('')
  }, [])

  // Use the custom state hook
  const {
    user,
    setUser,
    sales,
    summary,
    loading,
    stores,
    selectedStore,
    hasCustomData,
    showImport,
    setShowImport,
    isOnboarded,
    fetchUserData,
    handleSelectStore,
    handleCreateStore,
    handleOnboardingComplete,
    handleSettingsSave,
    handleDemoUploadComplete,
    handleDemoRestore,
  } = useRetailData(isAuthenticated, showToast, handleLogout)

  // Listen for forced logout from token refresh failure
  useEffect(() => {
    const handleForcedLogout = () => {
      handleLogout()
      showToast('warning', 'Your session expired. Please log in again.')
    }
    window.addEventListener('auth:logout', handleForcedLogout)
    return () => window.removeEventListener('auth:logout', handleForcedLogout)
  }, [handleLogout, showToast])

  // Listen for Escape key to close settings, admin console, and advisor chat overlays
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        if (showSettings) setShowSettings(false)
        if (showChat) setShowChat(false)
        if (showAdmin) setShowAdmin(false)
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [showSettings, showChat, showAdmin])

  // ── Routing ────────────────────────────────────────────────────────────────
  if (!isAuthenticated) {
    return authView === 'login'
      ? <Login onLogin={handleLogin} onDemoLogin={handleDemoLogin} onSwitch={() => setAuthView('register')} />
      : <Register onRegister={handleRegister} onSwitch={() => setAuthView('login')} />
  }

  if (!splashDone) {
    return <SplashScreen onComplete={() => setSplashDone(true)} />
  }

  if (!isOnboarded) {
    return <OnboardingWizard onComplete={handleOnboardingComplete} />
  }

  return (
    <div className="app-root">
      <GuidedTour />
      {/* Demo Mode Banner — always visible in demo, never dismissible */}
      <DemoModeBanner
        onUpload={() => setShowImport(true)}
        hasCustomData={hasCustomData}
        onRestore={handleDemoRestore}
        hasSalesData={sales.length > 0}
      />

      {/* Demo upload modal */}
      {showImport && (
        <DemoResetUploadModal
          onClose={() => setShowImport(false)}
          onComplete={handleDemoUploadComplete}
        />
      )}

      {/* Settings modal — inline, lightweight */}
      {showSettings && (
        <div className="settings-overlay">
          <div className="settings-modal">
            <div className="settings-header">
              <h2>Store Settings</h2>
              <button className="close-btn" onClick={() => setShowSettings(false)}>✕</button>
            </div>
            <SettingsForm user={user} onSave={(updatedData) => handleSettingsSave(updatedData, () => setShowSettings(false))} onCancel={() => setShowSettings(false)} />
          </div>
        </div>
      )}

      {showChat && (
        <AdvisorChat
          summary={summary}
          prefill={chatPrefill}
          clearPrefill={() => setChatPrefill('')}
          onClose={() => setShowChat(false)}
        />
      )}

      {showAdmin && (
        <AdminConsoleModal
          onClose={() => setShowAdmin(false)}
          showToast={showToast}
          currentUser={user}
          onBypassSuccess={(bypassState) => {
            setUser(prev => ({ ...prev, plan: bypassState ? 'enterprise' : 'free' }))
          }}
          onReseedComplete={() => {
            fetchUserData(undefined, undefined, undefined, undefined, true)
          }}
          adminPin={adminPin}
          setAdminPin={setAdminPin}
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
        isDemoMode={IS_DEMO}
        onShowImport={() => setShowImport(true)}
        onAskAdvisor={handleAskAdvisor}
        onShowAdmin={() => setShowAdmin(true)}
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

  useEffect(() => {
    const previousFocus = document.activeElement
    const firstInput = document.querySelector('.settings-input')
    if (firstInput) {
      firstInput.focus()
    }
    return () => {
      if (previousFocus) {
        previousFocus.focus()
      }
    }
  }, [])

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
        <button type="button" className="btn-secondary" onClick={onCancel} disabled={isSubmitting}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={isSubmitting}>{isSubmitting ? 'Saving...' : 'Save Settings'}</button>
      </div>
    </form>
  )
}

export default App
