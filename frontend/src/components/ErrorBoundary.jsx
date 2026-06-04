/**
 * RetailMind Global Error Boundary
 *
 * Catches unhandled React render errors and shows a broadsheet-style
 * fallback UI instead of a blank screen.
 *
 * Logs errors to Sentry if available.
 */

import React from 'react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // Log to Sentry if available
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.captureException(error, { extra: info })
    }
    console.error('[RetailMind] Unhandled render error:', error, info)
  }

  handleReload() {
    window.location.reload()
  }

  handleReset() {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (!this.state.hasError) return this.props.children

    if (this.props.inline) {
      return (
        <div className="card error-card" style={{ border: '1px solid var(--ink-red)', background: 'rgba(139,0,0,0.03)', padding: '1.5rem', textAlign: 'center' }}>
          <span className="mono" style={{ color: 'var(--ink-red)', fontSize: '0.65rem', fontWeight: 700 }}>
            SECTION ERROR
          </span>
          <h3 style={{ fontSize: '1.1rem', margin: '0.5rem 0' }}>Unable to load this component</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0 0 1rem' }}>
            {this.state.error?.message || 'Unexpected rendering error'}
          </p>
          <button 
            onClick={() => this.handleReset()}
            style={{ fontSize: '0.65rem', padding: '4px 10px', borderColor: 'var(--ink-red)', color: 'var(--ink-red)' }}
          >
            Retry
          </button>
        </div>
      )
    }

    return (
      <div className="error-boundary">
        <div className="error-boundary__masthead">
          <span className="error-boundary__kicker">SYSTEM ALERT</span>
          <h1 className="error-boundary__headline">Something went wrong</h1>
          <p className="error-boundary__subhead">
            RetailMind encountered an unexpected error. Your data is safe.
          </p>
        </div>

        <div className="error-boundary__body">
          {this.state.error && (
            <div className="error-boundary__detail">
              <span className="error-boundary__detail-label">Error</span>
              <code className="error-boundary__detail-code">
                {this.state.error.message || 'Unknown error'}
              </code>
            </div>
          )}

          <div className="error-boundary__actions">
            <button
              className="error-boundary__btn error-boundary__btn--primary"
              onClick={this.handleReload}
            >
              Reload Page
            </button>
            <button
              className="error-boundary__btn error-boundary__btn--secondary"
              onClick={() => this.handleReset()}
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }
}

export default ErrorBoundary
