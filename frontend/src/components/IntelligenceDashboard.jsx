import React, { useState } from 'react'
import './IntelligenceDashboard.css'
import SalesLedger from './SalesLedger'
import MLArchitectureMap from './MLArchitectureMap'
import RevenueHero from './RevenueHero'
import DemandSignals from './DemandSignals'
import TopProductsTable from './TopProductsTable'
import SalesTrendGraph from './SalesTrendGraph'
import DateRangeToggle from './DateRangeToggle'
import PortfolioMatrix from './PortfolioMatrix'
import CustomerSegmentsPanel from './CustomerSegmentsPanel'
import UserManual from './UserManual'
import DocumentScanner from './DocumentScanner'
import { api } from '../services/api'
import { useToast } from './Toast'

const IntelligenceDashboard = ({
  summary,
  sales,
  user,
  loading,
  onShowSettings,
  onLogout,
  onShowChat,
  onRefresh,
  currency = 'INR',
  stores = [],
  selectedStore = null,
  onSelectStore,
  onCreateStore,
  onAskAdvisor,
}) => {
  const { showToast } = useToast()
  const [activeView, setActiveView] = useState('briefing')
  const [showArchitecture, setShowArchitecture] = useState(false)
  const [showScanner, setShowScanner] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [period, setPeriod] = useState('mtd')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [ledgerProductFilter, setLedgerProductFilter] = useState(null)
  const fileInputRef = React.useRef(null)

  const [showStoreModal, setShowStoreModal] = useState(false)
  const [newStoreName, setNewStoreName] = useState('')
  const [newStoreLoc, setNewStoreLoc] = useState('')

  const handleCreateStoreSubmit = async (e) => {
    e.preventDefault()
    if (!newStoreName.trim() || !newStoreLoc.trim()) return
    await onCreateStore(newStoreName.trim(), newStoreLoc.trim())
    setNewStoreName('')
    setNewStoreLoc('')
  }

  const handleUploadClick = () => fileInputRef.current.click()

  const processFile = async (file) => {
    if (!file) return

    // Client-side size check (10 MB)
    if (file.size > 10 * 1024 * 1024) {
      showToast('error', 'File exceeds 10 MB limit. Please split your data into smaller files.')
      return
    }

    // Client-side type check
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!['csv', 'txt', 'xlsx'].includes(extension)) {
      showToast('error', 'Supported formats: .csv, .txt, .xlsx')
      return
    }

    setUploading(true)
    try {
      const result = await api.uploadSalesCsv(file, selectedStore?.id)
      showToast('success', result.message || `Imported ${result.inserted} records.`)
      if (result.errors > 0) {
        showToast('warning', `${result.errors} rows had errors and were skipped.`)
      }
      onRefresh(period, dateFrom, dateTo)
    } catch (err) {
      showToast('error', err.message || 'Upload failed. Check your file format.')
    } finally {
      setUploading(false)
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (file) {
      await processFile(file)
    }
    e.target.value = ''
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) {
      await processFile(file)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handlePeriodChange = ({ period: p, dateFrom: df, dateTo: dt }) => {
    setPeriod(p)
    setDateFrom(df)
    setDateTo(dt)
    // Trigger a refresh with the new period params
    onRefresh(p, df, dt)
  }

  const downloadTemplate = () => {
    window.open(api.getTemplateCsvUrl(), '_blank')
  }

  const totalAlerts =
    (summary?.demand_signals?.length ?? 0) +
    (summary?.dead_stock_alerts?.length ?? 0) +
    (summary?.margin_erosion_alerts?.length ?? 0)

  return (
    <div className="newsprint-container">

      {/* ── Masthead ── */}
      <header className="masthead">
        <div className="masthead-ticker">
          <div className="masthead-ticker-edition">
            <span>VOL. I — RETAIL EDITION</span>
            <span>POWERED BY AI</span>
            <span>SMB INTELLIGENCE BUREAU</span>
          </div>
          <span>RETAILMIND INTEL CORP.</span>
        </div>

        <div className="masthead-main">
          <div className="masthead-title-block">
            <h1 className="masthead-title">RetailMind</h1>
            <span className="masthead-tagline">Business Intelligence Bulletin</span>
          </div>
          <div className="masthead-actions">
            <button className="mono-btn" onClick={() => setShowArchitecture(true)}>System</button>
            <button className="mono-btn" onClick={onShowSettings}>Settings</button>
            <button className="mono-btn alert" onClick={onLogout}>Logout</button>
          </div>
        </div>

        <div className="masthead-byline">
          <span className="byline-date">
            {new Date().toLocaleDateString('en-IN', {
              weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
            })}
          </span>
          <span className="byline-edition">
            <span className="byline-store-selector-trigger" onClick={() => setShowStoreModal(true)}>
              🏬 <strong>{selectedStore ? selectedStore.name : 'Select Store'}</strong>
              {selectedStore?.location && <span className="store-loc"> ({selectedStore.location})</span>}
              <span className="dropdown-arrow"> ▼</span>
            </span>
          </span>
          {totalAlerts > 0 && (
            <span className="byline-alerts">
              ⚠ {totalAlerts} Active Alert{totalAlerts !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </header>

      {/* ── Nav ── */}
      <nav className="view-nav">
        <button
          className={`view-nav-btn ${activeView === 'briefing' ? 'active' : ''}`}
          onClick={() => setActiveView('briefing')}
        >
          📰 Intelligence Briefing
        </button>
        <button
          className={`view-nav-btn ${activeView === 'ledger' ? 'active' : ''}`}
          onClick={() => setActiveView('ledger')}
        >
          📋 Sales Ledger
        </button>
      </nav>

      {/* ── Main Content ── */}
      <main>
        {activeView === 'briefing' ? (
          <>
            {/* Date range toggle — full width above columns */}
            <div className="briefing-period-bar">
              <DateRangeToggle
                period={period}
                dateFrom={dateFrom}
                dateTo={dateTo}
                onChange={handlePeriodChange}
              />
              {summary?.date_from && summary?.date_to && (
                <span className="period-label mono">
                  {summary.date_from} → {summary.date_to}
                </span>
              )}
            </div>

            <div className="briefing-grid">
              {/* LEFT — main analytics column */}
              <div className="briefing-col-main">
                <UserManual />
                {loading ? (
                <div className="broadsheet-skeleton">
                  {/* Revenue hero skeleton */}
                  <div className="section-pad">
                    <div className="skeleton-grid-cols">
                      <div className="skeleton-col-box"><div className="skeleton-line sub" /><div className="skeleton-line header" /></div>
                      <div className="skeleton-col-box"><div className="skeleton-line sub" /><div className="skeleton-line header" /></div>
                      <div className="skeleton-col-box"><div className="skeleton-line sub" /><div className="skeleton-line header" /></div>
                      <div className="skeleton-col-box"><div className="skeleton-line sub" /><div className="skeleton-line header" /></div>
                    </div>
                  </div>
                  {/* Chart skeleton */}
                  <div className="section-pad">
                    <div className="skeleton-line kicker" />
                    <div className="skeleton-line header" />
                    <div className="skeleton-chart-box">COMPILING BUSINESS SALES LEDGER TRENDS...</div>
                  </div>
                  {/* Table skeleton */}
                  <div className="section-pad">
                    <div className="skeleton-line kicker" />
                    <div className="skeleton-line header" />
                    <div className="skeleton-line text-long" />
                    <div className="skeleton-line text-mid" />
                    <div className="skeleton-line text-long" />
                    <div className="skeleton-line text-short" />
                  </div>
                </div>
              ) : (
                <>
                  <div className="section-pad">
                    <RevenueHero summary={summary} currency={currency} />
                  </div>
                  <div className="section-pad" id="tour-sales-graph">
                    <SalesTrendGraph sales={sales} categoryBreakdown={summary?.category_breakdown} forecast={summary?.revenue_forecast_14d ?? []} currency={currency} />
                  </div>
                  <div className="section-pad">
                    <TopProductsTable products={summary?.top_products ?? []} currency={currency} />
                  </div>
                  <div className="section-pad">
                    <PortfolioMatrix
                      period={period}
                      dateFrom={dateFrom}
                      dateTo={dateTo}
                      storeId={selectedStore?.id}
                      currency={currency}
                      onQuadrantSelect={(productNames, quadName) => {
                        setLedgerProductFilter(productNames)
                        setActiveView('ledger')
                        showToast('success', `Filtered ledger by ${quadName} quadrant`)
                      }}
                    />
                  </div>

                  {/* Category Breakdown */}
                  <div className="section-pad">
                    <div className="section-kicker">
                      <span className="kicker-label">Category Performance</span>
                      <div className="kicker-line" />
                    </div>
                    <div className="category-breakdown">
                      {(summary?.category_breakdown ?? []).map((cat) => (
                        <div className="cat-row" key={cat.category}>
                          <span className="cat-name">{cat.category}</span>
                          <div className="cat-bar-track">
                            <div
                              className="cat-bar-fill"
                              style={{
                                width: `${Math.min(
                                  (cat.revenue /
                                    Math.max(...(summary.category_breakdown.map(c => c.revenue)), 1)) * 100,
                                  100
                                )}%`,
                              }}
                            />
                          </div>
                          <span className="cat-margin" style={{ color: cat.margin_pct >= 25 ? '#4CAF50' : '#E57373' }}>
                            {cat.margin_pct.toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* RIGHT — signals + upload + AI */}
            <div className="briefing-col-side">
              {loading ? (
                <div className="broadsheet-skeleton">
                  {/* Signals skeleton */}
                  <div className="section-pad">
                    <div className="skeleton-line kicker" />
                    <div className="skeleton-line header" />
                    <div className="skeleton-line text-long" />
                    <div className="skeleton-line text-mid" />
                    <div className="skeleton-line text-long" />
                    <div className="skeleton-line text-short" />
                  </div>
                  {/* Upload box skeleton */}
                  <div className="section-pad">
                    <div className="skeleton-line kicker" />
                    <div className="skeleton-line header" style={{ height: '50px' }} />
                  </div>
                  {/* AI dispatch skeleton */}
                  <div className="section-pad">
                    <div className="skeleton-line kicker" />
                    <div className="skeleton-line text-long" />
                    <div className="skeleton-line text-short" />
                  </div>
                </div>
              ) : (
                <>
                  <div className="section-pad" id="tour-alerts">
                    <DemandSignals
                      demandSignals={summary?.demand_signals ?? []}
                      deadStockAlerts={summary?.dead_stock_alerts ?? []}
                      marginAlerts={summary?.margin_erosion_alerts ?? []}
                      currency={currency}
                      onAskAdvisor={onAskAdvisor}
                      storeId={selectedStore?.id}
                    />
                  </div>

                  {/* Customer Segment Analytics Panel */}
                  <div className="section-pad">
                    <CustomerSegmentsPanel
                      customerSegments={summary?.customer_segments ?? []}
                      currency={currency}
                      onAskAdvisor={onAskAdvisor}
                    />
                  </div>

                  {/* CSV Upload */}
                  <div className="section-pad upload-section" id="tour-upload">
                    <div className="section-kicker">
                      <span className="kicker-label">Data Import</span>
                      <div className="kicker-line" />
                    </div>
                    <input
                      type="file"
                      ref={fileInputRef}
                      style={{ display: 'none' }}
                      onChange={handleFileChange}
                      accept=".csv,.txt,.xlsx"
                    />
                    <div
                      className={`upload-box ${uploading ? 'uploading' : ''} ${isDragging ? 'dragging' : ''}`}
                      onClick={handleUploadClick}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      style={{ 
                        cursor: uploading ? 'wait' : 'pointer',
                        border: isDragging ? '2px dashed var(--ink-blue)' : undefined,
                        background: isDragging ? 'var(--bg-tint)' : undefined
                      }}
                      role="button"
                      tabIndex={0}
                      aria-label="Upload sales CSV or Excel file"
                      onKeyDown={e => e.key === 'Enter' && handleUploadClick()}
                    >
                      <span className="upload-icon">{uploading ? '⏳' : (isDragging ? '📥' : '↑')}</span>
                      <span className="mono">{uploading ? 'Importing…' : (isDragging ? 'Drop File Here' : 'Upload Sales File')}</span>
                      <span className="upload-subtitle">
                        CSV · Excel (.xlsx) · Auto-detects column headers
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                      <button className="template-btn" style={{ flex: 1, margin: 0 }} onClick={downloadTemplate}>
                        ↓ CSV Template
                      </button>
                      <button 
                        className="template-btn" 
                        style={{ flex: 1, margin: 0, borderColor: 'var(--ink-red)', color: 'var(--ink-red)' }} 
                        onClick={() => setShowScanner(true)}
                      >
                        📷 AI Scan Receipt
                      </button>
                    </div>
                  </div>

                  {/* AI Insight */}
                  <div className="section-pad insight-section">
                    <div className="insight-card">
                      <p className="insight-label">Bureau of Retail Intelligence · AI Dispatch</p>
                      <p className="insight-quote">"{summary?.ai_insight ?? 'Analysing your retail data...'}"</p>
                      <button className="ask-btn" onClick={onShowChat}>Ask Retail Advisor →</button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
          </>
        ) : (
          <div className="full-view-container">
            <SalesLedger
              sales={sales}
              currency={currency}
              initialProductNames={ledgerProductFilter}
              onBack={() => {
                setLedgerProductFilter(null)
                setActiveView('briefing')
              }}
            />
          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="newsprint-footer">
        <p>© 2025 RetailMind Intel Corp. · Powered by Gemini AI · All Rights Reserved</p>
        <div className="footer-links">
          <span>Terms</span>
          <span>Privacy</span>
          <span>Data Ethics</span>
        </div>
      </footer>

      {/* ── Overlays ── */}
      {showArchitecture && (
        <MLArchitectureMap onClose={() => setShowArchitecture(false)} />
      )}
      
      {showScanner && (
        <DocumentScanner
          onClose={() => setShowScanner(false)}
          onComplete={() => {
            onRefresh(period, dateFrom, dateTo)
            setShowScanner(false)
          }}
          selectedStore={selectedStore}
          currency={currency}
        />
      )}

      {/* Store Selector Modal */}
      {showStoreModal && (
        <div className="store-modal-overlay">
          <div className="store-modal">
            <div className="store-modal-header">
              <span className="mono-kicker">Location Roster</span>
              <h2>Select Retail Store</h2>
              <button className="close-btn" onClick={() => setShowStoreModal(false)}>✕</button>
            </div>
            
            <div className="store-list">
              {stores.length === 0 ? (
                <div className="empty-state">No retail stores registered.</div>
              ) : (
                stores.map(st => (
                  <div 
                    key={st.id} 
                    className={`store-item ${selectedStore?.id === st.id ? 'active' : ''}`}
                    onClick={() => {
                      onSelectStore(st.id)
                      setShowStoreModal(false)
                    }}
                  >
                    <div className="store-item-info">
                      <span className="store-item-name">{st.name}</span>
                      <span className="store-item-loc">{st.location || 'No Location'}</span>
                    </div>
                    {selectedStore?.id === st.id ? (
                      <span className="store-active-badge">ACTIVE</span>
                    ) : (
                      <span className="store-switch-prompt">SWITCH</span>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="store-modal-divider" />

            <form onSubmit={handleCreateStoreSubmit} className="store-create-form">
              <h3>Register New Location</h3>
              <div className="form-fields">
                <input 
                  type="text" 
                  placeholder="Store Name" 
                  value={newStoreName}
                  onChange={e => setNewStoreName(e.target.value)}
                  required
                />
                <input 
                  type="text" 
                  placeholder="Location" 
                  value={newStoreLoc}
                  onChange={e => setNewStoreLoc(e.target.value)}
                  required
                />
                <button type="submit" className="mono-btn">Register</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default IntelligenceDashboard
