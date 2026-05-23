import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileSpreadsheet, Brain, TrendingUp, AlertTriangle } from 'lucide-react';

export default function UserManual() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="user-manual-section" style={{
      border: '4px double var(--ink-black)',
      background: 'var(--bg-paper)',
      padding: '1.2rem',
      marginBottom: '1.5rem',
      boxShadow: '6px 6px 0 rgba(26, 26, 26, 0.05)',
      transition: 'all 0.2s ease'
    }}>
      {/* Header toggle */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          userSelect: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <BookOpen size={20} className="text-red" />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--ink-red)', fontWeight: 700, letterSpacing: '0.12em' }}>
              ✦ Documentation & Specifications ✦
            </span>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontFamily: 'var(--font-display)', fontWeight: 800 }}>
              RetailMind Store Operating Manual & Data Guide
            </h3>
          </div>
        </div>
        <button style={{
          background: 'transparent',
          border: 'none',
          padding: '0.25rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {isOpen && (
        <div style={{
          marginTop: '1.2rem',
          borderTop: '1px dashed rgba(0,0,0,0.15)',
          paddingTop: '1.2rem',
          animation: 'fadeIn 0.3s ease-in-out'
        }}>
          {/* Broadsheet Columns Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.5rem'
          }}>
            {/* Column 1: Spreadsheet specifications */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', borderBottom: '1px solid var(--ink-black)', paddingBottom: '0.3rem' }}>
                <FileSpreadsheet size={16} className="text-blue" />
                <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 700 }}>1. Spreadsheet Upload Spec</span>
              </div>
              <p className="serif italic" style={{ fontSize: '0.85rem', margin: 0 }}>
                To import your sales data, upload a `.csv` or `.xlsx` spreadsheet. The system automatically maps headers using an advanced alias engine.
              </p>
              
              <div style={{
                background: 'var(--bg-tint)',
                padding: '0.6rem',
                border: '1px solid rgba(0,0,0,0.12)',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)'
              }}>
                <strong style={{ color: 'var(--ink-red)' }}>Required Columns:</strong>
                <ul style={{ margin: '0.3rem 0', paddingLeft: '1.2rem' }}>
                  <li><code>product_name</code> (Item description)</li>
                  <li><code>quantity</code> (Units sold - numeric)</li>
                  <li><code>unit_price</code> (Selling price per unit)</li>
                  <li><code>date</code> (Format: YYYY-MM-DD or DD-MM-YYYY)</li>
                </ul>
                <strong style={{ color: 'var(--ink-blue)' }}>Optional Columns:</strong>
                <ul style={{ margin: '0.3rem 0', paddingLeft: '1.2rem' }}>
                  <li><code>sku</code> (Product ID code)</li>
                  <li><code>category</code> (Electronics, Apparel, Grocery...)</li>
                  <li><code>cogs</code> (Cost of goods sold per unit)</li>
                  <li><code>customer_segment</code> (Walk-in, Online, B2B)</li>
                </ul>
              </div>
            </div>

            {/* Column 2: ML & Predictive Forecasts */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', borderBottom: '1px solid var(--ink-black)', paddingBottom: '0.3rem' }}>
                <TrendingUp size={16} className="text-green" />
                <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 700 }}>2. Predictive Forecasts</span>
              </div>
              <p className="serif italic" style={{ fontSize: '0.85rem', margin: 0 }}>
                Our algorithms extract business growth signals from your transaction data to predict future metrics automatically:
              </p>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', lineHeight: '1.5' }}>
                <li>
                  <strong>Holt-Winters Smoothing:</strong> The daily trend graph displays a 14-day statistical projection with seasonal weighting adjustments.
                </li>
                <li>
                  <strong>K-Means Quadrants:</strong> Product catalog groupings:
                  <ul style={{ paddingLeft: '1rem', margin: '0.2rem 0' }}>
                    <li><strong>Stars:</strong> Premium catalog items driving revenue and high profit margins.</li>
                    <li><strong>Hidden Gems:</strong> High-margin products with low transaction volume.</li>
                    <li><strong>Cash Cows:</strong> Low-margin items that draw massive overall sales volume.</li>
                    <li><strong>Dead Weight:</strong> Low-revenue, low-margin products slated for liquidation.</li>
                  </ul>
                </li>
              </ul>
            </div>

            {/* Column 3: AI Advisor & Smart Alerts */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', borderBottom: '1px solid var(--ink-black)', paddingBottom: '0.3rem' }}>
                <Brain size={16} style={{ color: 'var(--ink-yellow)' }} />
                <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 700 }}>3. AI Advisor & Alerts</span>
              </div>
              <p className="serif italic" style={{ fontSize: '0.85rem', margin: 0 }}>
                Secure, state-of-the-art Gemini 2.5 models power your automated retail advisor.
              </p>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', lineHeight: '1.5' }}>
                <li>
                  <strong>AI Advisor Chat:</strong> Tap "Ask Retail Advisor" to ask specific questions about sales patterns, inventory strategies, or cost adjustments.
                </li>
                <li>
                  <strong>Smart Guardrails:</strong> The AI advisor responds exclusively to retail operations queries, shielding your data and keeping audits strictly productive.
                </li>
                <li>
                  <strong>Alert Indicators:</strong>
                  <ul style={{ paddingLeft: '1rem', margin: '0.2rem 0' }}>
                    <li><strong className="text-red">Dead Stock:</strong> Warns when high-velocity items go 30+ days without sales.</li>
                    <li><strong className="text-red">Margin Erosion:</strong> Triggers when promotional pricing eats into target margins.</li>
                  </ul>
                </li>
              </ul>
            </div>
          </div>

          {/* Guidelines Footer */}
          <div style={{
            marginTop: '1.2rem',
            borderTop: '1px solid var(--ink-black)',
            paddingTop: '0.6rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            fontSize: '0.72rem',
            color: 'var(--text-muted)'
          }}>
            <AlertTriangle size={14} className="text-red" />
            <span className="mono">Note: Data is parsed directly inside memory sandbox. No customer details are exposed.</span>
          </div>
        </div>
      )}
    </div>
  );
}
