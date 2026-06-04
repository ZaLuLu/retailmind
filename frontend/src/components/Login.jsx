import React, { useState, useEffect } from 'react'

const STORAGE_KEY = 'retailmind_saved_email'

function Login({ onLogin, onDemoLogin, onSwitch }) {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [demoLoading, setDemoLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [remember, setRemember] = useState(false)

  const handleDemoClick = async (e) => {
    e.preventDefault()
    setError('')
    setDemoLoading(true)
    try {
      await onDemoLogin()
    } catch (err) {
      setError(err?.message || 'Demo login failed')
    } finally {
      setDemoLoading(false)
    }
  }

  // Restore saved email on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      setEmail(saved)
      setRemember(true)
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onLogin(email.trim(), password)
      // On success — persist email if remember is checked
      if (remember) {
        localStorage.setItem(STORAGE_KEY, email.trim())
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch (err) {
      // Show server-side message if available, else fallback
      const msg = err?.message || ''
      if (msg.toLowerCase().includes('incorrect') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('401')) {
        setError('INVALID CREDENTIALS — ACCESS DENIED')
      } else if (msg.toLowerCase().includes('network') || msg.toLowerCase().includes('failed to fetch')) {
        setError('NETWORK ERROR — CANNOT REACH SERVER')
      } else if (msg) {
        setError(msg.toUpperCase())
      } else {
        setError('INVALID CREDENTIALS — ACCESS DENIED')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-broadsheet animate-scale">
          {/* Left Column: Broadside Editorial */}
          <div className="editorial-column">
            <div className="editorial-masthead">
              <span className="editorial-masthead-kicker">LATEST EDITION</span>
              <h1 className="editorial-masthead-title">RetailMind</h1>
              <div className="editorial-tagline">
                THE INDEPENDENT BUSINESS JOURNAL FOR SMB RETAILERS
              </div>
            </div>

            <div className="editorial-bulletin">
              <h3 className="editorial-bulletin-title">Intelligence Bulletin</h3>
              <p className="editorial-bulletin-text">
                "Without reliable data, a merchant merely walks through the dark. Light up your revenue, stock margins, and customer dynamics today."
              </p>
            </div>
          </div>

          {/* Right Column: Active Card */}
          <div className="auth-card">
            <div style={{ marginBottom: '1.75rem', borderBottom: 'var(--border-mid)', paddingBottom: '1rem' }}>
              <p className="mono" style={{ margin: '0 0 0.2rem', color: 'var(--ink-red)', fontSize: '0.65rem', fontWeight: 700 }}>
                ESTABLISHED MMXXVI — SECURITY PORTAL
              </p>
              <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 800, color: 'var(--ink-black)' }}>
                Sign In
              </h2>
            </div>

            <form onSubmit={handleSubmit}>
              {error && <div className="auth-error">{error}</div>}

              <div className="form-group">
                <label htmlFor="login-email">Email Address</label>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </div>

              <div className="form-group">
                <label htmlFor="login-password">Password</label>
                <div className="password-wrapper">
                  <input
                    id="login-password"
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    className="show-pass-btn"
                    onClick={() => setShowPass(v => !v)}
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                    tabIndex={-1}
                  >
                    {showPass ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              <div className="remember-row">
                <label className="remember-label">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={e => setRemember(e.target.checked)}
                  />
                  <span>Remember my email</span>
                </label>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button type="submit" disabled={loading || demoLoading} id="login-submit">
                  {loading ? 'SIGNING IN...' : 'SIGN IN →'}
                </button>

                <button
                  type="button"
                  disabled={loading || demoLoading}
                  onClick={handleDemoClick}
                  style={{
                    background: 'none',
                    color: 'var(--ink-blue)',
                    border: '2px solid var(--ink-blue)',
                    fontWeight: '700',
                    letterSpacing: '0.04em',
                    padding: '0.85rem'
                  }}
                >
                  {demoLoading ? 'BOOTSTRAPPING DEMO...' : 'TRY LIVE DEMO (GUEST ACCESS) →'}
                </button>

                <button
                  type="button"
                  onClick={onSwitch}
                  className="switch-btn"
                >
                  Create an account
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
