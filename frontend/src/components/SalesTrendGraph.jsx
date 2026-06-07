import { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { formatMoneyCompact, formatMoneyDetailed } from '../services/currency';

// Custom tooltips with newsprint broadsheet aesthetics defined outside render
const CustomTooltip = ({ active, payload, label, currency }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div style={{
        background: '#FDFCF0',
        color: '#1A1A1A',
        padding: '0.65rem 0.95rem',
        border: '2px solid #1A1A1A',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.7rem',
        boxShadow: '4px 4px 0 #1A1A1A',
        pointerEvents: 'none'
      }}>
        <div style={{ fontWeight: 'bold', borderBottom: '1px dashed #1A1A1A', paddingBottom: '0.2rem', marginBottom: '0.3rem', color: '#8B0000' }}>
          {label || data.category || data.name}
        </div>
        {payload.map((p, idx) => {
          if (p.value !== undefined && p.value !== null) {
            if (Array.isArray(p.value)) {
              return (
                <div key={idx} style={{ margin: '0.1rem 0', fontStyle: 'italic', color: '#B8860B' }}>
                  {p.name}: <span>{formatMoneyDetailed(p.value[0], currency)} - {formatMoneyDetailed(p.value[1], currency)}</span>
                </div>
              );
            }
            return (
              <div key={idx} style={{ margin: '0.1rem 0' }}>
                {p.name}: <span style={{ color: p.color || '#003366', fontWeight: 700 }}>{formatMoneyDetailed(p.value, currency)}</span>
              </div>
            );
          }
          return null;
        })}
        {data.margin !== undefined && (
          <div style={{ marginTop: '0.2rem', color: '#1A4D2E', fontWeight: 'bold', borderTop: '1px dotted #1A1A1A', paddingTop: '0.15rem' }}>
            Margin: {data.margin.toFixed(1)}%
          </div>
        )}
        {data.percent !== undefined && (
          <div style={{ marginTop: '0.2rem', color: '#8B0000', fontWeight: 'bold', borderTop: '1px dotted #1A1A1A', paddingTop: '0.15rem' }}>
            Share: {data.percent.toFixed(1)}%
          </div>
        )}
        {data.isAnomaly && (
          <div style={{ marginTop: '0.25rem', color: '#8B0000', fontWeight: 'bold', borderTop: '1px dashed #8B0000', paddingTop: '0.2rem', fontSize: '0.62rem' }}>
            ⚠️ EXTREME VOLUME SPIKE DETECTED (&gt;3σ)
          </div>
        )}
      </div>
    );
  }
  return null;
};

export default function SalesTrendGraph({ sales = [], categoryBreakdown = [], forecast = [], currency = 'INR' }) {
  const [activeTab, setActiveTab] = useState('trend'); // 'trend' | 'comparison' | 'share'

  // Broadsheet Print Color Palette
  const colors = useMemo(() => [
    '#003366', // var(--ink-blue)
    '#B8860B', // var(--ink-yellow)
    '#1A4D2E', // var(--ink-green)
    '#8B0000', // var(--ink-red)
    '#4A6B82', // Slate/Steel blue
    '#8B7A5E', // Khaki/Sepia
    '#5C3D2E', // Umber
    '#2E4053'  // Charcoal
  ], []);

  // ── Tab 1: Daily Revenue Trend Data ──────────────────────────────────────
  const trendData = useMemo(() => {
    if (!sales || sales.length === 0) return [];

    // Group by sale_date
    const dailyMap = {};
    sales.forEach(s => {
      if (!s.sale_date) return;
      const dateStr = s.sale_date.substring(0, 10);
      if (!dailyMap[dateStr]) {
        dailyMap[dateStr] = 0;
      }
      dailyMap[dateStr] += s.total_revenue || 0;
    });

    // Sort chronologically and grab last 15 days of activity
    const sortedDates = Object.keys(dailyMap).sort();
    const last15 = sortedDates.slice(-15);

    // Calculate historical mean and standard deviation for aggregate daily revenue
    const histRevenues = Object.values(dailyMap);
    const histCount = histRevenues.length;
    const histMean = histCount > 0 ? histRevenues.reduce((a, b) => a + b, 0) / histCount : 0;
    const histVariance = histCount > 0 ? histRevenues.reduce((a, b) => a + Math.pow(b - histMean, 2), 0) / histCount : 0;
    const histStd = Math.sqrt(histVariance);

    const hist = last15.map(d => {
      let displayDate = d;
      try {
        const parts = d.split('-');
        if (parts.length === 3) {
          const dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
          displayDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
      } catch {
        // fallback to original date format
      }

      const rev = dailyMap[d];
      const isAnomaly = histStd > 0 && Math.abs(rev - histMean) > 3 * histStd;

      return {
        date: displayDate,
        revenue: rev,
        isAnomaly: isAnomaly,
        type: 'Historical'
      };
    });

    // Append forecast data seamlessly
    const fore = (forecast || []).map(f => {
      let displayDate = f.date;
      try {
        const parts = f.date.split('-');
        if (parts.length === 3) {
          const dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
          displayDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
      } catch {
        // fallback to original date format
      }

      return {
        date: displayDate,
        forecastRevenue: f.revenue,
        forecastLower: f.forecast_lower || f.revenue,
        forecastUpper: f.forecast_upper || f.revenue,
        type: 'Forecast'
      };
    });

    // Merge them chronologically for a continuous flow
    return [...hist, ...fore];
  }, [sales, forecast]);

  // ── Tab 2: Category Revenue vs COGS Comparison Data ──────────────────────
  const comparisonData = useMemo(() => {
    if (!categoryBreakdown || categoryBreakdown.length === 0) {
      // Build from raw sales if categoryBreakdown is empty
      const catMap = {};
      sales.forEach(s => {
        const cat = s.product_category || 'Other';
        if (!catMap[cat]) {
          catMap[cat] = { revenue: 0, cogs: 0 };
        }
        catMap[cat].revenue += s.total_revenue || 0;
        catMap[cat].cogs += s.cogs || 0;
      });
      return Object.keys(catMap).map(cat => ({
        category: cat,
        revenue: catMap[cat].revenue,
        cogs: catMap[cat].cogs,
        margin: catMap[cat].revenue > 0 ? ((catMap[cat].revenue - catMap[cat].cogs) / catMap[cat].revenue) * 100 : 0
      }));
    }

    const rawCogsMap = {};
    sales.forEach(s => {
      const cat = s.product_category || 'Other';
      if (!rawCogsMap[cat]) rawCogsMap[cat] = 0;
      rawCogsMap[cat] += s.cogs || 0;
    });

    return categoryBreakdown.map(cat => ({
      category: cat.category,
      revenue: cat.revenue,
      cogs: rawCogsMap[cat.category] || (cat.revenue * 0.6), // Fallback to 60% if no COGS
      margin: cat.revenue > 0 ? ((cat.revenue - (rawCogsMap[cat.category] || (cat.revenue * 0.6))) / cat.revenue) * 100 : 0
    }));
  }, [categoryBreakdown, sales]);

  // ── Tab 3: Category Revenue Share (Pie) ──────────────────────────────────
  const shareData = useMemo(() => {
    const totalRev = comparisonData.reduce((acc, curr) => acc + curr.revenue, 0) || 1;
    return comparisonData.map(d => ({
      name: d.category,
      value: d.revenue,
      percent: (d.revenue / totalRev) * 100
    })).sort((a, b) => b.value - a.value);
  }, [comparisonData]);

  const totalRevenue = useMemo(() => {
    return comparisonData.reduce((acc, curr) => acc + curr.revenue, 0);
  }, [comparisonData]);

  return (
    <div className="card newsprint-chart-card" style={{
      padding: '1.5rem',
      marginBottom: '1.5rem',
      position: 'relative',
      border: '4px double var(--ink-black)',
      background: 'var(--bg-paper)',
      boxShadow: '6px 6px 0 rgba(26, 26, 26, 0.05)'
    }}>
      {/* Chart Header Row */}
      <div className="chart-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid rgba(0,0,0,0.12)', paddingBottom: '0.75rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
          <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--ink-red)', letterSpacing: '0.12em', fontWeight: 700, textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
            ✦ Interactive Analytics ✦
          </span>
          <h4 style={{ margin: 0, fontSize: '1.35rem', fontFamily: 'var(--font-display)', fontWeight: 800, color: 'var(--ink-black)', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
            {activeTab === 'trend' ? 'Daily Revenue History & Smart Forecast' : activeTab === 'comparison' ? 'Revenue vs Cost Breakdown by Category' : 'Revenue Share Contribution by Product Category'}
          </h4>
        </div>
        
        {/* Action Tabs */}
        <div className="tab-group" style={{ display: 'flex', gap: '0.3rem' }}>
          {[
            { id: 'trend', label: '📈 Sales Trend' },
            { id: 'comparison', label: '📊 Cost Comparison' },
            { id: 'share', label: '🍩 Category Share' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '0.4rem 0.9rem',
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                textTransform: 'uppercase',
                fontWeight: 700,
                background: activeTab === tab.id ? 'var(--ink-black)' : 'transparent',
                color: activeTab === tab.id ? 'var(--bg-paper)' : 'var(--ink-black)',
                border: '1px solid var(--ink-black)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chart Stage */}
      <div style={{ width: '100%', height: 350, overflow: 'visible' }}>
        {activeTab === 'trend' && (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="histColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#003366" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#FDFCF0" stopOpacity={0.01}/>
                </linearGradient>
                <linearGradient id="foreColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#B8860B" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#FDFCF0" stopOpacity={0.01}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
              <XAxis
                dataKey="date"
                stroke="#1A1A1A"
                tick={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem' }}
              />
              <YAxis
                stroke="#1A1A1A"
                tickFormatter={(v) => formatMoneyCompact(v, currency)}
                tick={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem' }}
              />
              <Tooltip content={<CustomTooltip currency={currency} />} />
              <Area
                name="95% Confidence Band"
                type="monotone"
                dataKey={(d) => d.type === 'Forecast' ? [d.forecastLower, d.forecastUpper] : [null, null]}
                stroke="none"
                fill="#B8860B"
                fillOpacity={0.12}
                legendType="rect"
              />
              <Area
                name="Historical Revenue"
                type="monotone"
                dataKey="revenue"
                stroke="#003366"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#histColor)"
                dot={(props) => {
                  const { cx, cy, payload } = props;
                  if (payload && payload.isAnomaly) {
                    return (
                      <g key={payload.date}>
                        <circle cx={cx} cy={cy} r={6} fill="#8B0000" stroke="#FDFCF0" strokeWidth={1.5} />
                        <path d={`M ${cx} ${cy - 12} L ${cx - 5} ${cy - 4} L ${cx + 5} ${cy - 4} Z`} fill="#8B0000" />
                        <text x={cx} y={cy - 15} textAnchor="middle" fill="#8B0000" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', fontWeight: 800 }}>⚠️ SPIKE</text>
                      </g>
                    );
                  }
                  return null;
                }}
              />
              <Area
                name="Projected Forecast"
                type="monotone"
                dataKey="forecastRevenue"
                stroke="#B8860B"
                strokeWidth={2.5}
                strokeDasharray="4 4"
                fillOpacity={1}
                fill="url(#foreColor)"
              />
              <Legend
                wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', textTransform: 'uppercase', marginTop: '10px' }}
                iconType="plainline"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}

        {activeTab === 'comparison' && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={comparisonData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
              <XAxis
                dataKey="category"
                stroke="#1A1A1A"
                tick={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem' }}
              />
              <YAxis
                stroke="#1A1A1A"
                tickFormatter={(v) => formatMoneyCompact(v, currency)}
                tick={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem' }}
              />
              <Tooltip content={<CustomTooltip currency={currency} />} />
              <Bar name="Total Revenue" dataKey="revenue" fill="#003366" stroke="#1A1A1A" strokeWidth={1} />
              <Bar name="Cost of Goods Sold (COGS)" dataKey="cogs" fill="#B8860B" stroke="#1A1A1A" strokeWidth={1} />
              <Legend
                wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', textTransform: 'uppercase', marginTop: '10px' }}
              />
            </BarChart>
          </ResponsiveContainer>
        )}

        {activeTab === 'share' && (
          <div style={{ display: 'flex', flexDirection: 'row', height: '100%', alignItems: 'center', justifyContent: 'space-around', gap: '1rem' }}>
            <div style={{ width: '50%', height: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={shareData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {shareData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={colors[index % colors.length]} stroke="#1A1A1A" strokeWidth={1} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip currency={currency} />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            {/* Visual Legend Table with dotted leaders */}
            <div style={{
              width: '45%',
              maxHeight: '100%',
              overflowY: 'auto',
              border: '1px solid #1A1A1A',
              padding: '0.9rem',
              background: 'var(--bg-tint)',
              fontFamily: 'var(--font-mono)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1A1A1A', paddingBottom: '0.35rem', marginBottom: '0.5rem', fontSize: '0.6rem', fontWeight: 700 }}>
                <span>CATEGORY</span>
                <span>SHARE</span>
              </div>
              {shareData.map((d, index) => {
                const color = colors[index % colors.length];
                return (
                  <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0.35rem 0', fontSize: '0.72rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: color, border: '1px solid #1a1a1a' }} />
                      <span style={{ fontFamily: 'var(--font-serif)', color: '#1a1a1a', fontWeight: 600 }}>{d.name}</span>
                    </div>
                    <span style={{ fontSize: '0.65rem' }}>........................</span>
                    <span style={{ fontWeight: 700 }}>{d.percent.toFixed(1)}%</span>
                  </div>
                );
              })}
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px dashed #1A1A1A', paddingTop: '0.5rem', marginTop: '0.5rem', fontSize: '0.75rem', fontWeight: 700 }}>
                <span>TOTAL REVENUE</span>
                <span style={{ color: 'var(--ink-red)' }}>{formatMoneyCompact(totalRevenue, currency)}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
