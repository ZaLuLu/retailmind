import { useState } from 'react'

function Register({ onRegister, onSwitch }) {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirm) {
      setError('PASSWORDS DO NOT MATCH — VERIFY AND RETRY')
      return
    }
    if (password.length < 6) {
      setError('PASSWORD TOO SHORT — MINIMUM 6 CHARACTERS')
      return
    }

    setLoading(true)
    try {
      await onRegister(email.trim(), password)
      // Credentials are safely handled by the browser's native password manager
      // via autocomplete="new-password" — no manual storage needed
    } catch (err) {
      const msg = err?.message || ''
      if (msg.toLowerCase().includes('already') || msg.toLowerCase().includes('exists') || msg.toLowerCase().includes('409')) {
        setError('EMAIL ALREADY REGISTERED — TRY LOGGING IN')
      } else if (msg.toLowerCase().includes('network') || msg.toLowerCase().includes('failed to fetch')) {
        setError('NETWORK ERROR — CANNOT REACH SERVER')
      } else if (msg) {
        setError(msg.toUpperCase())
      } else {
        setError('REGISTRATION FAILED — SYSTEM ERROR')
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
                "By establishing your identity in our records, you gain deep analytical command over gross margins, sales trends, and AI forecasting."
              </p>
            </div>
          </div>

          {/* Right Column: Active Card */}
          <div className="auth-card">
            <div style={{ marginBottom: '1.75rem', borderBottom: 'var(--border-mid)', paddingBottom: '1rem' }}>
              <p className="mono" style={{ margin: '0 0 0.2rem', color: 'var(--ink-red)', fontSize: '0.65rem', fontWeight: 700 }}>
                ESTABLISHED MMXXVI — REGISTRATION PORTAL
              </p>
              <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 800, color: 'var(--ink-black)' }}>
                Create Account
              </h2>
            </div>

            <form onSubmit={handleSubmit}>
              {error && <div className="auth-error">{error}</div>}

              <div className="form-group">
                <label htmlFor="register-email">Email Address</label>
                <input
                  id="register-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </div>

              <div className="form-group">
                <label htmlFor="register-password">Password</label>
                <div className="password-wrapper">
                  <input
                    id="register-password"
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    placeholder="min. 6 characters"
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

              <div className="form-group">
                <label htmlFor="register-confirm">Confirm Password</label>
                <div className="password-wrapper">
                  <input
                    id="register-confirm"
                    type={showConfirm ? 'text' : 'password'}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                    autoComplete="new-password"
                    placeholder="repeat password"
                  />
                  <button
                    type="button"
                    className="show-pass-btn"
                    onClick={() => setShowConfirm(v => !v)}
                    aria-label={showConfirm ? 'Hide password' : 'Show password'}
                    tabIndex={-1}
                  >
                    {showConfirm ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1.5rem' }}>
                <button type="submit" disabled={loading} id="register-submit">
                  {loading ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT →'}
                </button>
                <button
                  type="button"
                  onClick={onSwitch}
                  className="switch-btn"
                >
                  Already have an account? Sign in
                </button>
                <a
                  href="/"
                  className="switch-btn"
                  style={{ textDecoration: 'underline', marginTop: '0.5rem', fontSize: '0.8rem', textAlign: 'center', display: 'block', color: 'var(--text-muted)' }}
                  onClick={(e) => {
                    e.preventDefault()
                    window.location.href = window.location.origin
                  }}
                >
                  ← Back to Demo Showcase
                </a>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Register
