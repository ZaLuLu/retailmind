import React, { useState, useMemo } from 'react'
import { formatMoneyCompact, formatMoneyDetailed, convertMoney } from '../services/currency'

export default function SalesTrendGraph({ sales = [], categoryBreakdown = [], forecast = [], currency = 'INR' }) {
  const [activeTab, setActiveTab] = useState('trend') // 'trend' | 'comparison' | 'share'
  const [hoveredPoint, setHoveredPoint] = useState(null) // { x, y, label, val1, val2 } for tooltip

  // Broadside Print Color Palette
  const colors = useMemo(() => [
    'var(--ink-blue)',
    'var(--gold)',
    'var(--green)',
    'var(--red)',
    'var(--ink-muted)',
    '#4A6B82', // Slate/Steel blue
    '#8B7A5E', // Khaki/Sepia
    '#5C3D2E'  // Umber
  ], [])

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

  // ── Tab 1.5: Forecast Data ───────────────────────────────────────────────
  const forecastData = useMemo(() => {
    if (!forecast || forecast.length === 0) return []
    return forecast.map(f => {
      let displayDate = f.date
      try {
        const parts = f.date.split('-')
        if (parts.length === 3) {
          const dateObj = new Date(parts[0], parts[1] - 1, parts[2])
          displayDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        }
      } catch (e) {}

      return {
        rawDate: f.date,
        date: displayDate,
        revenue: f.revenue
      }
    })
  }, [forecast])

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

  // ── Tab 3: Category Revenue Share (Donut Segment Calculation) ────────────
  const shareData = useMemo(() => {
    const totalRev = comparisonData.reduce((acc, curr) => acc + curr.revenue, 0) || 1
    let accumulatedPercent = 0

    return comparisonData.map((d) => {
      const percent = (d.revenue / totalRev) * 100
      const startPercent = accumulatedPercent
      accumulatedPercent += percent
      return {
        ...d,
        percent,
        startPercent
      }
    })
  }, [comparisonData])

  // ── SVG Constants & Scaling for Line Chart ───────────────────────────────
  const svgWidth = 700
  const svgHeight = 240
  const paddingLeft = 60
  const paddingRight = 30
  const paddingTop = 20
  const paddingBottom = 40

  const maxRevenue = useMemo(() => {
    if (activeTab === 'trend') {
      const histVals = trendData.map(d => d.revenue)
      const foreVals = forecastData.map(d => d.revenue)
      const maxVal = Math.max(...histVals, ...foreVals, 1000)
      return maxVal * 1.15 // 15% buffer
    } else {
      const allVals = comparisonData.flatMap(d => [d.revenue, d.cogs])
      const maxVal = Math.max(...allVals, 1000)
      return maxVal * 1.15
    }
  }, [trendData, forecastData, comparisonData, activeTab])

  // ── Render Line Chart ────────────────────────────────────────────────────
  const lineChartContent = useMemo(() => {
    if (activeTab !== 'trend' || trendData.length === 0) return null

    const totalPoints = trendData.length + forecastData.length
    const xInterval = (svgWidth - paddingLeft - paddingRight) / Math.max(totalPoints - 1, 1)

    // Historical Coords
    const histCoords = trendData.map((d, index) => {
      const x = paddingLeft + index * xInterval
      const y = svgHeight - paddingBottom - ((d.revenue / maxRevenue) * (svgHeight - paddingTop - paddingBottom))
      return { x, y, data: d }
    })

    // Forecast Coords
    const forecastCoords = forecastData.map((d, index) => {
      const x = paddingLeft + (trendData.length + index) * xInterval
      const y = svgHeight - paddingBottom - ((d.revenue / maxRevenue) * (svgHeight - paddingTop - paddingBottom))
      return { x, y, data: d }
    })

    // Historical path
    let histPathString = ''
    histCoords.forEach((c, index) => {
      if (index === 0) {
        histPathString += `M ${c.x} ${c.y}`
      } else {
        histPathString += ` L ${c.x} ${c.y}`
      }
    })

    // Forecast path (starts from last historical)
    let forecastPathString = ''
    if (histCoords.length > 0 && forecastCoords.length > 0) {
      const lastHist = histCoords[histCoords.length - 1]
      forecastPathString = `M ${lastHist.x} ${lastHist.y}`
      forecastCoords.forEach((c) => {
        forecastPathString += ` L ${c.x} ${c.y}`
      })
    } else if (forecastCoords.length > 0) {
      forecastCoords.forEach((c, index) => {
        if (index === 0) {
          forecastPathString += `M ${c.x} ${c.y}`
        } else {
          forecastPathString += ` L ${c.x} ${c.y}`
        }
      })
    }

    const closedHistPathString = histCoords.length > 0
      ? `${histPathString} L ${histCoords[histCoords.length - 1].x} ${svgHeight - paddingBottom} L ${histCoords[0].x} ${svgHeight - paddingBottom} Z`
      : ''

    const closedForecastPathString = (histCoords.length > 0 && forecastCoords.length > 0)
      ? `M ${histCoords[histCoords.length - 1].x} ${histCoords[histCoords.length - 1].y} ` +
        forecastCoords.map(c => `L ${c.x} ${c.y}`).join(' ') +
        ` L ${forecastCoords[forecastCoords.length - 1].x} ${svgHeight - paddingBottom}` +
        ` L ${histCoords[histCoords.length - 1].x} ${svgHeight - paddingBottom} Z`
      : (forecastCoords.length > 0
        ? `M ${forecastCoords[0].x} ${forecastCoords[0].y} ` +
          forecastCoords.slice(1).map(c => `L ${c.x} ${c.y}`).join(' ') +
          ` L ${forecastCoords[forecastCoords.length - 1].x} ${svgHeight - paddingBottom}` +
          ` L ${forecastCoords[0].x} ${svgHeight - paddingBottom} Z`
        : '')

    return { histCoords, forecastCoords, histPathString, forecastPathString, closedHistPathString, closedForecastPathString }
  }, [trendData, forecastData, maxRevenue, activeTab])

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
            {activeTab === 'trend' ? 'Daily Revenue History (MTD)' : activeTab === 'comparison' ? 'Revenue vs Cost Breakdown by Category' : 'Revenue Share Contribution by Product Category'}
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
          <button
            onClick={() => { setActiveTab('share'); setHoveredPoint(null) }}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.65rem',
              background: activeTab === 'share' ? 'var(--ink-black)' : 'transparent',
              color: activeTab === 'share' ? 'var(--bg-paper)' : 'var(--ink-black)',
              border: '1px solid var(--ink-black)'
            }}
          >
            🍩 Category Share
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
            <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="8" stroke="var(--ink-blue)" strokeWidth="1.2" opacity="0.22" />
            </pattern>
          </defs>

          {/* Grid lines (Only for trend and comparison, share is coordinate-less) */}
          {activeTab !== 'share' && [0, 0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
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
              {/* Subtle Historical Area Fill */}
              <path
                d={lineChartContent.closedHistPathString}
                fill="url(#trendGrad)"
              />

              {/* Halftone Diagonal Stripe Forecast Area Fill */}
              {lineChartContent.closedForecastPathString && (
                <path
                  d={lineChartContent.closedForecastPathString}
                  fill="url(#diagonalHatch)"
                />
              )}

              {/* Precise Blue Historical Trend Line */}
              <path
                d={lineChartContent.histPathString}
                fill="none"
                stroke="var(--ink-blue)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="animate-draw"
                strokeDasharray="1000"
                strokeDashoffset="1000"
              />

              {/* Dashed Forecast Trend Line */}
              {lineChartContent.forecastPathString && (
                <path
                  d={lineChartContent.forecastPathString}
                  fill="none"
                  stroke="var(--ink-blue)"
                  strokeWidth="2.5"
                  strokeDasharray="4,4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}

              {/* Historical Data points */}
              {lineChartContent.histCoords.map((c, i) => (
                <circle
                  key={`hist-${i}`}
                  cx={c.x}
                  cy={c.y}
                  r={hoveredPoint?.rawDate === c.data.rawDate ? 6 : 3.5}
                  fill={hoveredPoint?.rawDate === c.data.rawDate ? 'var(--ink-red)' : 'var(--ink-blue)'}
                  stroke="var(--bg-paper)"
                  strokeWidth="1.5"
                  className="animate-scale"
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease', animationDelay: `${i * 0.04}s` }}
                  onMouseEnter={(e) => {
                    setHoveredPoint({
                      rawDate: c.data.rawDate,
                      x: c.x,
                      y: c.y,
                      label: c.data.date,
                      val1: c.data.revenue,
                      isForecast: false
                    })
                  }}
                />
              ))}

              {/* Forecast Data points */}
              {lineChartContent.forecastCoords.map((c, i) => (
                <circle
                  key={`fore-${i}`}
                  cx={c.x}
                  cy={c.y}
                  r={hoveredPoint?.rawDate === c.data.rawDate ? 6 : 3.5}
                  fill={hoveredPoint?.rawDate === c.data.rawDate ? 'var(--ink-red)' : 'var(--bg-paper)'}
                  stroke="var(--ink-blue)"
                  strokeWidth="2.0"
                  className="animate-scale"
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease', animationDelay: `${(lineChartContent.histCoords.length + i) * 0.04}s` }}
                  onMouseEnter={(e) => {
                    setHoveredPoint({
                      rawDate: c.data.rawDate,
                      x: c.x,
                      y: c.y,
                      label: `${c.data.date} (Forecast)`,
                      val1: c.data.revenue,
                      isForecast: true
                    })
                  }}
                />
              ))}

              {/* Bottom Labels */}
              {[...lineChartContent.histCoords, ...lineChartContent.forecastCoords].map((c, i, arr) => {
                if (i % 4 !== 0 && i !== arr.length - 1) return null
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

          {/* Render Tab 2: Comparison Bar Graph with Rise Animation */}
          {activeTab === 'comparison' && barChartContent && (
            <>
              {barChartContent.map((group, i) => {
                const isHovered = hoveredPoint?.label === group.data.category
                return (
                  <g key={i} style={{ cursor: 'pointer' }}>
                    {/* Revenue Bar (Navy) with bottom-centered origin and delay */}
                    <rect
                      x={group.revBar.x}
                      y={group.revBar.y}
                      width={group.revBar.width}
                      height={Math.max(group.revBar.height, 1)}
                      fill="var(--ink-blue)"
                      opacity={isHovered ? 1.0 : 0.85}
                      stroke="var(--ink-black)"
                      strokeWidth="1"
                      className="animate-rise"
                      style={{
                        transformOrigin: `${group.revBar.x + group.revBar.width / 2}px 200px`,
                        animationDelay: `${i * 0.05}s`
                      }}
                      onMouseEnter={() => setHoveredPoint({
                        x: group.groupCenterX,
                        y: Math.min(group.revBar.y, group.cogsBar.y),
                        label: group.data.category,
                        val1: group.data.revenue,
                        val2: group.data.cogs
                      })}
                    />

                    {/* Cost/COGS Bar (Gold) with bottom-centered origin and delay */}
                    <rect
                      x={group.cogsBar.x}
                      y={group.cogsBar.y}
                      width={group.cogsBar.width}
                      height={Math.max(group.cogsBar.height, 1)}
                      fill="var(--ink-yellow)"
                      opacity={isHovered ? 1.0 : 0.8}
                      stroke="var(--ink-black)"
                      strokeWidth="1"
                      className="animate-rise"
                      style={{
                        transformOrigin: `${group.cogsBar.x + group.cogsBar.width / 2}px 200px`,
                        animationDelay: `${i * 0.05 + 0.1}s`
                      }}
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

          {/* Render Tab 3: Category Share Donut Chart */}
          {activeTab === 'share' && shareData.length > 0 && (
            <g className="animate-scale" style={{ transformOrigin: '250px 120px' }}>
              {/* Donut Segments with offset mathematics and starting rotation */}
              <g transform="rotate(-90 250 120)">
                {shareData.map((d, i) => {
                  const color = colors[i % colors.length]
                  const isHovered = hoveredPoint?.label === d.category
                  
                  const r = 65
                  const C = 408.4 // 2 * pi * r
                  const strokeLength = (d.percent / 100) * C
                  const strokeOffset = C - (d.startPercent / 100) * C

                  return (
                    <circle
                      key={i}
                      cx="250"
                      cy="120"
                      r={r}
                      fill="transparent"
                      stroke={color}
                      strokeWidth={isHovered ? 34 : 26}
                      strokeDasharray={`${strokeLength} ${C}`}
                      strokeDashoffset={strokeOffset}
                      strokeLinecap={d.percent > 2.5 ? 'round' : 'butt'}
                      style={{
                        cursor: 'pointer',
                        transition: 'stroke-width 0.25s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.25s, opacity 0.25s',
                        opacity: hoveredPoint && !isHovered ? 0.6 : 1.0
                      }}
                      onMouseEnter={() => {
                        setHoveredPoint({
                          x: 250,
                          y: 90,
                          label: d.category,
                          val1: d.revenue,
                          val2: d.percent
                        })
                      }}
                    />
                  )
                })}
              </g>

              {/* Donut Center Hole Text */}
              <circle cx="250" cy="120" r="46" fill="var(--bg-paper)" stroke="var(--ink-black)" strokeWidth="0.5" />
              <text x="250" y="114" textAnchor="middle" className="mono" style={{ fontSize: '0.45rem', fill: 'var(--text-muted)' }}>
                TOTAL REVENUE
              </text>
              <text x="250" y="130" textAnchor="middle" style={{ fontFamily: 'var(--font-serif)', fontSize: '0.9rem', fontWeight: 800, fill: 'var(--ink-black)' }}>
                {formatMoneyCompact(shareData.reduce((acc, curr) => acc + curr.revenue, 0), currency)}
              </text>

              {/* Broadsheet Style Legend Table with dotted leaders */}
              <g transform="translate(440, 20)">
                {/* Vintage Border around Legend */}
                <rect x="-15" y="-12" width="245" height={shareData.length * 22 + 26} fill="var(--bg-tint)" stroke="var(--ink-black)" strokeWidth="1" />
                <line x1="-15" y1="12" x2="230" y2="12" stroke="var(--ink-black)" strokeWidth="1" />
                
                <text x="0" y="3" className="mono" style={{ fontSize: '0.55rem', fontWeight: 800 }}>CATEGORY CONTRIBUTION</text>
                <text x="215" y="3" className="mono" style={{ fontSize: '0.55rem', fontWeight: 800, textAnchor: 'end' }}>SHARE</text>

                {shareData.map((d, i) => {
                  const color = colors[i % colors.length]
                  const y = 30 + i * 22
                  const isHovered = hoveredPoint?.label === d.category

                  return (
                    <g key={i} style={{ cursor: 'pointer' }}
                       onMouseEnter={() => setHoveredPoint({
                         x: 250,
                         y: 90,
                         label: d.category,
                         val1: d.revenue,
                         val2: d.percent
                       })}>
                      {/* Color bullet */}
                      <circle cx="2" cy={y - 4} r="5" fill={color} stroke="var(--ink-black)" strokeWidth="1" />
                      
                      {/* Category Label */}
                      <text x="14" y={y} style={{ fontSize: '0.65rem', fontWeight: isHovered ? 'bold' : 'normal', fill: 'var(--ink-black)' }}>
                        {d.category.substring(0, 14)}
                      </text>
                      
                      {/* Dotted Leader */}
                      <text x="82" y={y} className="mono" style={{ fontSize: '0.55rem', fill: 'rgba(0,0,0,0.22)' }}>
                        ...................................
                      </text>
                      
                      {/* Percentage Share */}
                      <text x="215" y={y} className="mono" style={{ fontSize: '0.65rem', fontWeight: 700, textAnchor: 'end', fill: isHovered ? 'var(--ink-red)' : 'var(--ink-black)' }}>
                        {d.percent.toFixed(1)}%
                      </text>
                    </g>
                  )
                })}
              </g>
            </g>
          )}

          {/* Flat line base (Only for coordinate-based charts) */}
          {activeTab !== 'share' && (
            <line
              x1={paddingLeft}
              y1={svgHeight - paddingBottom}
              x2={svgWidth - paddingRight}
              y2={svgHeight - paddingBottom}
              stroke="var(--ink-black)"
              strokeWidth="1.5"
            />
          )}
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
              {hoveredPoint.isForecast ? 'Projected Rev: ' : 'Revenue: '}<span style={{ color: '#fff', fontWeight: 600 }}>{formatMoneyDetailed(hoveredPoint.val1, currency)}</span>
            </div>
            {activeTab !== 'share' && hoveredPoint.val2 !== undefined && (
              <div style={{ marginTop: '0.1rem' }}>
                COGS: <span style={{ color: '#FCD34D' }}>{formatMoneyDetailed(hoveredPoint.val2, currency)}</span>
              </div>
            )}
            {activeTab !== 'share' && hoveredPoint.val2 !== undefined && (
              <div style={{ marginTop: '0.1rem', color: '#34D399', fontWeight: 'bold' }}>
                Margin: {((hoveredPoint.val1 - hoveredPoint.val2) / Math.max(hoveredPoint.val1, 1) * 100).toFixed(1)}%
              </div>
            )}
            {activeTab === 'share' && hoveredPoint.val2 !== undefined && (
              <div style={{ marginTop: '0.1rem', color: '#60A5FA', fontWeight: 'bold' }}>
                Share: {hoveredPoint.val2.toFixed(1)}%
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend strip (Only for comparison chart) */}
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

      {/* Legend strip (Only for trend chart) */}
      {activeTab === 'trend' && forecastData.length > 0 && (
        <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginTop: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ display: 'inline-block', width: '16px', height: '0px', borderTop: '2.5px solid var(--ink-blue)' }} />
            <span className="mono" style={{ fontSize: '0.55rem' }}>Historical Revenue</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ display: 'inline-block', width: '16px', height: '0px', borderTop: '2.5px dashed var(--ink-blue)' }} />
            <span className="mono" style={{ fontSize: '0.55rem' }}>14-Day Holt-Winters Projection</span>
          </div>
        </div>
      )}
    </div>
  )
}
