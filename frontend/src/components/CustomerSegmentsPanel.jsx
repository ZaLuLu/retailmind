import { formatMoneyCompact } from '../services/currency'
import DashboardTooltip from './DashboardTooltip'

export default function CustomerSegmentsPanel({ customerSegments = [], currency = 'INR', onAskAdvisor }) {
  // Sort segments by revenue contribution share descending
  const sortedSegments = [...customerSegments].sort((a, b) => b.revenue - a.revenue)

  // Helper to get telex tag style and text
  const getSegmentTag = (segment) => {
    switch (segment.toLowerCase()) {
      case 'b2b':
        return {
          text: 'WHOLESALE',
          className: 'telex-stamp-badge red-stamp',
          color: 'var(--ink-red)',
          lightColor: 'rgba(139, 0, 0, 0.05)',
          mediumColor: 'rgba(139, 0, 0, 0.12)'
        }
      case 'online':
        return {
          text: 'E-COMMERCE',
          className: 'telex-stamp-badge',
          color: 'var(--ink-blue)',
          lightColor: 'rgba(0, 51, 102, 0.05)',
          mediumColor: 'rgba(0, 51, 102, 0.12)'
        }
      case 'walk-in':
      default:
        return {
          text: 'STOREFRONT',
          className: 'telex-stamp-badge green-stamp',
          color: 'var(--ink-green)',
          lightColor: 'rgba(26, 77, 46, 0.05)',
          mediumColor: 'rgba(26, 77, 46, 0.12)'
        }
    }
  }

  return (
    <div className="card newsprint-segment-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
      <div className="section-kicker" style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center' }}>
        <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.08em', display: 'flex', alignItems: 'center' }}>
          Customer Analytics
          <DashboardTooltip 
            title="Segment Metrics" 
            content="Breaks down performance metrics (Revenue, Gross Margin, Average Order Value, and MoM Growth) across B2B, Online, and Walk-in customer channels." 
          />
        </span>
        <div className="kicker-line" style={{ height: '1px', background: 'rgba(0,0,0,0.12)', margin: '4px 0', flex: 1, marginLeft: '12px' }} />
      </div>

      <h4 className="serif" style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 800, borderBottom: '3px double var(--ink-black)', paddingBottom: '0.5rem' }}>
        Customer Segment Performance
      </h4>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {sortedSegments.map((seg) => {
          const tagInfo = getSegmentTag(seg.segment)
          const shareVal = seg.share || 0
          const growthVal = seg.mom_growth_pct || 0
          
          // Heatmap background color intensity scaled by shareVal
          const heatmapBg = shareVal > 40 ? tagInfo.mediumColor : tagInfo.lightColor;

          return (
            <div 
              key={seg.segment} 
              className="segment-row" 
              style={{ 
                borderBottom: '1px dashed rgba(0,0,0,0.12)', 
                paddingBottom: '1rem',
                backgroundColor: heatmapBg,
                padding: '0.5rem',
                borderRadius: '4px',
                marginBottom: '0.25rem'
              }}
            >
              {/* Segment Header (Name & Channel Tag) */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="serif" style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                  {seg.segment} Segment
                </span>
                <span className={tagInfo.className} style={{ fontSize: '0.55rem', margin: 0 }}>
                  {tagInfo.text}
                </span>
              </div>

              {/* Core Metrics: Revenue & Share */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.4rem' }}>
                <span className="serif" style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ink-black)' }}>
                  {formatMoneyCompact(seg.revenue, currency)}
                </span>
                <span className="mono" style={{ fontSize: '0.7rem', fontWeight: 700 }}>
                  {shareVal.toFixed(1)}% Share
                </span>
              </div>

              {/* Progress Bar (SVG) */}
              <div style={{ width: '100%', height: '8px', background: 'rgba(0,0,0,0.06)', border: '1px solid var(--ink-black)', padding: '1px', marginBottom: '0.75rem', boxSizing: 'border-box' }}>
                <div 
                  style={{ 
                    width: `${Math.max(Math.min(shareVal, 100), 0)}%`, 
                    height: '100%', 
                    background: tagInfo.color,
                    transition: 'width 0.8s ease'
                  }} 
                />
              </div>

              {/* Detailed Metrics Panel */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', background: 'var(--bg-paper)', padding: '0.5rem', border: '1px solid rgba(0,0,0,0.08)' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span className="mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)' }}>Gross Margin</span>
                  <span className="mono" style={{ fontSize: '0.7rem', fontWeight: 700, color: seg.margin_pct >= 25 ? 'var(--ink-green)' : 'var(--ink-red)' }}>
                    {seg.margin_pct.toFixed(1)}%
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span className="mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)' }}>Avg Order (AOV)</span>
                  <span className="mono" style={{ fontSize: '0.7rem', fontWeight: 700 }}>
                    {formatMoneyCompact(seg.aov, currency)}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span className="mono" style={{ fontSize: '0.5rem', color: 'var(--text-muted)' }}>MoM Growth</span>
                  <span className="mono" style={{ fontSize: '0.7rem', fontWeight: 700, color: growthVal >= 0 ? 'var(--ink-green)' : 'var(--ink-red)' }}>
                    {growthVal >= 0 ? '+' : ''}{growthVal.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Ask Advisor prompt trigger */}
              {onAskAdvisor && (
                <div style={{ marginTop: '0.5rem', display: 'flex', justifyContent: 'flex-start' }}>
                  <button
                    className="ask-advisor-btn mono"
                    style={{
                      fontSize: '0.62rem',
                      background: 'var(--bg-paper)',
                      border: '1px solid var(--ink-black)',
                      padding: '3px 8px',
                      cursor: 'pointer',
                      boxShadow: '2px 2px 0 var(--ink-black)',
                      transition: 'all 0.1s ease',
                      fontWeight: 700
                    }}
                    onClick={() => onAskAdvisor(`Reviewing our segment analytics: the "${seg.segment}" channel brings in ${formatMoneyCompact(seg.revenue, currency)} (${shareVal.toFixed(1)}% share) with a gross margin of ${seg.margin_pct.toFixed(1)}% and MoM growth of ${growthVal.toFixed(1)}%. What specific strategic optimizations do you recommend for this segment?`)}
                  >
                    Ask Advisor about Segment →
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
