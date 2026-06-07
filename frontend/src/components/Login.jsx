/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react'

const STORAGE_KEY = 'retailmind_saved_email'

function Login({ onLogin, onDemoLogin, onSwitch }) {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [demoLoading, setDemoLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [remember, setRemember] = useState(false)
  const [showAdminForm, setShowAdminForm] = useState(false)

  // Restore saved email and check URL params on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      setEmail(saved)
      setRemember(true)
    }

    const params = new URLSearchParams(window.location.search)
    if (params.get('admin') === 'true' || params.get('mode') === 'admin') {
      setShowAdminForm(true)
    }
  }, [])

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
          <div className="editorial-column" style={{ position: 'relative' }}>
            <div className="editorial-masthead">
              <span className="editorial-masthead-kicker">LATEST EDITION</span>
              <h1 className="editorial-masthead-title" onDoubleClick={() => setShowAdminForm(v => !v)} style={{ cursor: 'pointer' }}>RetailMind</h1>
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

            {/* Hidden admin trigger: double click the circular stamp to reveal form */}
            <div 
              className="editorial-stamp" 
              style={{ pointerEvents: 'auto', cursor: 'help' }}
              onDoubleClick={() => setShowAdminForm(v => !v)}
              title="Double click to reveal Admin Login"
            >
              <div className="editorial-stamp-inner">
                Retail<br />Mind<br />Admin
              </div>
            </div>
          </div>

          {/* Right Column: Active Card */}
          <div className="auth-card">
            {!showAdminForm ? (
              <div className="showcase-content">
                <div style={{ marginBottom: '1.5rem', borderBottom: 'var(--border-mid)', paddingBottom: '1rem' }}>
                  <p className="mono" style={{ margin: '0 0 0.2rem', color: 'var(--ink-red)', fontSize: '0.65rem', fontWeight: 700 }}>
                    ESTABLISHED MMXXVI — INTERACTIVE SHOWCASE
                  </p>
                  <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800, color: 'var(--ink-black)', lineHeight: 1.15 }}>
                    Retail Intelligence Terminal
                  </h2>
                </div>

                <p style={{ fontSize: '0.92rem', color: '#334155', lineHeight: '1.6', marginBottom: '1.25rem' }}>
                  Welcome to the <strong>RetailMind</strong> portfolio showcase. This interactive platform demonstrates advanced machine learning solutions for independent merchants:
                </p>

                <ul style={{ paddingLeft: '1.2rem', margin: '0 0 1.5rem 0', lineHeight: '1.7', fontSize: '0.85rem', color: '#475569' }}>
                  <li><strong>Triple Exponential Smoothing (Holt-Winters)</strong> for multi-store customer demand forecasting.</li>
                  <li><strong>Unsupervised K-Means clustering</strong> for product catalog quadrant analytics.</li>
                  <li><strong>Interactive Pricing Simulator & Margin Elasticity</strong> for category optimization.</li>
                  <li><strong>Conversational AI Business Advisor</strong> powered by Groq Llama-3.</li>
                </ul>

                <div style={{ border: '1px dashed var(--ink-black)', padding: '1rem', backgroundColor: 'var(--bg-tint)', marginBottom: '1.5rem' }}>
                  <p className="mono" style={{ color: 'var(--ink-red)', fontSize: '0.65rem', fontWeight: 700, margin: '0 0 0.5rem' }}>
                    DEMO ENVIRONMENT RULES
                  </p>
                  <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Guest demo sessions are isolated, rate-limited, and automatically deleted after 2 hours. Permanent database writing is disabled.
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <button
                    type="button"
                    disabled={loading || demoLoading}
                    onClick={handleDemoClick}
                    style={{
                      background: 'var(--ink-black)',
                      color: 'var(--bg-paper)',
                      border: 'var(--border-mid)',
                      fontWeight: '800',
                      letterSpacing: '0.06em',
                      padding: '1.1rem',
                      fontSize: '0.9rem',
                      boxShadow: '4px 4px 0 rgba(0,0,0,0.15)',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {demoLoading ? 'PREPARING DEMO ENVIRONMENT...' : 'Continue with Demo Account'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="admin-login-content">
                <div style={{ marginBottom: '1.75rem', borderBottom: 'var(--border-mid)', paddingBottom: '1rem' }}>
                  <p className="mono" style={{ margin: '0 0 0.2rem', color: 'var(--ink-red)', fontSize: '0.65rem', fontWeight: 700 }}>
                    ESTABLISHED MMXXVI — SECURITY PORTAL
                  </p>
                  <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 800, color: 'var(--ink-black)' }}>
                    Admin Sign In
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
                      onClick={() => setShowAdminForm(false)}
                      className="switch-btn"
                      style={{ fontSize: '0.8rem', marginTop: '1rem' }}
                    >
                      ← Back to Demo Showcase
                    </button>
                    
                    <button
                      type="button"
                      onClick={onSwitch}
                      className="switch-btn"
                      style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}
                    >
                      Create an account
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
