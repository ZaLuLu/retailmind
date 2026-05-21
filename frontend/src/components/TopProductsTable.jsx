import React, { useState } from 'react'

import { formatMoneyCompact } from '../services/currency'

const SORT_KEYS = ['revenue', 'margin_pct', 'quantity']
const SORT_LABELS = { revenue: 'Revenue', margin_pct: 'Margin %', quantity: 'Qty Sold' }

const TopProductsTable = ({ products = [], currency = 'INR' }) => {
  const [sortKey, setSortKey] = useState('revenue')
  const [sortDir, setSortDir] = useState('desc')

  const sorted = [...products].sort((a, b) => {
    const diff = (a[sortKey] ?? 0) - (b[sortKey] ?? 0)
    return sortDir === 'desc' ? -diff : diff
  })

  const handleSort = (key) => {
    if (key === sortKey) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const maxRevenue = Math.max(...products.map(p => p.revenue || 0), 1)

  const marginColor = (pct) => {
    if (pct >= 40) return '#4CAF50'
    if (pct >= 25) return '#C9A84C'
    return '#E57373'
  }

  return (
    <section className="top-products">
      <div className="section-kicker">
        <span className="kicker-label">Top Products</span>
        <div className="kicker-line" />
        <div className="sort-controls">
          {SORT_KEYS.map(k => (
            <button
              key={k}
              className={`sort-btn ${sortKey === k ? 'active' : ''}`}
              onClick={() => handleSort(k)}
            >
              {SORT_LABELS[k]} {sortKey === k ? (sortDir === 'desc' ? '↓' : '↑') : ''}
            </button>
          ))}
        </div>
      </div>

      {products.length === 0 ? (
        <p className="empty-state">No product data yet. Upload a CSV to get started.</p>
      ) : (
        <div className="products-table">
          <div className="products-table-header">
            <span>Product</span>
            <span>Category</span>
            <span>Revenue</span>
            <span>Qty</span>
            <span>Margin</span>
          </div>
          {sorted.map((p, i) => (
            <div className="products-row" key={`${p.product_name}-${i}`}>
              <div className="product-cell">
                <span className="product-rank">#{i + 1}</span>
                <span className="product-name">{p.product_name}</span>
              </div>
              <span className="product-category-badge">{p.category}</span>
              <div className="revenue-cell">
                <span className="revenue-value">{formatMoneyCompact(p.revenue, currency)}</span>
                <div className="revenue-bar-track">
                  <div
                    className="revenue-bar-fill"
                    style={{ width: `${(p.revenue / maxRevenue) * 100}%` }}
                  />
                </div>
              </div>
              <span className="qty-cell">{p.quantity.toFixed(0)}</span>
              <div className="margin-cell">
                <span
                  className="margin-badge"
                  style={{ color: marginColor(p.margin_pct), borderColor: marginColor(p.margin_pct) }}
                >
                  {p.margin_pct.toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default TopProductsTable
