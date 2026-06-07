/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import './AdminConsoleModal.css'

export default function AdminConsoleModal({ onClose, showToast, currentUser, onBypassSuccess, onReseedComplete, adminPin, setAdminPin }) {
  const [pin, setPin] = useState(adminPin || '')
  const [isVerified, setIsVerified] = useState(!!adminPin)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  
  // Enterprise bypass toggle
  const [isBypassed, setIsBypassed] = useState(currentUser?.plan === 'enterprise')

  // Double confirmation states
  const [confirmAction, setConfirmAction] = useState(null) // 'reseed' | 'flush'
  const [confirmInput, setConfirmInput] = useState('')

  const verifyAndLoad = useCallback(async (authPin) => {
    setLoading(true)
    try {
      // 1. Verify PIN
      await api.verifyAdminPin(authPin)
      setAdminPin(authPin)
      setIsVerified(true)

      // 2. Fetch stats
      const res = await api.getAdminStats(authPin)
      if (res && res.stats) {
        setStats(res.stats)
      }
    } catch (err) {
      setAdminPin('')
      showToast('error', err.message || 'Verification failed. Incorrect PIN.')
      setIsVerified(false)
    } finally {
      setLoading(false)
    }
  }, [setAdminPin, showToast])

  // Load stats if already verified in parent memory state
  useEffect(() => {
    if (adminPin) {
      verifyAndLoad(adminPin)
    }
  }, [adminPin, verifyAndLoad])

  const handleVerifySubmit = (e) => {
    e.preventDefault()
    if (!pin.trim()) return
    verifyAndLoad(pin.trim())
  }

  const handleToggleBypass = async () => {
    if (!currentUser?.id) {
      showToast('error', 'No active user session detected.')
      return
    }
    setLoading(true)
    const nextBypassState = !isBypassed
    try {
      await api.toggleAdminBypass(adminPin, currentUser.id, nextBypassState)
      setIsBypassed(nextBypassState)
      showToast('success', `Limits bypass toggled: ${nextBypassState ? 'ACTIVE' : 'INACTIVE'}`)
      if (onBypassSuccess) {
        onBypassSuccess(nextBypassState)
      }
    } catch (err) {
      showToast('error', err.message || 'Failed to update bypass limits.')
    } finally {
      setLoading(false)
    }
  }

  const handleTriggerReseed = async () => {
    if (confirmInput.trim() !== 'RESEED') {
      showToast('error', 'Please type RESEED to confirm.')
      return
    }
    setLoading(true)
    try {
      const res = await api.triggerAdminReseed(adminPin)
      showToast('success', res.message || 'Database successfully reseeded globally.')
      setConfirmAction(null)
      setConfirmInput('')
      
      // Reload stats
      const statsRes = await api.getAdminStats(adminPin)
      if (statsRes && statsRes.stats) {
        setStats(statsRes.stats)
      }

      if (onReseedComplete) {
        onReseedComplete()
      }
    } catch (err) {
      showToast('error', err.message || 'Global reseed failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleTriggerFlush = async () => {
    if (confirmInput.trim() !== 'FLUSH') {
      showToast('error', 'Please type FLUSH to confirm.')
      return
    }
    setLoading(true)
    try {
      const res = await api.clearAdminCache(adminPin)
      showToast('success', res.message || 'Cache database cleared successfully.')
      setConfirmAction(null)
      setConfirmInput('')
    } catch (err) {
      showToast('error', err.message || 'Failed to clear cache.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogoutAdmin = () => {
    setAdminPin('')
    setIsVerified(false)
    setPin('')
    setStats(null)
    showToast('info', 'Logged out from admin console.')
  }

  // Intercept and prevent parent Escape key unmount triggers when executing admin operations
  useEffect(() => {
    if (!loading) return

    const handleCaptureEscape = (e) => {
      if (e.key === 'Escape') {
        e.stopImmediatePropagation()
        e.preventDefault()
      }
    }
    window.addEventListener('keydown', handleCaptureEscape, true)
    return () => window.removeEventListener('keydown', handleCaptureEscape, true)
  }, [loading])

  return (
    <div className="admin-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="admin-title">
      <div className="admin-modal animate-scale">
        <div className="admin-modal-header">
          <span className="mono-kicker">Admin Command Center</span>
          <h2 id="admin-title">System Console</h2>
          <button className="close-btn" onClick={onClose} aria-label="Close Admin Console" disabled={loading}>✕</button>
        </div>

        {loading && <div className="admin-loading-indicator mono">EXECUTING OPERATION...</div>}

        {!isVerified ? (
          /* PIN Verification form */
          <form onSubmit={handleVerifySubmit} className="admin-pin-form">
            <p className="serif italic">
              Access to system configuration and data seeding requires administrative verification.
            </p>
            <label className="admin-label">
              <span>Admin Verification PIN</span>
              <input
                type="password"
                className="admin-input"
                placeholder="Enter PIN"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                disabled={loading}
                autoFocus
              />
            </label>
            <div className="admin-form-actions">
              <button type="button" className="mono-btn alert" onClick={onClose} disabled={loading}>
                Cancel
              </button>
              <button type="submit" className="mono-btn" disabled={loading}>
                Verify PIN
              </button>
            </div>
          </form>
        ) : (
          /* Verified Admin View */
          <div className="admin-console-content">
            
            {/* Stats section */}
            <div className="admin-section">
              <h3 className="serif">Database Statistics</h3>
              {stats ? (
                <div className="stats-grid mono">
                  <div className="stat-box">
                    <span className="stat-label">USERS</span>
                    <strong className="stat-num">{stats.users}</strong>
                  </div>
                  <div className="stat-box">
                    <span className="stat-label">STORES</span>
                    <strong className="stat-num">{stats.stores}</strong>
                  </div>
                  <div className="stat-box">
                    <span className="stat-label">SALES ROWS</span>
                    <strong className="stat-num">{stats.sale_records}</strong>
                  </div>
                  <div className="stat-box">
                    <span className="stat-label">ALERTS</span>
                    <strong className="stat-num">{stats.alerts}</strong>
                  </div>
                  <div className="stat-box">
                    <span className="stat-label">ML RESULTS</span>
                    <strong className="stat-num">{stats.ml_results}</strong>
                  </div>
                </div>
              ) : (
                <p className="mono">Loading database statistics...</p>
              )}
            </div>

            {/* Config bypass toggle */}
            <div className="admin-section">
              <h3 className="serif">User Limit Controls</h3>
              <div className="bypass-control-card">
                <div className="bypass-info">
                  <span className="mono bold">Enterprise Limits Bypass</span>
                  <p className="serif italic">
                    Upgrades the active user plan status to "enterprise". Bypasses the 500-record CSV/Excel upload constraint and overrides the 4-message context limit in AI Retail Advisor chat.
                  </p>
                  <span className="mono status-badge">
                    Current user plan: <strong style={{ color: currentUser?.plan === 'enterprise' ? 'var(--green-light)' : 'var(--red-light)' }}>{currentUser?.plan?.toUpperCase()}</strong>
                  </span>
                </div>
                <button 
                  className={`mono-btn ${isBypassed ? 'alert' : ''}`}
                  onClick={handleToggleBypass}
                  disabled={loading}
                >
                  {isBypassed ? 'Disable Bypass' : 'Enable Bypass'}
                </button>
              </div>
            </div>

            {/* High-risk actions */}
            <div className="admin-section">
              <h3 className="serif text-red">Danger Zone Operations</h3>
              
              {confirmAction ? (
                /* Double confirmation pane */
                <div className="confirm-action-box animate-scale">
                  <p className="mono bold text-red">⚠️ DETECTED HIGH IMPACT ACTION</p>
                  <p className="serif">
                    {confirmAction === 'reseed' 
                      ? 'Global DB Reseed will TRUNCATE all transaction ledgers, registered stores, alerts, ML clustering results, and user accounts. It will then populate default demo data.' 
                      : 'Flush Cache will invalidate all pre-cached forecast models, chart bundles, and database queries.'}
                  </p>
                  <label className="admin-label">
                    <span>Type <strong className="mono">{confirmAction.toUpperCase()}</strong> to confirm:</span>
                    <input
                      type="text"
                      className="admin-input"
                      value={confirmInput}
                      onChange={(e) => setConfirmInput(e.target.value)}
                      placeholder={`Type ${confirmAction.toUpperCase()}`}
                      autoFocus
                    />
                  </label>
                  <div className="admin-form-actions" style={{ marginTop: '10px' }}>
                    <button className="mono-btn" onClick={() => { setConfirmAction(null); setConfirmInput(''); }}>
                      Cancel
                    </button>
                    <button 
                      className="mono-btn alert" 
                      onClick={confirmAction === 'reseed' ? handleTriggerReseed : handleTriggerFlush}
                      disabled={loading}
                    >
                      Confirm Execution
                    </button>
                  </div>
                </div>
              ) : (
                /* Primary buttons */
                <div className="danger-actions">
                  <div className="danger-row">
                    <div className="danger-info">
                      <span className="mono bold">Flush Redis Cache</span>
                      <p className="serif italic">Flushes intermediate memory caching. Forces stats and forecast model recalculations.</p>
                    </div>
                    <button className="mono-btn alert" onClick={() => setConfirmAction('flush')}>
                      Flush Cache
                    </button>
                  </div>
                  <div className="danger-row">
                    <div className="danger-info">
                      <span className="mono bold text-red">Global DB Reseed</span>
                      <p className="serif italic">Truncates all tables and seeds fresh dataset (90-day history, default alerts).</p>
                    </div>
                    <button className="mono-btn alert" onClick={() => setConfirmAction('reseed')}>
                      Reseed DB
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Admin Console Footer */}
            <div className="admin-modal-footer">
              <button className="mono-btn" onClick={handleLogoutAdmin} disabled={loading}>
                Lock Console (Logout)
              </button>
              <button className="mono-btn btn-secondary" onClick={onClose} disabled={loading}>
                Close Console
              </button>
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
