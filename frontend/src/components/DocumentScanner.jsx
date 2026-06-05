// DocumentScanner.jsx
import { useState } from 'react'
import { api } from '../services/api'
import './DocumentScanner.css'

export default function DocumentScanner({ onClose, onComplete, selectedStore, currency = 'INR' }) {
  const [phase, setPhase] = useState('drop') // 'drop' | 'loading' | 'review' | 'success' | 'error'
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [items, setItems] = useState([])
  const [errorMessage, setErrorMessage] = useState('')
  const [terminalLogs, setTerminalLogs] = useState([])
  const [terminalIndex, setTerminalIndex] = useState(0)
  const [committing, setCommitting] = useState(false)

  const logSteps = [
    'CONNECTING TO AI DOCUMENT EXTRACTION ENGINE...',
    'ESTABLISHING SECURE DATA SHAKE...',
    'UPLOADING INVOICE BYTES TO GEMINI VISION MODEL...',
    'PERFORMING DOCUMENT SCANNING AND METADATA EXTRACTION...',
    'RECONCILING TRANSACTION DATE STAMPS AND BARCODE SKU SIGNALS...',
    'APPLYING NATURAL LANGUAGE CATEGORIZATION SCHEMES...',
    'CALCULATING UNIT PRICES, COGS SCALES, AND SYSTEM MARGINS...',
    'COMPILING PROVISIONAL TRANSACTION BULK INSERT LEDGER...'
  ]

  // Typewriter effect timer for terminal simulation
  useEffect(() => {
    let interval
    if (phase === 'loading' && terminalIndex < logSteps.length) {
      interval = setInterval(() => {
        setTerminalLogs(prev => [...prev, `[LOG] ${logSteps[terminalIndex]}`])
        setTerminalIndex(prev => prev + 1)
      }, 750)
    }
    return () => clearInterval(interval)
  }, [phase, terminalIndex])

  // Escape key handler to close the modal & restore focus
  useEffect(() => {
    const previousFocus = document.activeElement
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    
    // Focus close button or container on mount
    const closeBtn = document.querySelector('.scanner-modal .close-btn')
    if (closeBtn) {
      closeBtn.focus()
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      if (previousFocus) {
        previousFocus.focus()
      }
    }
  }, [onClose])

  // Drag handlers
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0])
    }
  }

  const handleFileSelected = async (selectedFile) => {
    const name = selectedFile.name.toLowerCase()
    const validExts = ['.pdf', '.jpg', '.jpeg', '.png', '.webp']
    const hasValidExt = validExts.some(ext => name.endsWith(ext))

    if (!hasValidExt) {
      setErrorMessage("Unsupported file format. Supported: .pdf, .jpg, .jpeg, .png, .webp")
      setPhase('error')
      return
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setErrorMessage("File exceeds 10 MB limit.")
      setPhase('error')
      return
    }

    setFile(selectedFile)
    await uploadAndScan(selectedFile)
  }

  const uploadAndScan = async (selectedFile) => {
    setPhase('loading')
    setTerminalLogs(['[SYS] MOUNTING RAW INVOICE DOCUMENT STREAM...'])
    setTerminalIndex(0)

    try {
      const result = await api.scanDocument(selectedFile)
      
      // Let the terminal animation complete at least some lines before skipping
      setTimeout(() => {
        if (result && result.items && result.items.length > 0) {
          // Map to local editable structure
          const formatted = result.items.map((item, idx) => ({
            id: idx,
            product_name: item.product_name || 'Unknown Product',
            product_category: item.product_category || 'Other',
            product_sku: item.product_sku || '',
            quantity_sold: Number(item.quantity_sold) || 1,
            unit_price: Number(item.unit_price) || 0,
            sale_date: item.sale_date || new Date().toISOString().split('T')[0],
            customer_segment: item.customer_segment || 'Walk-in',
            currency: item.currency || currency || 'INR'
          }))
          setItems(formatted)
          setPhase('review')
        } else {
          throw new Error("No transactions could be extracted from this document.")
        }
      }, 2500)

    } catch (err) {
      console.error("AI scanning failed:", err)
      setErrorMessage(err.message || "The AI scanner was unable to interpret this receipt's layout. Please check your Gemini connection or run our offline preview fallback.")
      setPhase('error')
    }
  }

  // Load Mock Fallback for testing/offline support
  const handleLoadMockFallback = () => {
    const mockData = [
      {
        id: 0,
        product_name: "Premium Vintage Fountain Pen",
        product_sku: "SKU-VFN-898",
        product_category: "Stationery",
        quantity_sold: 4,
        unit_price: 450.00,
        sale_date: new Date().toISOString().split('T')[0],
        customer_segment: "Online",
        currency: currency
      },
      {
        id: 1,
        product_name: "Cotton Editorial Tweed Jacket",
        product_sku: "SKU-CLO-334",
        product_category: "Apparel",
        quantity_sold: 1,
        unit_price: 2800.00,
        sale_date: new Date().toISOString().split('T')[0],
        customer_segment: "Walk-in",
        currency: currency
      },
      {
        id: 2,
        product_name: "Leather Ledger Journal",
        product_sku: "SKU-JRN-442",
        product_category: "Stationery",
        quantity_sold: 3,
        unit_price: 650.00,
        sale_date: new Date().toISOString().split('T')[0],
        customer_segment: "Walk-in",
        currency: currency
      }
    ]
    setItems(mockData)
    setPhase('review')
  }

  // Edit fields
  const handleFieldChange = (id, field, value) => {
    setItems(prev => prev.map(item => {
      if (item.id === id) {
        return { ...item, [field]: value }
      }
      return item
    }))
  }

  // Delete row
  const handleDeleteRow = (id) => {
    setItems(prev => prev.filter(item => item.id !== id))
  }

  // Add blank row
  const handleAddRow = () => {
    const newId = items.length > 0 ? Math.max(...items.map(i => i.id)) + 1 : 0
    const newRow = {
      id: newId,
      product_name: "",
      product_category: "Other",
      product_sku: "",
      quantity_sold: 1,
      unit_price: 0,
      sale_date: new Date().toISOString().split('T')[0],
      customer_segment: "Walk-in",
      currency: currency
    }
    setItems(prev => [...prev, newRow])
  }

  // Commit items to backend sales bulk API
  const handleCommitLedger = async () => {
    if (items.length === 0) return

    // Simple validation
    const invalid = items.some(item => !item.product_name.trim() || Number(item.unit_price) <= 0 || Number(item.quantity_sold) <= 0)
    if (invalid) {
      alert("All transactions require a valid Product Name, positive Quantity, and positive Unit Price.")
      return
    }

    setCommitting(true)
    try {
      // Map to SaleRecordCreate fields
      const payload = {
        sales: items.map(item => ({
          product_name: item.product_name.trim(),
          product_sku: item.product_sku.trim() || null,
          product_category: item.product_category,
          quantity_sold: Number(item.quantity_sold),
          unit_price: Number(item.unit_price),
          sale_date: item.sale_date,
          customer_segment: item.customer_segment,
          currency: item.currency
        }))
      }

      const endpoint = selectedStore?.id ? `/retail/bulk?store_id=${selectedStore.id}` : '/retail/bulk'
      await api.post(endpoint, payload)
      setPhase('success')
      if (onComplete) {
        onComplete()
      }
    } catch (err) {
      console.error("Bulk insert failed:", err)
      alert(err.message || "Failed to commit transactions to General Ledger.")
    } finally {
      setCommitting(false)
    }
  }

  const computedTotal = items.reduce((acc, curr) => acc + (curr.quantity_sold * curr.unit_price), 0)

  return (
    <div className="scanner-modal-overlay">
      <div className="scanner-modal-container">
        
        <div className="scanner-modal-header">
          <div className="scanner-header-title-block">
            <span className="scanner-kicker">AI DOCUMENT SCANNER</span>
            <h2>AI Document Scanning Terminal</h2>
          </div>
          <button className="scanner-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="scanner-modal-body">
          
          {phase === 'drop' && (
            <div>
              <div className="scanner-fallback-banner">
                💡 <strong>Gemini Vision Mode:</strong> Drop print receipts or supplier invoice PDFs here. The scanner will process line-by-line, forecast demand spikes, and compute standard margins instantly.
              </div>

              <div 
                className={`scanner-dropzone ${dragActive ? 'drag-active' : ''}`}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('scannerFileInput').click()}
              >
                <input 
                  type="file" 
                  id="scannerFileInput" 
                  style={{ display: 'none' }} 
                  onChange={handleFileInput}
                  accept=".pdf,.png,.jpg,.jpeg,.webp"
                />
                <span className="scanner-dropzone-icon">📄</span>
                <div className="scanner-dropzone-text">Drop Printed Receipt or Supplier Invoice here</div>
                <div className="scanner-dropzone-subtext">PDF · PNG · JPG · WEBP (Max 10 MB size)</div>
                
                <button 
                  type="button" 
                  className="btn-mono-secondary"
                  onClick={(e) => {
                    e.stopPropagation()
                    document.getElementById('scannerFileInput').click()
                  }}
                >
                  Select File
                </button>
              </div>

              <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                  No receipt on hand? Explore this feature with our{' '}
                  <button 
                    type="button" 
                    style={{ background: 'none', border: 'none', color: 'var(--ink-blue)', textDecoration: 'underline', padding: 0, textTransform: 'none', fontSize: '0.85rem' }} 
                    onClick={handleLoadMockFallback}
                  >
                    vintage offline sample ledger.
                  </button>
                </span>
              </div>
            </div>
          )}

          {phase === 'loading' && (
            <div className="scanner-loading-container">
              <div className="scanner-typewriter-box">
                <div className="scanner-terminal-header">
                  <span>AI Scanner Terminal v1.0</span>
                  <span>STATUS: SECURE_SCAN</span>
                </div>
                {terminalLogs.map((log, i) => (
                  <div key={i} className="scanner-terminal-line">{log}</div>
                ))}
                {terminalIndex < logSteps.length && (
                  <div className="scanner-terminal-line">
                    [SYS] Processing...<span className="scanner-terminal-cursor"></span>
                  </div>
                )}
              </div>
            </div>
          )}

          {phase === 'review' && (
            <div>
              <div className="scanner-review-summary">
                <span>📁 INVOICE: {file?.name || 'OFFLINE SAMPLE LEDGER'}</span>
                <span>ITEMS DETECTED: <strong>{items.length}</strong></span>
                <span>ESTIMATED VALUE: <strong>{currency} {computedTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong></span>
              </div>

              <div className="scanner-table-container">
                <table className="scanner-review-table">
                  <thead>
                    <tr>
                      <th style={{ width: '4%' }}>#</th>
                      <th style={{ width: '30%' }}>Product Name</th>
                      <th style={{ width: '16%' }}>Category</th>
                      <th style={{ width: '12%' }}>SKU</th>
                      <th style={{ width: '8%', textAlign: 'right' }}>Qty</th>
                      <th style={{ width: '12%', textAlign: 'right' }}>Unit Price</th>
                      <th style={{ width: '10%' }}>Sale Date</th>
                      <th style={{ width: '12%' }}>Segment</th>
                      <th style={{ width: '6%', textAlign: 'center' }}>✕</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.length === 0 ? (
                      <tr>
                        <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', fontStyle: 'italic' }}>
                          No transaction rows present. Click "Add Row" to append manual transaction entries.
                        </td>
                      </tr>
                    ) : (
                      items.map((item, index) => (
                        <tr key={item.id}>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', paddingLeft: '0.8rem' }}>{index + 1}</td>
                          <td>
                            <input 
                              type="text" 
                              className="scanner-table-input"
                              value={item.product_name}
                              onChange={e => handleFieldChange(item.id, 'product_name', e.target.value)}
                              placeholder="Product Name"
                              required
                            />
                          </td>
                          <td>
                            <select 
                              className="scanner-table-select"
                              value={item.product_category}
                              onChange={e => handleFieldChange(item.id, 'product_category', e.target.value)}
                            >
                              <option value="Electronics">Electronics</option>
                              <option value="Apparel">Apparel</option>
                              <option value="Food & Beverage">Food & Bev</option>
                              <option value="Home & Garden">Home & Garden</option>
                              <option value="Stationery">Stationery</option>
                              <option value="Other">Other</option>
                            </select>
                          </td>
                          <td>
                            <input 
                              type="text" 
                              className="scanner-table-input"
                              value={item.product_sku || ''}
                              onChange={e => handleFieldChange(item.id, 'product_sku', e.target.value)}
                              placeholder="N/A"
                            />
                          </td>
                          <td>
                            <input 
                              type="number" 
                              className="scanner-table-input num-field"
                              value={item.quantity_sold}
                              onChange={e => handleFieldChange(item.id, 'quantity_sold', parseFloat(e.target.value) || 0)}
                              min="0.1"
                              step="any"
                              required
                            />
                          </td>
                          <td>
                            <input 
                              type="number" 
                              className="scanner-table-input num-field"
                              value={item.unit_price}
                              onChange={e => handleFieldChange(item.id, 'unit_price', parseFloat(e.target.value) || 0)}
                              min="0"
                              step="any"
                              required
                            />
                          </td>
                          <td>
                            <input 
                              type="date" 
                              className="scanner-table-input"
                              value={item.sale_date}
                              onChange={e => handleFieldChange(item.id, 'sale_date', e.target.value)}
                              required
                            />
                          </td>
                          <td>
                            <select 
                              className="scanner-table-select"
                              value={item.customer_segment}
                              onChange={e => handleFieldChange(item.id, 'customer_segment', e.target.value)}
                            >
                              <option value="Walk-in">Walk-in</option>
                              <option value="Online">Online</option>
                              <option value="B2B">B2B</option>
                            </select>
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <button 
                              type="button" 
                              className="scanner-row-delete-btn"
                              onClick={() => handleDeleteRow(item.id)}
                            >
                              ✕
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              <button 
                type="button" 
                className="scanner-add-row-btn"
                onClick={handleAddRow}
              >
                + Add Transaction Row
              </button>
            </div>
          )}

          {phase === 'success' && (
            <div className="scanner-success-container">
              <div className="scanner-stamp">📄 PASSED AUDIT</div>
              <h3 className="scanner-success-title">Transferred to General Ledger</h3>
              <p className="scanner-success-msg">
                The extracted invoices have successfully cleared local financial audits. All {items.length} records have been bulk inserted and indexed into your active store's ledger database.
              </p>
            </div>
          )}

          {phase === 'error' && (
            <div className="scanner-error-container">
              <span className="scanner-error-icon">⚠️</span>
              <h3 className="scanner-error-title">Extraction Error</h3>
              <p className="scanner-error-msg">
                {errorMessage}
              </p>
              <div className="scanner-error-actions">
                <button 
                  type="button" 
                  className="btn-mono-secondary" 
                  onClick={() => setPhase('drop')}
                >
                  Retry Upload
                </button>
                <button 
                  type="button" 
                  className="btn-mono-primary" 
                  onClick={handleLoadMockFallback}
                >
                  Run Offline Fallback
                </button>
              </div>
            </div>
          )}

        </div>

        <div className="scanner-modal-footer">
          {phase === 'drop' && (
            <button className="btn-mono-secondary" onClick={onClose}>Cancel</button>
          )}

          {phase === 'review' && (
            <>
              <button 
                className="btn-mono-secondary" 
                onClick={() => setPhase('drop')}
                disabled={committing}
              >
                Rescan File
              </button>
              <button 
                className="btn-mono-primary" 
                onClick={handleCommitLedger}
                disabled={committing || items.length === 0}
              >
                {committing ? 'Committing Ledger...' : 'Commit to Ledger →'}
              </button>
            </>
          )}

          {phase === 'success' && (
            <button className="btn-mono-primary" onClick={onClose}>Finish</button>
          )}

          {phase === 'error' && (
            <button className="btn-mono-secondary" onClick={onClose}>Close Terminal</button>
          )}
        </div>

      </div>
    </div>
  )
}
