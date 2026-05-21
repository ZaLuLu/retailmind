import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { formatMoneyCompact } from '../services/currency'

const TREND_ICON = { up: '↑', down: '↓', flat: '→', new: '★' }
const TREND_COLOR = { up: '#4CAF50', down: '#E57373', flat: '#C9A84C', new: '#1976D2' }
const CONFIDENCE_COLOR = { high: '#4CAF50', medium: '#C9A84C', low: '#E57373' }

const DemandSignals = ({
  demandSignals = [],
  deadStockAlerts = [],
  marginAlerts = [],
  currency = 'INR',
}) => {
  const [tab, setTab] = useState('demand') // 'demand' | 'dead' | 'margin' | 'forecast'
  const [forecast, setForecast] = useState([])
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastError, setForecastError] = useState(null)

  // Lazy-load forecast only when tab is selected
  useEffect(() => {
    if (tab !== 'forecast' || forecast.length > 0) return
    setForecastLoading(true)
    setForecastError(null)
    api.getRetailForecast()
      .then(data => setForecast(data))
      .catch(err => setForecastError(err.message || 'Failed to load forecast'))
      .finally(() => setForecastLoading(false))
  }, [tab])

  const totalAlerts = demandSignals.length + deadStockAlerts.length + marginAlerts.length

  return (
    <section className="demand-signals">
      <div className="section-kicker">
        <span className="kicker-label">
          Market Intelligence
          {totalAlerts > 0 && <span className="alert-badge">{totalAlerts}</span>}
        </span>
        <div className="kicker-line" />
      </div>

      {/* Tabs */}
      <div className="signal-tabs">
        <button
          className={`signal-tab ${tab === 'demand' ? 'active' : ''}`}
          onClick={() => setTab('demand')}
        >
          🔥 Spikes
          {demandSignals.length > 0 && <span className="tab-count">{demandSignals.length}</span>}
        </button>
        <button
          className={`signal-tab ${tab === 'dead' ? 'active' : ''}`}
          onClick={() => setTab('dead')}
        >
          📦 Dead Stock
          {deadStockAlerts.length > 0 && <span className="tab-count">{deadStockAlerts.length}</span>}
        </button>
        <button
          className={`signal-tab ${tab === 'margin' ? 'active' : ''}`}
          onClick={() => setTab('margin')}
        >
          ⚠ Margin
          {marginAlerts.length > 0 && <span className="tab-count">{marginAlerts.length}</span>}
        </button>
        <button
          className={`signal-tab ${tab === 'forecast' ? 'active' : ''}`}
          onClick={() => setTab('forecast')}
        >
          📈 Forecast
        </button>
      </div>

      {/* Content */}
      <div className="signal-list">

        {/* Demand Spikes */}
        {tab === 'demand' && (
          demandSignals.length === 0
            ? <p className="signal-empty">No demand spikes detected this week.</p>
            : demandSignals.map((s, i) => (
                <div className="signal-card spike" key={i}>
                  <div className="signal-icon">🚀</div>
                  <div className="signal-content" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {s.z_score && s.z_score > 0 ? (
                      <>
                        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                          <span className="telex-stamp-badge red-stamp">SPIKE ALERT</span>
                          <span className="signal-product" style={{ margin: 0 }}>{s.product_name}</span>
                        </div>
                        <span className="monospace-text signal-message" style={{ fontSize: '0.8rem', lineHeight: '1.4' }}>
                          Surge detected: Z-score of {s.z_score.toFixed(2)} (+{s.deviation_pct}% deviation).
                        </span>
                      </>
                    ) : (
                      <>
                        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                          <span className="telex-stamp-badge red-stamp" style={{ borderColor: 'var(--ink-yellow)', color: 'var(--ink-yellow)', backgroundColor: 'rgba(184, 134, 11, 0.05)' }}>SPIKE</span>
                          <span className="signal-product" style={{ margin: 0 }}>{s.product_name}</span>
                        </div>
                        <span className="signal-message">{s.message}</span>
                      </>
                    )}
                  </div>
                  <span className="signal-qty">+{s.recent_qty} units</span>
                </div>
              ))
        )}

        {/* Dead Stock */}
        {tab === 'dead' && (
          deadStockAlerts.length === 0
            ? <p className="signal-empty">No dead stock detected.</p>
            : deadStockAlerts.map((s, i) => (
                <div className="signal-card dead" key={i}>
                  <div className="signal-icon">⏸</div>
                  <div className="signal-content">
                    <span className="signal-product">{s.product_name}</span>
                    <span className="signal-message">{s.message}</span>
                  </div>
                  <span className="signal-days">{s.last_sale_days_ago}d</span>
                </div>
              ))
        )}

        {/* Margin Alerts */}
        {tab === 'margin' && (
          marginAlerts.length === 0
            ? <p className="signal-empty">All products above margin threshold.</p>
            : marginAlerts.map((s, i) => (
                <div className="signal-card margin-warn" key={i}>
                  <div className="signal-icon">📉</div>
                  <div className="signal-content">
                    <span className="signal-product">{s.product_name}</span>
                    <span className="signal-message">{s.message}</span>
                  </div>
                  <span className="signal-margin" style={{ color: '#E57373' }}>{s.margin_pct}%</span>
                </div>
              ))
        )}

        {/* Forecast */}
        {tab === 'forecast' && (
          forecastLoading
            ? <p className="signal-empty animate-pulse">Calculating forecasts…</p>
            : forecastError
              ? (
                <div className="signal-error">
                  <p>{forecastError}</p>
                  <button
                    className="mono-btn"
                    onClick={() => {
                      setForecast([])
                      setForecastError(null)
                      setTab('demand')
                      setTimeout(() => setTab('forecast'), 50)
                    }}
                  >
                    Retry
                  </button>
                </div>
              )
              : forecast.length === 0
                ? <p className="signal-empty">Not enough data for forecasting yet. Upload more sales history.</p>
                : (
                  <>
                    <p className="forecast-subtitle mono">
                      Weighted rolling average · Next 7 days · Top {forecast.length} products
                    </p>
                    {forecast.map((f, i) => (
                      <div className="signal-card forecast-card" key={i}>
                        <div className="forecast-rank mono">#{i + 1}</div>
                        <div className="signal-content">
                          <span className="signal-product">{f.product_name}</span>
                          <span className="signal-message">
                            <span className="cat-chip">{f.category}</span>
                            &nbsp;·&nbsp;
                            <span
                              className="confidence-badge"
                              style={{ color: CONFIDENCE_COLOR[f.confidence] }}
                            >
                              {f.confidence} confidence
                            </span>
                          </span>
                        </div>
                        <div className="forecast-right">
                          <span className="forecast-qty mono">
                            ~{f.forecast_qty_7d} units
                          </span>
                          <span
                            className="forecast-trend mono"
                            style={{ color: TREND_COLOR[f.trend] }}
                            title={`Prior 7d: ${f.prior_7d_qty} units`}
                          >
                            {TREND_ICON[f.trend]} {f.trend}
                          </span>
                        </div>
                      </div>
                    ))}
                  </>
                )
        )}
      </div>
    </section>
  )
}

export default DemandSignals
