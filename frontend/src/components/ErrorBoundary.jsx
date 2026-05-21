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
