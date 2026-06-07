import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import { useToast } from './Toast'
import './AuditConsole.css'

// ── Helper: render Markdown-ish text as JSX ────────────────────────────────
const renderMarkdown = (text) => {
  if (!text) return <p className="empty-note">AI Commentary is empty or unavailable.</p>
  return text.split('\n').map((line, idx) => {
    if (line.startsWith('### ')) return <h3 key={idx} className="md-h3">{line.slice(4)}</h3>
    if (line.startsWith('## '))  return <h2 key={idx} className="md-h2">{line.slice(3)}</h2>
    if (line.startsWith('- ') || line.startsWith('* '))
      return <li key={idx} className="md-li">{line.slice(2)}</li>
    if (/^\d+\. /.test(line))
      return <li key={idx} className="md-li md-ol">{line.replace(/^\d+\. /, '')}</li>
    if (line.trim() === '') return <div key={idx} className="md-spacer" />
    // Bold (**text**)
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    return (
      <p key={idx} className="md-p">
        {parts.map((part, i) =>
          part.startsWith('**') && part.endsWith('**')
            ? <strong key={i}>{part.slice(2, -2)}</strong>
            : part
        )}
      </p>
    )
  })
}

// ── Severity badge helper ──────────────────────────────────────────────────
const SeverityBadge = ({ level }) => (
  <span className={`severity-badge ${level}`}>{level.toUpperCase()}</span>
)

// ── Stat Card ─────────────────────────────────────────────────────────────
const StatCard = ({ label, value, sub, accent }) => (
  <div className={`ac-stat-card ${accent || ''}`}>
    <span className="ac-stat-label">{label}</span>
    <span className="ac-stat-value">{value}</span>
    {sub && <span className="ac-stat-sub">{sub}</span>}
  </div>
)

// ── Upload Log Drawer ─────────────────────────────────────────────────────
const UploadLogDrawer = ({ upload, onClose }) => {
  const { showToast } = useToast()
  const [log, setLog] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!upload?.id) return
    setLoading(true)
    api.getUploadLog(upload.id)
      .then(res => setLog(res?.data || null))
      .catch(err => showToast('error', 'Could not load error log: ' + err.message))
      .finally(() => setLoading(false))
  }, [upload?.id])

  const categories = log
    ? ['null', 'type', 'format', 'validation', 'duplicate', 'schema', 'limit']
        .map(cat => ({
          cat,
          items: (log.log || []).filter(e => e.category === cat),
        }))
        .filter(g => g.items.length > 0)
    : []

  return (
    <div className="log-drawer-overlay" onClick={onClose}>
      <div className="log-drawer" onClick={e => e.stopPropagation()}>
        <div className="log-drawer-header">
          <div>
            <span className="mono-kicker">Ingestion Trace</span>
            <h3>{upload?.filename}</h3>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Close log">✕</button>
        </div>

        {loading ? (
          <div className="loading-spinner">Loading per-row error trace…</div>
        ) : !log ? (
          <div className="empty-note">No log data available for this upload.</div>
        ) : (
          <>
            <div className="log-summary-row">
              <div className="log-pill">Total Rows <strong>{log.rows_total ?? '—'}</strong></div>
              <div className="log-pill success">Imported <strong>{log.records_processed ?? '—'}</strong></div>
              <div className="log-pill warn">Errors <strong>{log.validation_error_count ?? 0}</strong></div>
              <div className="log-pill">Duplicates <strong>{log.duplicates_skipped ?? 0}</strong></div>
            </div>

            {categories.length === 0 ? (
              <div className="empty-note" style={{ marginTop: '1rem' }}>✅ No validation errors — clean ingestion.</div>
            ) : categories.map(({ cat, items }) => (
              <div key={cat} className="log-category-group">
                <div className="log-cat-header">
                  <span className={`log-cat-badge ${cat}`}>{cat.toUpperCase()}</span>
                  <span className="log-cat-count">{items.length} row(s)</span>
                </div>
                <div className="log-items">
                  {items.slice(0, 20).map((e, i) => (
                    <div key={i} className="log-item-row mono">
                      <span className="log-row-num">Row {e.row}</span>
                      <span className="log-msg">{e.message}</span>
                    </div>
                  ))}
                  {items.length > 20 && (
                    <div className="log-overflow">+{items.length - 20} more rows not shown</div>
                  )}
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────
const AuditConsole = ({ selectedStore, onRefreshSummary }) => {
  const { showToast } = useToast()

  const [audits, setAudits]             = useState([])
  const [uploads, setUploads]           = useState([])
  const [selectedAudit, setSelectedAudit] = useState(null)
  const [auditDetail, setAuditDetail]   = useState(null)  // full detail with anomaly_snapshot
  const [loadingAudits, setLoadingAudits]   = useState(false)
  const [loadingUploads, setLoadingUploads] = useState(false)
  const [loadingDetail, setLoadingDetail]   = useState(false)
  const [runningAudit, setRunningAudit] = useState(false)
  const [logUpload, setLogUpload]       = useState(null)  // upload opened in drill-down
  const [activeTab, setActiveTab]       = useState('audits') // 'audits' | 'uploads'

  const storeId = selectedStore?.id || ''

  // ── Data fetchers ──────────────────────────────────────────────────────
  const fetchAudits = useCallback(async () => {
    setLoadingAudits(true)
    try {
      const res = await api.getAudits(storeId)
      if (res?.data) {
        setAudits(res.data)
        if (res.data.length > 0 && !selectedAudit) {
          setSelectedAudit(res.data[0])
        }
      }
    } catch (err) {
      showToast('error', 'Failed to load audits: ' + err.message)
    } finally {
      setLoadingAudits(false)
    }
  }, [storeId])

  const fetchUploadHistory = useCallback(async () => {
    setLoadingUploads(true)
    try {
      const res = await api.getUploadHistory(20, 0, storeId)
      setUploads(res?.data || res || [])
    } catch (err) {
      showToast('error', 'Failed to load upload history: ' + err.message)
    } finally {
      setLoadingUploads(false)
    }
  }, [storeId])

  const fetchAuditDetail = useCallback(async (auditId) => {
    if (!auditId) return
    setLoadingDetail(true)
    try {
      const res = await api.getAuditDetail(auditId)
      if (res?.data) setAuditDetail(res.data)
    } catch (err) {
      showToast('error', 'Failed to load audit detail: ' + err.message)
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  useEffect(() => {
    fetchAudits()
    fetchUploadHistory()
  }, [storeId])

  useEffect(() => {
    if (selectedAudit?.id) fetchAuditDetail(selectedAudit.id)
  }, [selectedAudit?.id])

  // ── Actions ────────────────────────────────────────────────────────────
  const handleRunAudit = async () => {
    setRunningAudit(true)
    showToast('info', 'Running Z-Score checks, Holt-Winters forecast, and generating AI executive report…')
    try {
      const res = await api.runAudit(storeId)
      if (res?.success) {
        showToast('success', 'Audit briefing compiled successfully!')
        const newAudit = res.data
        setAudits(prev => [newAudit, ...prev])
        setSelectedAudit(newAudit)
        setAuditDetail(newAudit)  // response already has anomaly_snapshot
        if (onRefreshSummary) onRefreshSummary()
      }
    } catch (err) {
      showToast('error', 'Audit failed: ' + err.message)
    } finally {
      setRunningAudit(false)
    }
  }

  const handleOpenHtmlReport = (auditId) => {
    if (!auditId) return
    window.open(api.getAuditExportUrl(auditId), '_blank')
  }

  const handleDownloadMarkdown = (auditId) => {
    if (!auditId) return
    const a = document.createElement('a')
    a.href = api.getAuditMarkdownUrl(auditId)
    a.download = `retailmind_audit_${auditId.slice(0, 8)}.md`
    a.click()
  }

  // ── Snapshot extraction helpers ────────────────────────────────────────
  const snap = auditDetail?.anomaly_snapshot || selectedAudit?.anomaly_snapshot || {}
  const fmt = (n) => typeof n === 'number' ? n.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : (n ?? '—')
  const fmtCur = (n) => typeof n === 'number' ? `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—'
  const demandSpikes    = snap.demand_signals        || []
  const deadStock       = snap.dead_stock_alerts     || []
  const marginErosion   = snap.margin_erosion_alerts || []
  const topProducts     = snap.top_products          || []
  const forecastSummary = snap.revenue_forecast_14d_summary || {}
  const momPct          = snap.mom_revenue_change_pct ?? 0
  const anomalyCount    = (auditDetail || selectedAudit)?.anomalies_detected ?? 0

  return (
    <div className="audit-console-grid">

      {/* ── LEFT: Nav (Audits / Uploads) + Lists ── */}
      <div className="audit-panel roster-panel">
        <div className="panel-header">
          <span className="mono-kicker">Operations Console</span>
          <div className="console-tabs">
            <button
              className={`console-tab ${activeTab === 'audits' ? 'active' : ''}`}
              onClick={() => setActiveTab('audits')}
            >📊 Audits</button>
            <button
              className={`console-tab ${activeTab === 'uploads' ? 'active' : ''}`}
              onClick={() => setActiveTab('uploads')}
            >📂 Upload Logs</button>
          </div>
        </div>

        {activeTab === 'audits' && (
          <>
            <button
              className="mono-btn primary run-audit-btn"
              onClick={handleRunAudit}
              disabled={runningAudit}
            >
              {runningAudit ? '⚙ Compiling Audit…' : '⚙ Run Store Audit'}
            </button>
            <p className="panel-helper-text">
              Runs Z-Score detection, Holt-Winters forecast, and generates an AI executive briefing via Groq.
            </p>
            {loadingAudits ? (
              <div className="loading-spinner">Loading audit roster…</div>
            ) : audits.length === 0 ? (
              <div className="empty-panel-state">
                <p>No audits registered. Run your first store audit above.</p>
              </div>
            ) : (
              <div className="audits-list">
                {audits.map(aud => (
                  <div
                    key={aud.id}
                    className={`audit-roster-item ${selectedAudit?.id === aud.id ? 'active' : ''}`}
                    onClick={() => setSelectedAudit(aud)}
                  >
                    <div className="item-meta">
                      <span className="audit-date mono">{aud.audit_date}</span>
                      <span className="audit-id-badge mono">#{aud.id.slice(0, 8)}</span>
                    </div>
                    <div className="item-stats">
                      <span className="stat-label">Checked: <strong>{aud.total_products_checked}</strong></span>
                      <span className={`stat-anomalies ${aud.anomalies_detected > 0 ? 'alert' : ''}`}>
                        Alerts: <strong>{aud.anomalies_detected}</strong>
                      </span>
                    </div>
                    {aud.has_snapshot && <span className="snapshot-dot" title="Full snapshot available">●</span>}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'uploads' && (
          <>
            <button
              className="mono-btn refresh-btn"
              onClick={fetchUploadHistory}
              disabled={loadingUploads}
            >
              ↻ Refresh Logs
            </button>
            {loadingUploads ? (
              <div className="loading-spinner">Loading ingestion logs…</div>
            ) : uploads.length === 0 ? (
              <div className="empty-panel-state">
                <p>No uploads found. Ingest a CSV file to view preprocessing logs.</p>
              </div>
            ) : (
              <div className="uploads-list">
                {uploads.map(up => (
                  <div key={up.id} className={`upload-log-card ${up.status}`}>
                    <div className="log-card-header">
                      <span className="log-filename" title={up.filename}>{up.filename}</span>
                      <span className={`log-status-badge ${up.status}`}>{up.status.toUpperCase()}</span>
                    </div>
                    <div className="log-card-body">
                      <div className="log-stats-row">
                        <span className="log-pill">Total <strong>{up.rows_total ?? '—'}</strong></span>
                        <span className="log-pill success">OK <strong>{up.records_processed}</strong></span>
                        {up.duplicates_skipped > 0 && (
                          <span className="log-pill dupe">Dupes <strong>{up.duplicates_skipped}</strong></span>
                        )}
                        {up.error_count > 0 && (
                          <span className="log-pill warn">Errors <strong>{up.error_count}</strong></span>
                        )}
                      </div>
                      <div className="log-date mono">
                        {new Date(up.created_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })}
                      </div>
                      {up.error_count > 0 && (
                        <button
                          className="mono-btn secondary log-drill-btn"
                          onClick={() => setLogUpload(up)}
                        >
                          🔍 Inspect Error Log ({up.error_count} issues)
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* ── CENTER: Audit Report Viewer ── */}
      <div className="audit-panel report-panel" id="printable-audit-report">
        {!selectedAudit ? (
          <div className="empty-panel-state center-empty">
            <span className="empty-icon">📊</span>
            <p>Select an audit from the roster or run a new audit to view the executive report.</p>
          </div>
        ) : (
          <>
            {/* Report Header */}
            <div className="panel-header report-header no-print">
              <div>
                <span className="mono-kicker">Report Briefing</span>
                <h2>Audit Snapshot — {selectedAudit.audit_date}</h2>
              </div>
              <div className="report-actions">
                <button
                  className="mono-btn secondary"
                  onClick={() => handleOpenHtmlReport(selectedAudit.id)}
                  title="Opens a print-ready HTML report in a new tab"
                >
                  🖨 Print / PDF Report
                </button>
                <button
                  className="mono-btn secondary"
                  onClick={() => handleDownloadMarkdown(selectedAudit.id)}
                  title="Download raw Markdown report"
                >
                  📄 Download .md
                </button>
              </div>
            </div>

            {loadingDetail ? (
              <div className="loading-spinner" style={{ padding: '2rem' }}>Loading full audit detail…</div>
            ) : (
              <div className="audit-report-sheet">

                {/* Sheet masthead */}
                <div className="sheet-masthead">
                  <div className="masthead-main-title">RETAILMIND AUDIT TELEMETRY</div>
                  <div className="masthead-details">
                    <div><strong>AUDIT ID:</strong> #{(auditDetail?.id || selectedAudit.id).slice(0, 8).toUpperCase()}</div>
                    <div><strong>DATE:</strong> {(auditDetail || selectedAudit).audit_date}</div>
                    <div><strong>STORE:</strong> {selectedStore ? selectedStore.name : 'All Locations'}</div>
                  </div>
                </div>

                {/* KPI Scorecard */}
                <div className="ac-kpi-grid">
                  <StatCard
                    label="Total Revenue (MTD)"
                    value={fmtCur(snap.total_revenue)}
                    sub={`${momPct >= 0 ? '+' : ''}${fmt(momPct)}% vs prior`}
                    accent={momPct >= 0 ? 'green' : 'red'}
                  />
                  <StatCard
                    label="Gross Profit"
                    value={fmtCur(snap.gross_profit)}
                    sub={`Margin: ${fmt(snap.overall_margin_pct)}%`}
                  />
                  <StatCard
                    label="Products Audited"
                    value={fmt(snap.total_products_checked || (auditDetail || selectedAudit).total_products_checked)}
                    sub="Unique SKUs tracked"
                  />
                  <StatCard
                    label="Risk Alerts"
                    value={anomalyCount}
                    sub={`${demandSpikes.length} spikes · ${deadStock.length} dead · ${marginErosion.length} margin`}
                    accent={anomalyCount > 0 ? 'red' : 'green'}
                  />
                </div>

                {/* Forecast Summary (if available) */}
                {forecastSummary.projected_total_14d != null && (
                  <div className="ac-forecast-strip">
                    <span className="forecast-label">📈 14-Day Revenue Forecast</span>
                    <div className="forecast-cards">
                      <div className="forecast-card">
                        <span>Projected Total</span>
                        <strong>{fmtCur(forecastSummary.projected_total_14d)}</strong>
                      </div>
                      <div className="forecast-card">
                        <span>Peak Day</span>
                        <strong>{forecastSummary.peak_day || '—'}</strong>
                        <small>{fmtCur(forecastSummary.peak_revenue)}</small>
                      </div>
                      <div className="forecast-card">
                        <span>Trough Day</span>
                        <strong>{forecastSummary.trough_day || '—'}</strong>
                        <small>{fmtCur(forecastSummary.trough_revenue)}</small>
                      </div>
                    </div>
                  </div>
                )}

                {/* AI Report */}
                <div className="report-section">
                  <div className="section-kicker-label">🤖 AI Executive Report</div>
                  <div className="report-markdown-content">
                    {renderMarkdown((auditDetail || selectedAudit).ai_audit_summary)}
                  </div>
                </div>

                {/* Top Products Table */}
                {topProducts.length > 0 && (
                  <div className="report-section">
                    <div className="section-kicker-label">📦 Top 5 Products by Revenue</div>
                    <table className="ac-table">
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>Category</th>
                          <th>Revenue</th>
                          <th>Units</th>
                          <th>Margin %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topProducts.map((p, i) => (
                          <tr key={i}>
                            <td><strong>{p.product_name}</strong></td>
                            <td>{p.category}</td>
                            <td>{fmtCur(p.revenue)}</td>
                            <td>{fmt(p.quantity)}</td>
                            <td>
                              <span className={`margin-chip ${p.margin_pct >= 25 ? 'good' : p.margin_pct >= 10 ? 'warn' : 'bad'}`}>
                                {fmt(p.margin_pct)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Demand Spikes */}
                {demandSpikes.length > 0 && (
                  <div className="report-section">
                    <div className="section-kicker-label">⚡ Demand Spike Alerts ({demandSpikes.length})</div>
                    <table className="ac-table">
                      <thead>
                        <tr><th>Product</th><th>Z-Score</th><th>Deviation</th><th>Recent Vol</th></tr>
                      </thead>
                      <tbody>
                        {demandSpikes.map((s, i) => (
                          <tr key={i}>
                            <td><strong>{s.product_name}</strong></td>
                            <td>
                              <span className={`severity-badge ${s.z_score > 3 ? 'critical' : 'warning'}`}>
                                {(s.z_score || 0).toFixed(2)}
                              </span>
                            </td>
                            <td>+{(s.deviation_pct || 0).toFixed(0)}%</td>
                            <td>{(s.recent_qty || 0).toFixed(0)} units</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Dead Stock */}
                {deadStock.length > 0 && (
                  <div className="report-section">
                    <div className="section-kicker-label">🧊 Dead Stock Alerts ({deadStock.length})</div>
                    <table className="ac-table">
                      <thead>
                        <tr><th>Product</th><th>Days Inactive</th><th>Note</th></tr>
                      </thead>
                      <tbody>
                        {deadStock.map((d, i) => (
                          <tr key={i}>
                            <td><strong>{d.product_name}</strong></td>
                            <td>
                              <span className={`severity-badge ${d.last_sale_days_ago > 45 ? 'critical' : 'warning'}`}>
                                {d.last_sale_days_ago}d
                              </span>
                            </td>
                            <td>{d.message}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Margin Erosion */}
                {marginErosion.length > 0 && (
                  <div className="report-section">
                    <div className="section-kicker-label">📉 Margin Erosion Alerts ({marginErosion.length})</div>
                    <table className="ac-table">
                      <thead>
                        <tr><th>Product</th><th>Avg Margin</th><th>Total Revenue</th></tr>
                      </thead>
                      <tbody>
                        {marginErosion.map((m, i) => (
                          <tr key={i}>
                            <td><strong>{m.product_name}</strong></td>
                            <td>
                              <span className={`severity-badge ${m.margin_pct < 5 ? 'critical' : 'warning'}`}>
                                {(m.margin_pct || 0).toFixed(1)}%
                              </span>
                            </td>
                            <td>{fmtCur(m.revenue)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Clean bill if no anomalies and snapshot loaded */}
                {anomalyCount === 0 && snap.total_products_checked > 0 && (
                  <div className="clean-bill">
                    ✅ All {snap.total_products_checked} products passed anomaly checks. No alerts detected.
                  </div>
                )}

                <div className="sheet-footer">
                  RetailMind Operational Audit · Confidential Internal Records
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Upload Log Drawer ── */}
      {logUpload && (
        <UploadLogDrawer
          upload={logUpload}
          onClose={() => setLogUpload(null)}
        />
      )}
    </div>
  )
}

export default AuditConsole
