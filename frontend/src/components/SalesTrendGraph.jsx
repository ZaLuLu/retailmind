import React, { useState, useMemo } from 'react'
import { formatMoneyCompact, formatMoneyDetailed, convertMoney } from '../services/currency'

export default function SalesTrendGraph({ sales = [], categoryBreakdown = [], currency = 'INR' }) {
  const [activeTab, setActiveTab] = useState('trend') // 'trend' | 'comparison'
  const [hoveredPoint, setHoveredPoint] = useState(null) // { x, y, label, val1, val2 } for tooltip

  // ── Tab 1: Daily Revenue Trend Data ──────────────────────────────────────
  const trendData = useMemo(() => {
    if (!sales || sales.length === 0) return []

    // Group by sale_date
    const dailyMap = {}
    sales.forEach(s => {
      if (!s.sale_date) return
      // Parse out just YYYY-MM-DD or readable date
      const dateStr = s.sale_date.substring(0, 10)
      if (!dailyMap[dateStr]) {
        dailyMap[dateStr] = 0
      }
      dailyMap[dateStr] += s.total_revenue || 0
    })

    // Sort chronologically and grab last 15 days of activity
    const sortedDates = Object.keys(dailyMap).sort()
    const last15 = sortedDates.slice(-15)

    return last15.map(d => {
      // Format to short date e.g. "May 12"
      let displayDate = d
      try {
        const parts = d.split('-')
        if (parts.length === 3) {
          const dateObj = new Date(parts[0], parts[1] - 1, parts[2])
          displayDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        }
      } catch (e) {}

      return {
        rawDate: d,
        date: displayDate,
        revenue: dailyMap[d]
      }
    })
  }, [sales])

  // ── Tab 2: Category Revenue vs COGS Comparison Data ──────────────────────
  const comparisonData = useMemo(() => {
    if (!categoryBreakdown || categoryBreakdown.length === 0) {
      // If summary category breakdown is empty, build from raw sales
      const catMap = {}
      sales.forEach(s => {
        const cat = s.product_category || 'Other'
        if (!catMap[cat]) {
          catMap[cat] = { revenue: 0, cogs: 0 }
        }
        catMap[cat].revenue += s.total_revenue || 0
        catMap[cat].cogs += s.cogs || 0
      })
      return Object.keys(catMap).map(cat => ({
        category: cat,
        revenue: catMap[cat].revenue,
        cogs: catMap[cat].cogs
      }))
    }

    // Otherwise use passed summary category breakdown (we can aggregate COGS from sales if needed)
    const rawCogsMap = {}
    sales.forEach(s => {
      const cat = s.product_category || 'Other'
      if (!rawCogsMap[cat]) rawCogsMap[cat] = 0
      rawCogsMap[cat] += s.cogs || 0
    })

    return categoryBreakdown.map(cat => ({
      category: cat.category,
      revenue: cat.revenue,
      cogs: rawCogsMap[cat.category] || (cat.revenue * 0.6) // Fallback if no matching cogs
    }))
  }, [categoryBreakdown, sales])

  // ── SVG Constants & Scaling for Line Chart ───────────────────────────────
  const svgWidth = 700
  const svgHeight = 240
  const paddingLeft = 60
  const paddingRight = 30
  const paddingTop = 20
  const paddingBottom = 40

  const maxRevenue = useMemo(() => {
    if (activeTab === 'trend') {
      const maxVal = Math.max(...trendData.map(d => d.revenue), 1000)
      return maxVal * 1.15 // 15% buffer
    } else {
      const allVals = comparisonData.flatMap(d => [d.revenue, d.cogs])
      const maxVal = Math.max(...allVals, 1000)
      return maxVal * 1.15
    }
  }, [trendData, comparisonData, activeTab])

  // ── Render Line Chart ────────────────────────────────────────────────────
  const lineChartContent = useMemo(() => {
    if (activeTab !== 'trend' || trendData.length === 0) return null

    const pointsCount = trendData.length
    const xInterval = (svgWidth - paddingLeft - paddingRight) / Math.max(pointsCount - 1, 1)

    // Generate SVG path coordinate points
    const coords = trendData.map((d, index) => {
      const x = paddingLeft + index * xInterval
      const y = svgHeight - paddingBottom - ((d.revenue / maxRevenue) * (svgHeight - paddingTop - paddingBottom))
      return { x, y, data: d }
    })

    // Build the SVG path string
    let pathString = ''
    coords.forEach((c, index) => {
      if (index === 0) {
        pathString += `M ${c.x} ${c.y}`
      } else {
        pathString += ` L ${c.x} ${c.y}`
      }
    })

    // Closed path string for the subtle broadsheet fill gradient
    const closedPathString = coords.length > 0
      ? `${pathString} L ${coords[coords.length - 1].x} ${svgHeight - paddingBottom} L ${coords[0].x} ${svgHeight - paddingBottom} Z`
      : ''

    return { coords, pathString, closedPathString }
  }, [trendData, maxRevenue, activeTab])

  // ── Render Comparison Bar Chart ──────────────────────────────────────────
  const barChartContent = useMemo(() => {
    if (activeTab !== 'comparison' || comparisonData.length === 0) return null

    const barGroupWidth = (svgWidth - paddingLeft - paddingRight) / comparisonData.length
    const barWidth = Math.max(barGroupWidth * 0.28, 10)
    const gap = 4

    return comparisonData.map((d, index) => {
      const groupCenterX = paddingLeft + index * barGroupWidth + barGroupWidth / 2

      // Revenue Bar
      const revHeight = (d.revenue / maxRevenue) * (svgHeight - paddingTop - paddingBottom)
      const revX = groupCenterX - barWidth - gap / 2
      const revY = svgHeight - paddingBottom - revHeight

      // COGS Bar
      const cogsHeight = (d.cogs / maxRevenue) * (svgHeight - paddingTop - paddingBottom)
      const cogsX = groupCenterX + gap / 2
      const cogsY = svgHeight - paddingBottom - cogsHeight

      return {
        data: d,
        revBar: { x: revX, y: revY, width: barWidth, height: revHeight },
        cogsBar: { x: cogsX, y: cogsY, width: barWidth, height: cogsHeight },
        groupCenterX
      }
    })
  }, [comparisonData, maxRevenue, activeTab])

  return (
    <div className="card newsprint-chart-card" style={{ padding: '1.25rem', marginBottom: '1.5rem', position: 'relative' }}>
      {/* Chart Tabs */}
      <div className="chart-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid rgba(0,0,0,0.12)', paddingBottom: '0.75rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>Intelligence Analytics</span>
          <h4 className="serif" style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800 }}>
            {activeTab === 'trend' ? 'Daily Revenue History (MTD)' : 'Revenue vs Cost Breakdown by Category'}
          </h4>
        </div>
        <div className="tab-group" style={{ display: 'flex', gap: '0.25rem' }}>
          <button
            onClick={() => { setActiveTab('trend'); setHoveredPoint(null) }}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.65rem',
              background: activeTab === 'trend' ? 'var(--ink-black)' : 'transparent',
              color: activeTab === 'trend' ? 'var(--bg-paper)' : 'var(--ink-black)',
              border: '1px solid var(--ink-black)'
            }}
          >
            📈 Sales Trend
          </button>
          <button
            onClick={() => { setActiveTab('comparison'); setHoveredPoint(null) }}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.65rem',
              background: activeTab === 'comparison' ? 'var(--ink-black)' : 'transparent',
              color: activeTab === 'comparison' ? 'var(--bg-paper)' : 'var(--ink-black)',
              border: '1px solid var(--ink-black)'
            }}
          >
            📊 Cost Comparison
          </button>
        </div>
      </div>

      {/* SVG Graphics Container */}
      <div className="svg-container" style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          width="100%"
          height="100%"
          style={{ display: 'block', background: 'transparent' }}
          onMouseLeave={() => setHoveredPoint(null)}
        >
          {/* Fills & Definitions */}
          <defs>
            <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--ink-blue)" stopOpacity="0.15" />
              <stop offset="100%" stopColor="var(--bg-paper)" stopOpacity="0.01" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
            const y = paddingTop + ratio * (svgHeight - paddingTop - paddingBottom)
            const gridVal = maxRevenue * (1.0 - ratio)
            return (
              <g key={i}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={svgWidth - paddingRight}
                  y2={y}
                  stroke="rgba(0,0,0,0.08)"
                  strokeWidth="1"
                  strokeDasharray="2,3"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="mono"
                  style={{ fontSize: '0.55rem', fill: 'var(--text-muted)' }}
                >
                  {formatMoneyCompact(gridVal, currency)}
                </text>
              </g>
            )
          })}

          {/* Render Tab 1: Sales Line/Area Trend */}
          {activeTab === 'trend' && lineChartContent && (
            <>
              {/* Subtle Area Fill */}
              <path
                d={lineChartContent.closedPathString}
                fill="url(#trendGrad)"
              />

              {/* Precise Blue Trend Line */}
              <path
                d={lineChartContent.pathString}
                fill="none"
                stroke="var(--ink-blue)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Data points */}
              {lineChartContent.coords.map((c, i) => (
                <circle
                  key={i}
                  cx={c.x}
                  cy={c.y}
                  r={hoveredPoint?.rawDate === c.data.rawDate ? 6 : 3.5}
                  fill={hoveredPoint?.rawDate === c.data.rawDate ? 'var(--ink-red)' : 'var(--ink-blue)'}
                  stroke="var(--bg-paper)"
                  strokeWidth="1.5"
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                  onMouseEnter={(e) => {
                    setHoveredPoint({
                      rawDate: c.data.rawDate,
                      x: c.x,
                      y: c.y,
                      label: c.data.date,
                      val1: c.data.revenue
                    })
                  }}
                />
              ))}

              {/* Bottom Labels */}
              {lineChartContent.coords.map((c, i) => {
                if (i % 2 !== 0 && i !== lineChartContent.coords.length - 1) return null
                return (
                  <text
                    key={i}
                    x={c.x}
                    y={svgHeight - paddingBottom + 18}
                    textAnchor="middle"
                    className="mono"
                    style={{ fontSize: '0.55rem', fill: 'var(--text-muted)' }}
                  >
                    {c.data.date}
                  </text>
                )
              })}
            </>
          )}

          {/* Render Tab 2: Comparison Bar Graph */}
          {activeTab === 'comparison' && barChartContent && (
            <>
              {barChartContent.map((group, i) => {
                const isHovered = hoveredPoint?.label === group.data.category
                return (
                  <g key={i} style={{ cursor: 'pointer' }}>
                    {/* Revenue Bar (Navy) */}
                    <rect
                      x={group.revBar.x}
                      y={group.revBar.y}
                      width={group.revBar.width}
                      height={Math.max(group.revBar.height, 1)}
                      fill="var(--ink-blue)"
                      opacity={isHovered ? 1.0 : 0.85}
                      stroke="var(--ink-black)"
                      strokeWidth="1"
                      onMouseEnter={() => setHoveredPoint({
                        x: group.groupCenterX,
                        y: Math.min(group.revBar.y, group.cogsBar.y),
                        label: group.data.category,
                        val1: group.data.revenue,
                        val2: group.data.cogs
                      })}
                    />

                    {/* Cost/COGS Bar (Gold) */}
                    <rect
                      x={group.cogsBar.x}
                      y={group.cogsBar.y}
                      width={group.cogsBar.width}
                      height={Math.max(group.cogsBar.height, 1)}
                      fill="var(--ink-yellow)"
                      opacity={isHovered ? 1.0 : 0.8}
                      stroke="var(--ink-black)"
                      strokeWidth="1"
                      onMouseEnter={() => setHoveredPoint({
                        x: group.groupCenterX,
                        y: Math.min(group.revBar.y, group.cogsBar.y),
                        label: group.data.category,
                        val1: group.data.revenue,
                        val2: group.data.cogs
                      })}
                    />

                    {/* Bottom Category Label */}
                    <text
                      x={group.groupCenterX}
                      y={svgHeight - paddingBottom + 18}
                      textAnchor="middle"
                      className="mono"
                      style={{ fontSize: '0.55rem', fill: 'var(--text-muted)' }}
                    >
                      {group.data.category}
                    </text>
                  </g>
                )
              })}
            </>
          )}

          {/* Flat line base */}
          <line
            x1={paddingLeft}
            y1={svgHeight - paddingBottom}
            x2={svgWidth - paddingRight}
            y2={svgHeight - paddingBottom}
            stroke="var(--ink-black)"
            strokeWidth="1.5"
          />
        </svg>

        {/* Dynamic Editorial Tooltip Overlay */}
        {hoveredPoint && (
          <div
            className="editorial-tooltip"
            style={{
              position: 'absolute',
              left: `${Math.min(Math.max((hoveredPoint.x / svgWidth) * 100, 15), 85)}%`,
              top: `${(hoveredPoint.y / svgHeight) * 100 - 32}%`,
              transform: 'translate(-50%, -100%)',
              background: '#0D1B2A',
              color: '#FDFCF0',
              padding: '0.5rem 0.75rem',
              border: '1px solid #C9A84C',
              borderRadius: '3px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
              boxShadow: '4px 4px 0 rgba(0,0,0,0.15)',
              pointerEvents: 'none',
              zIndex: 5,
              whiteSpace: 'nowrap'
            }}
          >
            <div style={{ fontWeight: 'bold', borderBottom: '1px solid rgba(255,255,255,0.15)', paddingBottom: '0.2rem', marginBottom: '0.2rem', color: '#C9A84C' }}>
              {hoveredPoint.label}
            </div>
            <div>
              Revenue: <span style={{ color: '#fff', fontWeight: 600 }}>{formatMoneyDetailed(hoveredPoint.val1, currency)}</span>
            </div>
            {hoveredPoint.val2 !== undefined && (
              <div style={{ marginTop: '0.1rem' }}>
                COGS: <span style={{ color: '#FCD34D' }}>{formatMoneyDetailed(hoveredPoint.val2, currency)}</span>
              </div>
            )}
            {hoveredPoint.val2 !== undefined && (
              <div style={{ marginTop: '0.1rem', color: '#34D399', fontWeight: 'bold' }}>
                Margin: {((hoveredPoint.val1 - hoveredPoint.val2) / Math.max(hoveredPoint.val1, 1) * 100).toFixed(1)}%
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend strip */}
      {activeTab === 'comparison' && (
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', background: 'var(--ink-blue)', border: '1px solid #000' }} />
            <span className="mono" style={{ fontSize: '0.55rem' }}>Total Revenue</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', background: 'var(--ink-yellow)', border: '1px solid #000' }} />
            <span className="mono" style={{ fontSize: '0.55rem' }}>Cost of Goods Sold (COGS)</span>
          </div>
        </div>
      )}
    </div>
  )
}
