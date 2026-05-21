import React from 'react'

import { formatMoneyCompact } from '../services/currency'

const RevenueHero = ({ summary, currency = 'INR' }) => {
  const mom = summary?.mom_revenue_change_pct ?? 0
  const momUp = mom >= 0

  const kpis = [
    {
      label: 'MTD REVENUE',
      value: formatMoneyCompact(summary?.total_revenue ?? 0, currency),
      sub: `${summary?.num_sales ?? 0} transactions`,
      accent: '#C9A84C',
    },
    {
      label: 'GROSS PROFIT',
      value: formatMoneyCompact(summary?.gross_profit ?? 0, currency),
      sub: `COGS: ${formatMoneyCompact(summary?.total_cogs ?? 0, currency)}`,
      accent: '#4CAF50',
    },
    {
      label: 'OVERALL MARGIN',
      value: `${summary?.overall_margin_pct ?? 0}%`,
      sub: 'Blended gross margin',
      accent: summary?.overall_margin_pct >= 30 ? '#4CAF50' : '#E57373',
    },
    {
      label: 'MoM CHANGE',
      value: `${momUp ? '+' : ''}${mom}%`,
      sub: 'vs. previous month',
      accent: momUp ? '#4CAF50' : '#E57373',
    },
  ]

  return (
    <section className="revenue-hero">
      <div className="section-kicker">
        <span className="kicker-label">Business Performance</span>
        <div className="kicker-line" />
      </div>
      <div className="kpi-grid">
        {kpis.map((kpi) => (
          <div className="kpi-card" key={kpi.label}>
            <span className="kpi-label">{kpi.label}</span>
            <span className="kpi-value" style={{ color: kpi.accent }}>{kpi.value}</span>
            <span className="kpi-sub">{kpi.sub}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export default RevenueHero
