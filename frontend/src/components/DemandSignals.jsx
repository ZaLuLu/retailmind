/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react'
import { api } from '../services/api'
import DashboardTooltip from './DashboardTooltip'

const TREND_ICON = { up: '↑', down: '↓', flat: '→', new: '★' }
const TREND_COLOR = { up: '#4CAF50', down: '#E57373', flat: '#C9A84C', new: '#1976D2' }
const CONFIDENCE_COLOR = { high: '#4CAF50', medium: '#C9A84C', low: '#E57373' }

const DEFAULT_TASKS = {
  spike: [
    "Verify buffer stock in backroom",
    "Contact supplier for expedited reorder",
    "Adjust pricing upward (+5-10%) to optimize margin",
    "Verify promotional tag display on store floor"
  ],
  dead: [
    "Apply markdown discount (e.g. 20-30%)",
    "Relocate stock to clearance endcap",
    "Cross-merchandise with high-traffic category",
    "Process vendor return authorization (RTV) if eligible"
  ],
  margin: [
    "Renegotiate wholesale cost (COGS) with vendor",
    "Remove item from active promotions/discounts",
    "Bundle with high-margin complementary item",
    "Audit supplier invoice for billing discrepancies"
  ]
}

const DemandSignals = ({
  demandSignals = [],
  deadStockAlerts = [],
  marginAlerts = [],
  onAskAdvisor,
  storeId = null,
}) => {
  const [tab, setTab] = useState('demand') // 'demand' | 'dead' | 'margin' | 'forecast'
  const [forecast, setForecast] = useState([])
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastError, setForecastError] = useState(null)

  const [expandedCards, setExpandedCards] = useState({})
  const [checkedTasks, setCheckedTasks] = useState(() => {
    try {
      const saved = localStorage.getItem('retailmind_checked_tasks')
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem('retailmind_checked_tasks', JSON.stringify(checkedTasks))
    } catch (e) {
      console.error(e)
    }
  }, [checkedTasks])

  const toggleCard = (cardId) => {
    setExpandedCards(prev => ({ ...prev, [cardId]: !prev[cardId] }))
  }

  const toggleTask = (cardId, taskIdx) => {
    const key = `${cardId}-${taskIdx}`
    setCheckedTasks(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const renderChecklist = (cardId, type) => {
    const list = DEFAULT_TASKS[type]
    const isExpanded = !!expandedCards[cardId]

    if (!isExpanded) return null

    return (
      <div className="telex-task-checklist" onClick={(e) => e.stopPropagation()} style={{ marginTop: '0.75rem', borderTop: '1px dashed var(--rule)', paddingTop: '0.75rem', width: '100%' }}>
        <p className="mono" style={{ margin: '0 0 0.4rem 0', fontSize: '0.68rem', fontWeight: 700, color: 'var(--ink)' }}>
          📋 OPERATIONS ACTION PLAN:
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {list.map((task, idx) => {
            const key = `${cardId}-${idx}`
            const isChecked = !!checkedTasks[key]
            return (
              <label 
                key={idx} 
                className="mono" 
                style={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  gap: '8px', 
                  fontSize: '0.7rem', 
                  cursor: 'pointer',
                  textDecoration: isChecked ? 'line-through' : 'none',
                  color: isChecked ? 'var(--ink-muted)' : 'var(--ink)'
                }}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleTask(cardId, idx)}
                  style={{ marginTop: '2px', cursor: 'pointer' }}
                />
                <span>{task}</span>
              </label>
            )
          })}
        </div>
      </div>
    )
  }

  // Unified effect: reset forecast cache on storeId change; lazy-load when forecast tab is active
  useEffect(() => {
    // Always reset cached forecast when the store changes
    setForecast([])
    setForecastError(null)
    // Only fetch if the forecast tab is already active
    if (tab !== 'forecast') return
    let cancelled = false
    setForecastLoading(true)
    api.getRetailForecast(storeId)
      .then(data => { if (!cancelled) setForecast(data) })
      .catch(err => { if (!cancelled) setForecastError(err.message || 'Failed to load forecast') })
      .finally(() => { if (!cancelled) setForecastLoading(false) })
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeId])

  // Fetch forecast when the tab is switched to 'forecast'
  useEffect(() => {
    if (tab !== 'forecast' || forecast.length > 0 || forecastLoading) return
    let cancelled = false
    setForecastLoading(true)
    setForecastError(null)
    api.getRetailForecast(storeId)
      .then(data => { if (!cancelled) setForecast(data) })
      .catch(err => { if (!cancelled) setForecastError(err.message || 'Failed to load forecast') })
      .finally(() => { if (!cancelled) setForecastLoading(false) })
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  const totalAlerts = demandSignals.length + deadStockAlerts.length + marginAlerts.length

  return (
    <section className="demand-signals">
      <div className="section-kicker">
        <span className="kicker-label">
          Market Intelligence
          <DashboardTooltip 
            title="Market Intelligence Alerts" 
            content="Real-time operations alerts: Demand Spikes (sudden volume surge), Dead Stock (no sales in 30 days), Margin Erosion (margin < 20%), and 7-day predictive forecasts." 
          />
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
            : demandSignals.map((s, i) => {
                const cardId = `spike-${s.product_name}`
                return (
                  <div 
                    className="signal-card spike" 
                    key={i} 
                    onClick={() => toggleCard(cardId)}
                    style={{ cursor: 'pointer', flexDirection: 'column', alignItems: 'flex-start' }}
                  >
                    <div style={{ display: 'flex', width: '100%', alignItems: 'center', gap: '10px' }}>
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
                        {onAskAdvisor && (
                          <button
                            className="ask-advisor-btn mono"
                            style={{
                              fontSize: '0.62rem',
                              marginTop: '0.35rem',
                              background: 'var(--bg-paper)',
                              border: '1px solid var(--ink-black)',
                              padding: '3px 8px',
                              cursor: 'pointer',
                              boxShadow: '2px 2px 0 var(--ink-black)',
                              alignSelf: 'flex-start',
                              fontWeight: 700
                            }}
                            onClick={(e) => {
                              e.stopPropagation()
                              onAskAdvisor(`Our product "${s.product_name}" is experiencing a sudden demand surge of +${s.deviation_pct}% compared to rolling average (Z-score: ${s.z_score?.toFixed(2) || 'N/A'}). What inventory replenishment and pricing tactics should we execute immediately to satisfy this demand?`)
                            }}
                          >
                            Ask Advisor →
                          </button>
                        )}
                      </div>
                      <span className="signal-qty" style={{ marginLeft: 'auto' }}>+{s.recent_qty} units</span>
                    </div>
                    {renderChecklist(cardId, 'spike')}
                  </div>
                )
              })
        )}

        {/* Dead Stock */}
        {tab === 'dead' && (
          deadStockAlerts.length === 0
            ? <p className="signal-empty">No dead stock detected.</p>
            : deadStockAlerts.map((s, i) => {
                const cardId = `dead-${s.product_name}`
                return (
                  <div 
                    className="signal-card dead" 
                    key={i}
                    onClick={() => toggleCard(cardId)}
                    style={{ cursor: 'pointer', flexDirection: 'column', alignItems: 'flex-start' }}
                  >
                    <div style={{ display: 'flex', width: '100%', alignItems: 'center', gap: '10px' }}>
                      <div className="signal-icon">⏸</div>
                      <div className="signal-content" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className="signal-product">{s.product_name}</span>
                        <span className="signal-message">{s.message}</span>
                        {onAskAdvisor && (
                          <button
                            className="ask-advisor-btn mono"
                            style={{
                              fontSize: '0.62rem',
                              marginTop: '0.35rem',
                              background: 'var(--bg-paper)',
                              border: '1px solid var(--ink-black)',
                              padding: '3px 8px',
                              cursor: 'pointer',
                              boxShadow: '2px 2px 0 var(--ink-black)',
                              alignSelf: 'flex-start',
                              fontWeight: 700
                            }}
                            onClick={(e) => {
                              e.stopPropagation()
                              onAskAdvisor(`Our product "${s.product_name}" has had no sales in ${s.last_sale_days_ago} days. What concrete liquidation promotions, clearout discounts, or marketing campaigns do you advise to free up our working capital?`)
                            }}
                          >
                            Ask Advisor →
                          </button>
                        )}
                      </div>
                      <span className="signal-days" style={{ marginLeft: 'auto' }}>{s.last_sale_days_ago}d</span>
                    </div>
                    {renderChecklist(cardId, 'dead')}
                  </div>
                )
              })
        )}

        {/* Margin Alerts */}
        {tab === 'margin' && (
          marginAlerts.length === 0
            ? <p className="signal-empty">All products above margin threshold.</p>
            : marginAlerts.map((s, i) => {
                const cardId = `margin-${s.product_name}`
                return (
                  <div 
                    className="signal-card margin-warn" 
                    key={i}
                    onClick={() => toggleCard(cardId)}
                    style={{ cursor: 'pointer', flexDirection: 'column', alignItems: 'flex-start' }}
                  >
                    <div style={{ display: 'flex', width: '100%', alignItems: 'center', gap: '10px' }}>
                      <div className="signal-icon">📉</div>
                      <div className="signal-content" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className="signal-product">{s.product_name}</span>
                        <span className="signal-message">{s.message}</span>
                        {onAskAdvisor && (
                          <button
                            className="ask-advisor-btn mono"
                            style={{
                              fontSize: '0.62rem',
                              marginTop: '0.35rem',
                              background: 'var(--bg-paper)',
                              border: '1px solid var(--ink-black)',
                              padding: '3px 8px',
                              cursor: 'pointer',
                              boxShadow: '2px 2px 0 var(--ink-black)',
                              alignSelf: 'flex-start',
                              fontWeight: 700
                            }}
                            onClick={(e) => {
                              e.stopPropagation()
                              onAskAdvisor(`The product "${s.product_name}" is suffering from severe margin erosion, dropping down to ${s.margin_pct}%, which is below our 20% critical threshold. What options (e.g. renegotiating COGS, optimizing bundles, raising retail price) do we have to fix this?`)
                            }}
                          >
                            Ask Advisor →
                          </button>
                        )}
                      </div>
                      <span className="signal-margin" style={{ marginLeft: 'auto', color: '#E57373' }}>{s.margin_pct}%</span>
                    </div>
                    {renderChecklist(cardId, 'margin')}
                  </div>
                )
              })
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
                        <div className="signal-content" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
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
                          {onAskAdvisor && (
                            <button
                              className="ask-advisor-btn mono"
                              style={{
                                fontSize: '0.62rem',
                                marginTop: '0.35rem',
                                background: 'var(--bg-paper)',
                                border: '1px solid var(--ink-black)',
                                padding: '3px 8px',
                                cursor: 'pointer',
                                boxShadow: '2px 2px 0 var(--ink-black)',
                                alignSelf: 'flex-start',
                                fontWeight: 700
                              }}
                              onClick={() => onAskAdvisor(`Our Holt-Winters model forecasts ~${f.forecast_qty_7d} units in sales for "${f.product_name}" over the next 7 days, showing an ${f.trend} trend (Historical: ${f.recent_qty} units). How should we adjust stock buffer or safety stock levels?`)}
                            >
                              Ask Advisor →
                            </button>
                          )}
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
