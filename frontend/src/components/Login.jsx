import React, { useState, useEffect } from 'react'

const STORAGE_KEY = 'retailmind_saved_email'

function Login({ onLogin, onSwitch }) {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [remember, setRemember] = useState(false)

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
      <div className="auth-card">
        <div style={{ marginBottom: '2rem', borderBottom: 'var(--border-heavy)', paddingBottom: '1.5rem' }}>
          <p className="mono" style={{ margin: '0 0 0.25rem', color: 'var(--text-muted)', fontSize: '0.65rem' }}>
            The Morning Edition
          </p>
          <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800 }}>
            RetailMind Platform
          </h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}

          <div className="form-group">
            <label>Correspondence Email</label>
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
            <label>Secure Access Code</label>
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
              Remember email
            </label>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button type="submit" disabled={loading} id="login-submit">
              {loading ? 'Authenticating...' : 'Enter Desk →'}
            </button>

            <button
              type="button"
              onClick={onSwitch}
              className="switch-btn"
            >
              New correspondent? Register here
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login
