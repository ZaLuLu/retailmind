import React, { useState } from 'react'

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
      <div className="auth-card">
        <div style={{ marginBottom: '2rem', borderBottom: 'var(--border-heavy)', paddingBottom: '1.5rem' }}>
          <p className="mono" style={{ margin: '0 0 0.25rem', color: 'var(--text-muted)', fontSize: '0.65rem' }}>
            Join the Network
          </p>
          <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800 }}>
            Establish Identity
          </h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}

          <div className="form-group">
            <label>Correspondence Email</label>
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
            <label>Secure Access Code</label>
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
            <label>Confirm Access Code</label>
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

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button type="submit" disabled={loading} id="register-submit">
              {loading ? 'Initializing...' : 'Initialize Account →'}
            </button>
            <button
              type="button"
              onClick={onSwitch}
              className="switch-btn"
            >
              Already a correspondent? Login here
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Register
