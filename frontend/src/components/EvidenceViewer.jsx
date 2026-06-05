
function EvidenceViewer({ transaction, onClose }) {
  if (!transaction) return null

  const imageUrl = transaction.document_path
    ? `http://localhost:8000/uploads/${transaction.document_path.split(/[/\\]/).pop()}`
    : null

  const confidence = transaction.confidence || 0.9

  return (
    <>
      {/* Backdrop */}
      <div className="evidence-overlay" onClick={onClose} />

      {/* Drawer */}
      <div className="evidence-drawer">
        <div className="drawer-header">
          <span className="mono">Evidence — {String(transaction.id || '').slice(0, 8)}</span>
          <button className="close-btn" onClick={onClose} aria-label="Close evidence viewer">×</button>
        </div>

        <div className="drawer-content">
          {/* Receipt Image */}
          <div className="receipt-frame">
            {imageUrl ? (
              <img
                src={imageUrl}
                alt={`Receipt from ${transaction.vendor_name || transaction.vendor}`}
                className="receipt-image"
              />
            ) : (
              <div className="receipt-placeholder">
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem', opacity: 0.3 }}>🧾</div>
                <p>No image attached</p>
                <p style={{ fontSize: '0.6rem' }}>Upload a receipt to see it here</p>
              </div>
            )}
          </div>

          {/* Transaction Details */}
          <div className="evidence-meta">
            <h3>{transaction.vendor_name || transaction.vendor}</h3>

            <div className="evidence-row">
              <span className="ev-label">Transaction Date</span>
              <span className="ev-value">{transaction.transaction_date}</span>
            </div>
            <div className="evidence-row">
              <span className="ev-label">Amount</span>
              <span className="ev-value">₹{parseFloat(transaction.amount).toLocaleString('en-IN')}</span>
            </div>
            <div className="evidence-row">
              <span className="ev-label">Category</span>
              <span className="ev-value">{transaction.category || 'Uncategorized'}</span>
            </div>
            {transaction.intelligence_meta?.anomaly?.is_anomaly && (
              <div className="evidence-row">
                <span className="ev-label" style={{ color: 'var(--ink-red)' }}>Anomaly Flag</span>
                <span className="ev-value" style={{ color: 'var(--ink-red)' }}>FLAGGED</span>
              </div>
            )}
          </div>

          {/* AI Confidence */}
          <div className="ai-confidence-section">
            <h4>AI Confidence Score</h4>
            <div className="confidence-bar">
              <div
                className="confidence-fill"
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
            <p className="confidence-note">
              {(confidence * 100).toFixed(0)}% — {transaction.notes || 'Automated classification based on merchant patterns and receipt analysis.'}
            </p>
          </div>
        </div>
      </div>
    </>
  )
}

export default EvidenceViewer
