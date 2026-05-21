import React, { useState } from 'react'
import './TransactionVault.css'

function TransactionVault({ transactions, loading, onSelectTransaction, onBack }) {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('All')

  const filtered = transactions.filter(t => {
    const vendorName = t.vendor_name || t.vendor || ''
    const matchesSearch = vendorName.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === 'All' || t.category === filter
    return matchesSearch && matchesFilter
  })

  const totalExposure = transactions.reduce((acc, t) => acc + parseFloat(t.amount || 0), 0)
  const anomalyCount = transactions.filter(t => t.intelligence_meta?.anomaly?.is_anomaly).length

  const handleExportCSV = () => {
    const headers = ['Date', 'Vendor', 'Category', 'Amount (INR)', 'Status']
    const rows = filtered.map(t => {
      const isAnomaly = t.intelligence_meta?.anomaly?.is_anomaly
      const status = isAnomaly ? 'Flagged' : 'Verified'
      return [
        new Date(t.transaction_date).toLocaleDateString('en-IN'),
        `"${t.vendor_name || t.vendor || ''}"`,
        t.category,
        t.amount,
        status
      ].join(',')
    })

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', 'documind_ledger.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="transaction-vault">

      {/* Page Header */}
      <div className="vault-page-header">
        <div className="vault-header-top">
          {onBack && (
            <button className="text-btn mono" onClick={onBack}>← Back to Briefing</button>
          )}
          <p className="vault-subtitle">Archive Repository</p>
        </div>
        <h2 className="vault-title">Transaction Vault</h2>
      </div>

      {/* Controls */}
      <div className="vault-controls-grid">
        <div className="search-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search by vendor, entity..."
            className="search-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="filter-actions">
          <select
            className="action-btn"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="All">All Categories</option>
            <option value="Food">Food</option>
            <option value="Shopping">Shopping</option>
            <option value="Health">Health</option>
            <option value="Entertainment">Entertainment</option>
            <option value="Transport">Transport</option>
            <option value="Utilities">Utilities</option>
          </select>
          <button className="action-btn" onClick={handleExportCSV}>
            ↓ Export CSV
          </button>
        </div>
      </div>

      <div className="double-rule"></div>

      {/* Ledger Table */}
      <div className="ledger-table-wrapper">
        {loading ? (
          <p className="vault-loading">LOADING LEDGER...</p>
        ) : filtered.length === 0 ? (
          <p className="vault-loading">NO RECORDS MATCH YOUR SEARCH.</p>
        ) : (
          <table className="news-ledger-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Vendor / Entity</th>
                <th>Category</th>
                <th>Status</th>
                <th className="text-right">Amount (INR)</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, idx) => {
                const isAnomaly = t.intelligence_meta?.anomaly?.is_anomaly
                const status = isAnomaly ? 'Flagged' : 'Verified'

                return (
                  <tr
                    key={t.id || idx}
                    onClick={() => onSelectTransaction && onSelectTransaction(t)}
                    className="clickable-row"
                  >
                    <td className="mono">
                      {new Date(t.transaction_date).toLocaleDateString('en-IN', {
                        year: 'numeric', month: '2-digit', day: '2-digit'
                      })}
                    </td>
                    <td className="font-bold">{t.vendor_name || t.vendor}</td>
                    <td>
                      <span className="cat-tag">{t.category}</span>
                    </td>
                    <td>
                      <div className={`status-cell ${status.toLowerCase()}`}>
                        <span className="status-icon">{isAnomaly ? '⚠' : '✓'}</span>
                        <span>{status}</span>
                      </div>
                    </td>
                    <td className={`mono text-right font-bold ${isAnomaly ? 'flagged' : ''}`}>
                      ₹{parseFloat(t.amount).toLocaleString('en-IN')}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Bottom Stats */}
      <div className="vault-stats-grid">
        <div className="stat-card">
          <p className="stat-label">Vault Integrity</p>
          <div className="stat-value-group">
            <span className="stat-val">{anomalyCount > 0 ? '94.2%' : '99.9%'}</span>
            <span className="stat-sub verified">Secure</span>
          </div>
        </div>
        <div className="stat-card">
          <p className="stat-label">Aggregate Exposure</p>
          <div className="stat-value-group">
            <span className="stat-val">₹{(totalExposure / 1000).toFixed(1)}k</span>
            <span className="stat-sub">Fiscal Cycle</span>
          </div>
        </div>
        <div className="stat-card dark">
          <p className="stat-label">Terminal Status</p>
          <div className="stat-value-group">
            <span className="stat-val" style={{ color: '#7CFC00', fontSize: '1rem' }}>● ONLINE</span>
            <span className="stat-sub">Systems Nominal</span>
          </div>
        </div>
      </div>

      {/* Market Divergence / Insight Box */}
      <div className="divergence-box">
        <div className="divergence-text">
          <h3>Market Divergence</h3>
          <p>
            Financial trails indicate a {anomalyCount > 0 ? 'deviation' : 'stability'} in your spending
            throughput. {anomalyCount > 0
              ? `${anomalyCount} flagged transaction${anomalyCount > 1 ? 's' : ''} require review.`
              : 'Ledger verification is current — all entries within normal parameters.'}
          </p>
        </div>
      </div>

    </div>
  )
}

export default TransactionVault
