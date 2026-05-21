import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import { formatMoneyDetailed } from '../services/currency'
import './PortfolioMatrix.css'

const PortfolioMatrix = ({ period, dateFrom, dateTo, storeId, currency, onQuadrantSelect }) => {
  const [data, setData] = useState({ clusters: [], centroids: {} })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hoveredProduct, setHoveredProduct] = useState(null)
  const [activeQuadrant, setActiveQuadrant] = useState(null)

  useEffect(() => {
    let active = true
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await api.getPortfolioClusters(period, dateFrom, dateTo, storeId)
        if (active) {
          setData(res || { clusters: [], centroids: {} })
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Failed to load portfolio clusters')
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }
    fetchData()
    return () => {
      active = false
    }
  }, [period, dateFrom, dateTo, storeId])

  if (error) {
    return (
      <div className="portfolio-matrix-container error-box">
        <p className="mono text-red">⚠️ Error loading K-Means portfolio clusters</p>
        <p className="monospace-text">{error}</p>
      </div>
    )
  }

  // Dimension mapping: SVG coordinates
  // SVG size is 400x400.
  // Center is at 200, 200.
  // Standard scaled coordinates are clamped between [-2.5, 2.5]
  const width = 400
  const height = 400
  const padding = 45
  
  const toSVGCoords = (x, y) => {
    // Map -2.5..2.5 to padding..width-padding
    const scaleX = (width - 2 * padding) / 5
    const scaleY = (height - 2 * padding) / 5
    const cx = width / 2 + x * scaleX
    const cy = height / 2 - y * scaleY // inverted Y axis for SVG
    return { cx, cy }
  }

  // Count quadrant distribution
  const quadCounts = {
    'Stars': 0,
    'Hidden Gems': 0,
    'Cash Cows': 0,
    'Dead Weight': 0
  }
  
  if (data?.clusters) {
    data.clusters.forEach(p => {
      if (quadCounts[p.quadrant] !== undefined) {
        quadCounts[p.quadrant]++
      }
    })
  }

  const handleQuadrantClick = (quadName) => {
    setActiveQuadrant(quadName)
    if (!data?.clusters) return
    const matchingProducts = data.clusters
      .filter(p => p.quadrant === quadName)
      .map(p => p.product_name)
    
    if (onQuadrantSelect) {
      onQuadrantSelect(matchingProducts, quadName)
    }
  }

  return (
    <div className="portfolio-matrix-section">
      <div className="section-kicker">
        <span className="kicker-label">Product Portfolio Quadrants (K-Means Clustering)</span>
        <div className="kicker-line" />
      </div>

      <div className="portfolio-matrix-layout">
        <div className="portfolio-matrix-description">
          <p className="serif italic" style={{ fontSize: '0.95rem', margin: '0 0 1.2rem', lineHeight: '1.5' }}>
            Machine learning groups your entire catalog into four performance quadrants based on standard-scaled Revenue, Gross Margin, Velocity, and Recency of sales.
          </p>
          <div className="quadrant-roster mono">
            <div className={`roster-item stars ${activeQuadrant === 'Stars' ? 'active' : ''}`} onClick={() => handleQuadrantClick('Stars')}>
              <span className="roster-tag">🌟 Stars ({quadCounts['Stars']})</span>
              <span className="roster-desc">High Revenue, High Margin</span>
            </div>
            <div className={`roster-item gems ${activeQuadrant === 'Hidden Gems' ? 'active' : ''}`} onClick={() => handleQuadrantClick('Hidden Gems')}>
              <span className="roster-tag">💎 Hidden Gems ({quadCounts['Hidden Gems']})</span>
              <span className="roster-desc">Low Revenue, High Margin</span>
            </div>
            <div className={`roster-item cows ${activeQuadrant === 'Cash Cows' ? 'active' : ''}`} onClick={() => handleQuadrantClick('Cash Cows')}>
              <span className="roster-tag">🐄 Cash Cows ({quadCounts['Cash Cows']})</span>
              <span className="roster-desc">High Revenue, Low Margin</span>
            </div>
            <div className={`roster-item dead ${activeQuadrant === 'Dead Weight' ? 'active' : ''}`} onClick={() => handleQuadrantClick('Dead Weight')}>
              <span className="roster-tag">🪨 Dead Weight ({quadCounts['Dead Weight']})</span>
              <span className="roster-desc">Low Revenue, Low Margin</span>
            </div>
          </div>
          <p className="mono" style={{ fontSize: '0.72rem', marginTop: '1rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            💡 Click on any quadrant title or node to inspect matched products in the Sales Ledger.
          </p>
        </div>

        <div className="portfolio-matrix-svg-wrap">
          {loading ? (
            <div className="portfolio-matrix-loading">
              <span className="mono">Running K-Means Portfolio Clustering...</span>
            </div>
          ) : (
            <div className="svg-container">
              <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="portfolio-matrix-svg">
                {/* Quadrant backgrounds */}
                <rect x="0" y="0" width="200" height="200" className="quad-bg gems-bg" onClick={() => handleQuadrantClick('Hidden Gems')} />
                <rect x="200" y="0" width="200" height="200" className="quad-bg stars-bg" onClick={() => handleQuadrantClick('Stars')} />
                <rect x="0" y="200" width="200" height="200" className="quad-bg dead-bg" onClick={() => handleQuadrantClick('Dead Weight')} />
                <rect x="200" y="200" width="200" height="200" className="quad-bg cows-bg" onClick={() => handleQuadrantClick('Cash Cows')} />

                {/* Double-ruled horizontal and vertical axis grid lines */}
                {/* Horizontal double line */}
                <line x1="0" y1="198" x2="400" y2="198" stroke="var(--ink-black)" strokeWidth="1" />
                <line x1="0" y1="202" x2="400" y2="202" stroke="var(--ink-black)" strokeWidth="1" />
                
                {/* Vertical double line */}
                <line x1="198" y1="0" x2="198" y2="400" stroke="var(--ink-black)" strokeWidth="1" />
                <line x1="202" y1="0" x2="202" y2="400" stroke="var(--ink-black)" strokeWidth="1" />

                {/* Outer frame border */}
                <rect x="0" y="0" width={width} height={height} fill="none" stroke="var(--ink-black)" strokeWidth="4" />

                {/* Quadrant Text Labels */}
                <text x="15" y="25" className="quad-label mono">💎 HIDDEN GEMS</text>
                <text x="385" y="25" className="quad-label mono text-right" textAnchor="end">🌟 STARS</text>
                <text x="15" y="385" className="quad-label mono">🪨 DEAD WEIGHT</text>
                <text x="385" y="385" className="quad-label mono text-right" textAnchor="end">🐄 CASH COWS</text>

                {/* Axis labels */}
                <text x="370" y="190" className="axis-label mono" textAnchor="end">REVENUE →</text>
                <text x="30" y="190" className="axis-label mono">← REVENUE</text>
                <text x="210" y="30" className="axis-label mono" style={{ transform: 'rotate(90deg)', transformOrigin: '210px 30px' }}>MARGIN % →</text>
                <text x="210" y="370" className="axis-label mono" style={{ transform: 'rotate(-90deg)', transformOrigin: '210px 370px' }}>← MARGIN %</text>

                {/* Product nodes */}
                {data?.clusters && data.clusters.map((p, idx) => {
                  const { cx, cy } = toSVGCoords(p.coordinates.x, p.coordinates.y)
                  const isHovered = hoveredProduct?.product_name === p.product_name
                  return (
                    <g key={idx} className="product-node-group">
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isHovered ? 8 : 6}
                        className={`product-node-circle ${p.quadrant.toLowerCase().replace(' ', '-')}`}
                        onMouseEnter={() => setHoveredProduct(p)}
                        onMouseLeave={() => setHoveredProduct(null)}
                        onClick={() => {
                          if (onQuadrantSelect) {
                            onQuadrantSelect([p.product_name], p.quadrant)
                          }
                        }}
                      />
                      {/* Crosshair indicator on hover */}
                      {isHovered && (
                        <>
                          <line x1={cx} y1={0} x2={cx} y2={400} stroke="rgba(0,0,0,0.15)" strokeWidth="1" strokeDasharray="2,2" pointerEvents="none" />
                          <line x1={0} y1={cy} x2={400} y2={cy} stroke="rgba(0,0,0,0.15)" strokeWidth="1" strokeDasharray="2,2" pointerEvents="none" />
                        </>
                      )}
                    </g>
                  )
                })}
              </svg>

              {/* Courier typewriter tooltip */}
              {hoveredProduct && (
                <div className="telex-tooltip monospace-text animate-scale">
                  <div className="tooltip-header red-stamp telex-stamp-badge">
                    {hoveredProduct.quadrant}
                  </div>
                  <div className="tooltip-title">{hoveredProduct.product_name}</div>
                  <div className="tooltip-divider" />
                  <div className="tooltip-row">
                    <span>Revenue:</span>
                    <strong>{formatMoneyDetailed(hoveredProduct.metrics.revenue, currency)}</strong>
                  </div>
                  <div className="tooltip-row">
                    <span>Margin:</span>
                    <strong style={{ color: hoveredProduct.metrics.margin_pct >= 25 ? 'var(--ink-green)' : 'var(--ink-red)' }}>
                      {hoveredProduct.metrics.margin_pct.toFixed(1)}%
                    </strong>
                  </div>
                  <div className="tooltip-row">
                    <span>Qty:</span>
                    <strong>{hoveredProduct.metrics.qty} units</strong>
                  </div>
                  <div className="tooltip-row">
                    <span>Recency:</span>
                    <strong>{hoveredProduct.metrics.recency} days ago</strong>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PortfolioMatrix
