// DemoResetUploadModal.jsx
import React, { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import './DemoResetUploadModal.css'

export default function DemoResetUploadModal({ onClose, onComplete }) {
  const [phase, setPhase] = useState('confirm') // 'confirm' | 'drop' | 'preview' | 'progress' | 'success' | 'error'
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [previewHeaders, setPreviewHeaders] = useState([])
  const [previewRows, setPreviewRows] = useState([])
  const [errorMessage, setErrorMessage] = useState('')

  // SSE Progress States
  const [progressPercent, setProgressPercent] = useState(0)
  const [progressMsg, setProgressMsg] = useState('Enqueuing recomputation task...')
  const [currentStep, setCurrentStep] = useState('import') // 'import' | 'forecast' | 'clusters' | 'alerts' | 'segments' | 'done'
  
  const eventSourceRef = useRef(null)

  useEffect(() => {
    // Cleanup EventSource on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

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

  const handleFileSelected = (selectedFile) => {
    const name = selectedFile.name.toLowerCase()
    if (!name.endsWith('.csv') && !name.endsWith('.xlsx') && !name.endsWith('.xls')) {
      setErrorMessage("Only .csv, .xlsx, or .xls spreadsheets are accepted.")
      setPhase('error')
      return
    }

    setFile(selectedFile)
    
    // Parse preview if CSV
    if (name.endsWith('.csv')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target.result
        const lines = text.split('\n').filter(l => l.trim())
        if (lines.length > 0) {
          const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''))
          const rows = []
          for (let i = 1; i < Math.min(lines.length, 6); i++) {
            const cols = lines[i].split(',').map(c => c.trim().replace(/^["']|["']$/g, ''))
            const r = {}
            headers.forEach((h, idx) => {
              r[h] = cols[idx] || ''
            })
            rows.push(r)
          }
          setPreviewHeaders(headers)
          setPreviewRows(rows)
          setPhase('preview')
        }
      }
      reader.readAsText(selectedFile)
    } else {
      // Excel files: skip client-side preview, go straight to upload preview state
      setPreviewHeaders(['Excel Sheet'])
      setPreviewRows([{ 'File Name': selectedFile.name, 'Size': `${(selectedFile.size / 1024).toFixed(1)} KB` }])
      setPhase('preview')
    }
  }

  const handleStartAnalysis = async () => {
    if (!file) return

    setPhase('progress')
    setProgressPercent(10)
    setProgressMsg('Uploading file and clearing database...')

    try {
      // 1. Submit file to trigger background job
      const res = await api.demoResetAndUpload(file)
      const jobId = res.job_id

      if (!jobId) {
        throw new Error("Missing job_id in upload response")
      }

      // 2. Connect to Server-Sent Events stream for real-time progress
      setProgressPercent(20)
      setProgressMsg('Spawning background intelligence pipeline...')

      const eventSource = api.demoProgress(jobId)
      eventSourceRef.current = eventSource

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setProgressPercent(data.percent)
          setProgressMsg(data.message)
          setCurrentStep(data.step)

          if (data.step === 'done') {
            eventSource.close()
            onComplete() // refresh main view
            setPhase('success')
          } else if (data.step === 'error' || data.step === 'timeout') {
            eventSource.close()
            setErrorMessage(data.message || 'Pipeline failed.')
            setPhase('error')
          }
        } catch (err) {
          console.error("Failed to parse SSE event data:", err)
        }
      }

      eventSource.onerror = (err) => {
        console.error("SSE Connection Error:", err)
        eventSource.close()
        // If SSE connection disconnects, check if done or assume failure
        setErrorMessage("Lost connection to analysis pipeline.")
        setPhase('error')
      }

    } catch (err) {
      console.error("Upload failed:", err)
      setErrorMessage(err.message || 'Failed to replace demo data.')
      setPhase('error')
    }
  }

  const steps = [
    { id: 'import', label: 'Import & Validate Data' },
    { id: 'forecast', label: 'Holt-Winters Demand Forecast' },
    { id: 'clusters', label: 'K-Means Portfolio Matrix' },
    { id: 'alerts', label: 'Severity Smart Alerts' },
    { id: 'segments', label: 'Customer Segmentation' },
  ]

  const getStepClass = (stepId, index) => {
    const activeIndex = steps.findIndex(s => s.id === currentStep)
    if (currentStep === 'done') return 'completed'
    if (currentStep === stepId) return 'active'
    if (activeIndex > index) return 'completed'
    return ''
  }

  return (
    <div className="demo-modal-overlay">
      <div className="demo-modal-container">
        
        <div className="demo-modal-header">
          <h2>Replace Demo Dataset</h2>
          <button className="demo-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="demo-modal-body">
          
          {phase === 'confirm' && (
            <div>
              <div className="warning-box">
                <div className="warning-title">
                  ⚠️ WARNING: Destructive Action
                </div>
                <div className="warning-desc">
                  This will clear the current 90-day seeded demo database. Any custom data you previously uploaded will be overwritten.
                </div>
              </div>
              <p style={{ lineHeight: '1.6', fontSize: '0.95rem' }}>
                You are about to upload your own transaction ledger to experience <strong>RetailMind</strong> fully with your own business metrics.
              </p>
              <h3 style={{ margin: '24px 0 12px 0', fontSize: '1rem', fontFamily: 'var(--font-display)' }}>What will happen:</h3>
              <ul style={{ paddingLeft: '20px', lineHeight: '1.8', fontSize: '0.9rem', color: '#475569' }}>
                <li>Your entire daily sales ledger will be imported (up to 50,000 rows).</li>
                <li><strong>Triple Exponential Smoothing (Holt-Winters)</strong> forecasting will predict unit demand.</li>
                <li>An unsupervised <strong>K-Means</strong> algorithm will cluster your product portfolio.</li>
                <li>A smart agent will evaluate dead stock, margin erosion, and demand spikes.</li>
              </ul>
            </div>
          )}

          {phase === 'drop' && (
            <div>
              <div 
                className={`file-drop-area ${dragActive ? 'drag-active' : ''}`}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('fileInput').click()}
              >
                <input 
                  type="file" 
                  id="fileInput" 
                  style={{ display: 'none' }} 
                  onChange={handleFileInput}
                  accept=".csv,.xlsx,.xls"
                />
                <span className="file-drop-icon">📊</span>
                <div className="file-drop-text">Drag & drop your spreadsheet here</div>
                <div className="file-drop-subtext">Supports CSV or Excel (.xlsx, .xls) up to 10MB</div>
                
                <a 
                  href={api.getTemplateCsvUrl()} 
                  className="template-download-link"
                  onClick={(e) => e.stopPropagation()}
                >
                  Download template CSV
                </a>
              </div>
            </div>
          )}

          {phase === 'preview' && (
            <div>
              <p style={{ fontSize: '0.9rem', marginBottom: '16px' }}>
                <strong>File selected:</strong> {file?.name} ({(file?.size / 1024).toFixed(1)} KB)
              </p>
              <div className="preview-container">
                <div className="preview-title">
                  <span>Normalised Data Preview (First 5 Rows)</span>
                  <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>Check columns align correctly</span>
                </div>
                <div className="preview-table-wrapper">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        {previewHeaders.map((h, i) => <th key={i}>{h}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((row, rIdx) => (
                        <tr key={rIdx}>
                          {previewHeaders.map((h, cIdx) => <td key={cIdx}>{row[h]}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                If columns look misaligned or blank, check that your spreadsheet matches our template format.
              </p>
            </div>
          )}

          {phase === 'progress' && (
            <div className="progress-overlay-container">
              <div className="progress-spinner-wrapper">
                <div className="progress-spinner-bg"></div>
                <div className="progress-spinner-active"></div>
                <div className="progress-percentage">{progressPercent}%</div>
              </div>

              <div className="progress-step-title">
                {currentStep === 'import' && 'Parsing & Importing Ledger...'}
                {currentStep === 'forecast' && 'Running Holt-Winters demand smoothing...'}
                {currentStep === 'clusters' && 'Fitting K-Means portfolio clusters...'}
                {currentStep === 'alerts' && 'Evaluating severity smart alerts...'}
                {currentStep === 'segments' && 'Performing customer segments split...'}
              </div>
              <div className="progress-message">{progressMsg}</div>

              <div className="pipeline-checklist">
                {steps.map((s, idx) => (
                  <div key={s.id} className={`pipeline-check-item ${getStepClass(s.id, idx)}`}>
                    <div className="pipeline-check-icon">
                      {getStepClass(s.id, idx) === 'completed' ? '✓' : idx + 1}
                    </div>
                    <span>{s.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {phase === 'success' && (
            <div className="success-container">
              <div className="success-badge">✓</div>
              <div className="success-title">Intelligence Briefing Built!</div>
              <div className="success-desc">
                Your custom transaction ledger was imported and all scikit-learn/statsmodels models compiled successfully. 
              </div>
            </div>
          )}

          {phase === 'error' && (
            <div style={{ textAlign: 'center', padding: '32px 0' }}>
              <span style={{ fontSize: '3rem', display: 'inline-block', marginBottom: '16px' }}>❌</span>
              <h3 style={{ color: '#ef4444', fontSize: '1.25rem', marginBottom: '12px' }}>Analysis Failed</h3>
              <p style={{ fontSize: '0.95rem', color: '#475569', lineHeight: '1.6', marginBottom: '24px' }}>
                {errorMessage}
              </p>
              <button className="btn-secondary" onClick={() => setPhase('drop')}>
                Try Another File
              </button>
            </div>
          )}

        </div>

        <div className="demo-modal-footer">
          {phase === 'confirm' && (
            <>
              <button className="btn-secondary" onClick={onClose}>Cancel</button>
              <button className="btn-primary" onClick={() => setPhase('drop')}>I Understand, Proceed</button>
            </>
          )}

          {phase === 'drop' && (
            <button className="btn-secondary" onClick={() => setPhase('confirm')}>Back</button>
          )}

          {phase === 'preview' && (
            <>
              <button className="btn-secondary" onClick={() => setPhase('drop')}>Change File</button>
              <button className="btn-primary" onClick={handleStartAnalysis}>Start Analysis</button>
            </>
          )}

          {phase === 'success' && (
            <button className="btn-primary" onClick={onClose}>Enter Dashboard</button>
          )}

          {phase === 'error' && (
            <button className="btn-secondary" onClick={onClose}>Close</button>
          )}
        </div>

      </div>
    </div>
  )
}
