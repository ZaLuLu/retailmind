import { useState } from 'react'
import { formatMoneyCompact } from '../services/currency'
import './TelexBriefing.css'

const TelexBriefing = ({ summary = {}, onClose, currency = 'INR' }) => {
  const {
    total_revenue = 0,
    total_cogs = 0,
    gross_profit = 0,
    overall_margin_pct = 0,
    mom_revenue_change_pct = 0,
    num_sales = 0,
    demand_signals = [],
    dead_stock_alerts = [],
    margin_erosion_alerts = [],
    ai_insight = ''
  } = summary

  const [todayStr] = useState(() => new Date().toISOString().replace('T', ' ').substring(0, 19).toUpperCase() + ' UTC')
  const [messageId] = useState(() => `TX-${Math.floor(100000 + Math.random() * 900000)}`)

  // Format plaintext for download
  const generatePlaintext = () => {
    const divider = '=================================================='
    const thinDivider = '--------------------------------------------------'
    
    let text = `
${divider}
             RETAILMIND TELEGRAPHY SERVICES
         TELEPRINTER DISPATCH // CONFIDENTIAL
${divider}

MSG ID:   ${messageId}
ROUTING:  RM-CORP-SYS-01
DATE:     ${todayStr}
PRIORITY: URGENT / HIGH

TO: RETAIL STORE MANAGEMENT
FM: RETAILMIND CORE ANALYTICS SYSTEM

SUBJECT: MONTH-TO-DATE EXECUTIVE DISPATCH

${thinDivider}
SECTION 01 - FINANCIAL TELEMETRY
${thinDivider}
* REVENUE:      ${formatMoneyCompact(total_revenue, currency).toUpperCase()}
* COGS:         ${formatMoneyCompact(total_cogs, currency).toUpperCase()}
* GROSS PROFIT: ${formatMoneyCompact(gross_profit, currency).toUpperCase()}
* MARGIN:       ${overall_margin_pct.toFixed(2)}%
* VOLUME:       ${num_sales} TRANSACTIONS
* MOM CHANGE:   ${mom_revenue_change_pct >= 0 ? '+' : ''}${mom_revenue_change_pct.toFixed(2)}%

${thinDivider}
SECTION 02 - OPERATIONAL ANOMALIES
${thinDivider}
${demand_signals.length === 0 ? 'NO DEMAND SPIKES DETECTED.' : demand_signals.map((s, idx) => `[SPIKE #${idx+1}] ${s.product_name.toUpperCase()}: ${s.message.toUpperCase()}`).join('\n')}

${dead_stock_alerts.length === 0 ? 'NO DEAD STOCK ALERTS.' : dead_stock_alerts.map((s, idx) => `[DEAD STOCK #${idx+1}] ${s.product_name.toUpperCase()}: ${s.message.toUpperCase()}`).join('\n')}

${margin_erosion_alerts.length === 0 ? 'NO MARGIN EROSION DETECTED.' : margin_erosion_alerts.map((s, idx) => `[MARGIN EROSION #${idx+1}] ${s.product_name.toUpperCase()}: ${s.message.toUpperCase()}`).join('\n')}

${thinDivider}
SECTION 03 - AI SYSTEM BRIEFING
${thinDivider}
${(ai_insight || 'AI ANALYSIS UNAVAILABLE. VERIFY API CONFIGURATION.').toUpperCase()}

${divider}
            [STOP] END OF MESSAGE // RM-TELECON [STOP]
${divider}
`.trim()
    return text
  }

  const handleDownload = () => {
    const text = generatePlaintext()
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `Telex_Briefing_${messageId}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="telex-overlay" onClick={onClose}>
      <div className="telex-modal animate-scale" onClick={(e) => e.stopPropagation()}>
        <div className="telex-modal-header">
          <h3 className="telex-modal-title mono">📰 SYSTEM TELETYPE BRIEFING</h3>
          <button className="telex-close-btn mono" onClick={onClose}>CLOSE [ESC]</button>
        </div>

        <div className="telex-paper-container">
          <div className="telex-paper" id="telex-print-area">
            {/* Header info */}
            <div className="telex-banner mono">
              ****************************************************<br />
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;RETAILMIND TELEGRAPHY SERVICES<br />
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TELEPRINTER DISPATCH // CONFIDENTIAL<br />
              ****************************************************
            </div>

            <div className="telex-meta mono">
              <div><strong>MSG ID:</strong> {messageId}</div>
              <div><strong>ROUTING:</strong> RM-CORP-SYS-01</div>
              <div><strong>DATE:</strong> {todayStr}</div>
              <div><strong>PRIORITY:</strong> URGENT / HIGH</div>
              <br />
              <div><strong>TO:</strong> RETAIL STORE MANAGEMENT</div>
              <div><strong>FM:</strong> RETAILMIND CORE ANALYTICS SYSTEM</div>
              <br />
              <div><strong>SUBJECT:</strong> MONTH-TO-DATE EXECUTIVE DISPATCH</div>
            </div>

            <div className="telex-divider mono">----------------------------------------------------</div>

            <div className="telex-section mono">
              <div className="telex-section-title">SECTION 01 - FINANCIAL TELEMETRY</div>
              <div className="telex-section-content">
                <div className="telex-row"><span className="telex-lbl">REVENUE:</span><span className="telex-val">{formatMoneyCompact(total_revenue, currency).toUpperCase()}</span></div>
                <div className="telex-row"><span className="telex-lbl">COGS:</span><span className="telex-val">{formatMoneyCompact(total_cogs, currency).toUpperCase()}</span></div>
                <div className="telex-row"><span className="telex-lbl">GROSS PROFIT:</span><span className="telex-val">{formatMoneyCompact(gross_profit, currency).toUpperCase()}</span></div>
                <div className="telex-row"><span className="telex-lbl">MARGIN:</span><span className="telex-val">{overall_margin_pct.toFixed(2)}%</span></div>
                <div className="telex-row"><span className="telex-lbl">VOLUME:</span><span className="telex-val">{num_sales} TRANSACTIONS</span></div>
                <div className="telex-row"><span className="telex-lbl">MOM CHANGE:</span><span className="telex-val">{mom_revenue_change_pct >= 0 ? '+' : ''}{mom_revenue_change_pct.toFixed(2)}%</span></div>
              </div>
            </div>

            <div className="telex-divider mono">----------------------------------------------------</div>

            <div className="telex-section mono">
              <div className="telex-section-title">SECTION 02 - OPERATIONAL ANOMALIES</div>
              <div className="telex-section-content">
                {demand_signals.length === 0 && <div>NO DEMAND SPIKES DETECTED.</div>}
                {demand_signals.map((s, idx) => (
                  <div key={`ds-${idx}`} className="telex-bullet">
                    [SPIKE #{idx+1}] {s.product_name.toUpperCase()}: {s.message.toUpperCase()}
                  </div>
                ))}

                {dead_stock_alerts.length === 0 && <div style={{ marginTop: '8px' }}>NO DEAD STOCK ALERTS.</div>}
                {dead_stock_alerts.map((s, idx) => (
                  <div key={`ds-dead-${idx}`} className="telex-bullet">
                    [DEAD STOCK #{idx+1}] {s.product_name.toUpperCase()}: {s.message.toUpperCase()}
                  </div>
                ))}

                {margin_erosion_alerts.length === 0 && <div style={{ marginTop: '8px' }}>NO MARGIN EROSION DETECTED.</div>}
                {margin_erosion_alerts.map((s, idx) => (
                  <div key={`ds-margin-${idx}`} className="telex-bullet">
                    [MARGIN EROSION #{idx+1}] {s.product_name.toUpperCase()}: {s.message.toUpperCase()}
                  </div>
                ))}
              </div>
            </div>

            <div className="telex-divider mono">----------------------------------------------------</div>

            <div className="telex-section mono">
              <div className="telex-section-title">SECTION 03 - AI SYSTEM BRIEFING</div>
              <div className="telex-section-content telex-ai-text">
                {ai_insight ? ai_insight.toUpperCase() : 'AI ANALYSIS UNAVAILABLE. VERIFY API CONFIGURATION.'}
              </div>
            </div>

            <div className="telex-divider mono">----------------------------------------------------</div>

            <div className="telex-footer mono">
              [STOP] END OF MESSAGE // RM-TELECON [STOP]
            </div>
          </div>
        </div>

        <div className="telex-actions">
          <button className="telex-action-btn print mono" onClick={handlePrint}>🖨️ PRINT TELEGRAM (PDF)</button>
          <button className="telex-action-btn download mono" onClick={handleDownload}>💾 DOWNLOAD TELEX (.TXT)</button>
        </div>
      </div>
    </div>
  )
}

export default TelexBriefing
