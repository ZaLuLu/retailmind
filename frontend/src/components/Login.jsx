import React, { useState } from 'react'

function Login({ onLogin, onDemoLogin, onSwitch }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onLogin(email, password)
    } catch (err) {
      setError('INVALID CREDENTIALS — ACCESS DENIED')
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
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
          </div>
          <div className="form-group">
            <label>Secure Access Code</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button type="submit" disabled={loading}>
              {loading ? 'Authenticating...' : 'Enter Desk →'}
            </button>
            <button
              type="button"
              onClick={onDemoLogin}
              style={{
                backgroundColor: 'var(--ink-black)',
                color: 'var(--bg-paper)',
                borderColor: 'var(--ink-black)'
              }}
            >
              Portfolio Demo (Skip Login)
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
