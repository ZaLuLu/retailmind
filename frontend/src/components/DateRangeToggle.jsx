/**
 * DateRangeToggle
 *
 * Pill-style period selector: MTD | 7D | 30D | 90D | Custom
 * Custom mode shows two date inputs (from / to).
 *
 * Props:
 *   period       - active period string ('mtd'|'7d'|'30d'|'90d'|'custom')
 *   dateFrom     - string 'YYYY-MM-DD' (custom only)
 *   dateTo       - string 'YYYY-MM-DD' (custom only)
 *   onChange     - fn({ period, dateFrom, dateTo })
 */

import React, { useState } from 'react'

const PERIODS = [
  { value: 'mtd',    label: 'MTD' },
  { value: '7d',     label: '7D' },
  { value: '30d',    label: '30D' },
  { value: '90d',    label: '90D' },
  { value: 'custom', label: 'Custom' },
]

const DateRangeToggle = ({ period = 'mtd', dateFrom = '', dateTo = '', onChange }) => {
  const [localFrom, setLocalFrom] = useState(dateFrom)
  const [localTo, setLocalTo]     = useState(dateTo)

  const handlePeriod = (val) => {
    if (val !== 'custom') {
      onChange({ period: val, dateFrom: '', dateTo: '' })
    } else {
      onChange({ period: 'custom', dateFrom: localFrom, dateTo: localTo })
    }
  }

  const handleCustomApply = () => {
    if (!localFrom || !localTo) return
    if (localFrom > localTo) return
    onChange({ period: 'custom', dateFrom: localFrom, dateTo: localTo })
  }

  return (
    <div className="date-range-toggle">
      <div className="period-pills">
        {PERIODS.map(p => (
          <button
            key={p.value}
            className={`period-pill ${period === p.value ? 'active' : ''}`}
            onClick={() => handlePeriod(p.value)}
            aria-pressed={period === p.value}
          >
            {p.label}
          </button>
        ))}
      </div>

      {period === 'custom' && (
        <div className="custom-range">
          <input
            type="date"
            className="date-input"
            value={localFrom}
            max={localTo || undefined}
            onChange={e => setLocalFrom(e.target.value)}
            aria-label="Start date"
          />
          <span className="date-sep">→</span>
          <input
            type="date"
            className="date-input"
            value={localTo}
            min={localFrom || undefined}
            onChange={e => setLocalTo(e.target.value)}
            aria-label="End date"
          />
          <button
            className="period-pill active apply-btn"
            onClick={handleCustomApply}
            disabled={!localFrom || !localTo || localFrom > localTo}
          >
            Apply
          </button>
        </div>
      )}
    </div>
  )
}

export default DateRangeToggle
