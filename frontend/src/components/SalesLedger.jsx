import React, { useState, useCallback } from 'react'
import { formatMoneyDetailed } from '../services/currency'
import { api } from '../services/api'
import { useToast } from './Toast'

const marginColor = (pct) => {
  if (pct == null) return 'inherit'
  if (pct >= 40) return '#4CAF50'
  if (pct >= 20) return '#C9A84C'
  return '#E57373'
}

// Build categories dynamically from sales data + always include 'All'
const getCategories = (sales) => {
  const cats = [...new Set(sales.map(s => s.product_category).filter(Boolean))]
  return ['All', ...cats.sort()]
}

const SalesLedger = ({ sales = [], currency = 'INR', onBack, initialProductNames = null }) => {
  const { showToast } = useToast()
  const [search, setSearch]               = useState('')
  const [categoryFilter, setCategoryFilter] = useState('All')
  const [dateFrom, setDateFrom]           = useState('')
  const [dateTo, setDateTo]               = useState('')
  const [productNamesFilter, setProductNamesFilter] = useState(initialProductNames)
  const [sortCol, setSortCol]             = useState('sale_date')
  const [sortDir, setSortDir]             = useState('desc')
  const [page, setPage]                   = useState(0)
  const [exporting, setExporting]         = useState(false)
  const PAGE_SIZE = 20

  React.useEffect(() => {
    setProductNamesFilter(initialProductNames)
  }, [initialProductNames])

  const categories = getCategories(sales)

  // ── Client-side filtering ──────────────────────────────────────────────────
  const filtered = sales.filter(s => {
    const q = search.toLowerCase()
    const matchSearch = !q || (
      s.product_name?.toLowerCase().includes(q) ||
      s.product_sku?.toLowerCase().includes(q)
    )
    const matchCat = categoryFilter === 'All' || s.product_category === categoryFilter
    const matchFrom = !dateFrom || s.sale_date >= dateFrom
    const matchTo   = !dateTo   || s.sale_date <= dateTo
    const matchProductNames = !productNamesFilter || productNamesFilter.includes(s.product_name)
    return matchSearch && matchCat && matchFrom && matchTo && matchProductNames
  })

  // ── Sorting ────────────────────────────────────────────────────────────────
  const sorted = [...filtered].sort((a, b) => {
    let av = a[sortCol], bv = b[sortCol]
    if (sortCol === 'total_revenue' || sortCol === 'quantity_sold') {
      av = Number(av); bv = Number(bv)
    }
    if (av < bv) return sortDir === 'asc' ? -1 : 1
    if (av > bv) return sortDir === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
    setPage(0)
  }

  const sortIcon = (col) => {
    if (sortCol !== col) return <span className="sort-icon muted" aria-hidden="true">↕</span>
    return <span className="sort-icon" aria-hidden="true">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const paginated  = sorted.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE)

  // ── Export CSV ─────────────────────────────────────────────────────────────
  const handleExport = useCallback(async () => {
    if (filtered.length === 0) return
    setExporting(true)
    try {
      // Build query params matching active filters
      const params = new URLSearchParams()
      if (search)         params.set('search', search)
      if (categoryFilter !== 'All') params.set('category', categoryFilter)
      if (dateFrom)       params.set('date_from', dateFrom)
      if (dateTo)         params.set('date_to', dateTo)

      const url = api.getExportCsvUrl(params.toString() ? `?${params}` : '')
      const token = localStorage.getItem('token')
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Export failed')

      const blob = await res.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `retailmind_export_${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(link.href)
      showToast('success', `Exported ${filtered.length} records.`)
    } catch (err) {
      showToast('error', err.message || 'Export failed.')
    } finally {
      setExporting(false)
    }
  }, [filtered, search, categoryFilter, dateFrom, dateTo, showToast])

  const resetFilters = () => {
    setSearch('')
    setCategoryFilter('All')
    setDateFrom('')
    setDateTo('')
    setProductNamesFilter(null)
    setPage(0)
  }

  const hasActiveFilters = search || categoryFilter !== 'All' || dateFrom || dateTo || productNamesFilter

  return (
    <div className="sales-ledger">

      {/* ── Header ── */}
      <div className="ledger-header">
        <div className="section-kicker">
          <span className="kicker-label">
            Sales Ledger
            <span className="ledger-count mono"> · {filtered.length} records</span>
          </span>
          <div className="kicker-line" />
        </div>
        <div className="ledger-header-actions">
          <button
            className="mono-btn export-btn"
            onClick={handleExport}
            disabled={filtered.length === 0 || exporting}
            title={filtered.length === 0 ? 'No data to export' : `Export ${filtered.length} records as CSV`}
            aria-label="Export filtered records as CSV"
          >
            {exporting ? '⏳ Exporting…' : '↓ Export CSV'}
          </button>
          <button className="mono-btn" onClick={onBack}>← Briefing</button>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="ledger-filters">
        <div className="ledger-filters-row">
          <input
            className="ledger-search"
            type="text"
            placeholder="Search product or SKU…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0) }}
            aria-label="Search products"
          />
          <div className="ledger-date-range">
            <input
              type="date"
              className="date-input"
              value={dateFrom}
              max={dateTo || undefined}
              onChange={e => { setDateFrom(e.target.value); setPage(0) }}
              aria-label="Filter from date"
            />
            <span className="date-sep mono">→</span>
            <input
              type="date"
              className="date-input"
              value={dateTo}
              min={dateFrom || undefined}
              onChange={e => { setDateTo(e.target.value); setPage(0) }}
              aria-label="Filter to date"
            />
          </div>
          {hasActiveFilters && (
            <button className="mono-btn clear-btn" onClick={resetFilters} aria-label="Clear all filters">
              ✕ Clear
            </button>
          )}
          {productNamesFilter && (
            <span className="telex-stamp-badge red-stamp mono" style={{ alignSelf: 'center', margin: '0 0 0 1rem' }}>
              Quadrant filter active ({productNamesFilter.length} products)
            </span>
          )}
        </div>

        <div className="category-filters">
          {categories.map(cat => (
            <button
              key={cat}
              className={`cat-filter-btn ${categoryFilter === cat ? 'active' : ''}`}
              onClick={() => { setCategoryFilter(cat); setPage(0) }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* ── Table ── */}
      <div className="ledger-table-wrap">
        <table className="ledger-table">
          <thead>
            <tr>
              <th
                onClick={() => handleSort('sale_date')}
                className="sortable-th"
                aria-sort={sortCol === 'sale_date' ? sortDir : 'none'}
              >
                Date {sortIcon('sale_date')}
              </th>
              <th
                onClick={() => handleSort('product_name')}
                className="sortable-th"
                aria-sort={sortCol === 'product_name' ? sortDir : 'none'}
              >
                Product {sortIcon('product_name')}
              </th>
              <th>SKU</th>
              <th>Category</th>
              <th
                onClick={() => handleSort('quantity_sold')}
                className="sortable-th"
                aria-sort={sortCol === 'quantity_sold' ? sortDir : 'none'}
              >
                Qty {sortIcon('quantity_sold')}
              </th>
              <th>Unit Price</th>
              <th
                onClick={() => handleSort('total_revenue')}
                className="sortable-th"
                aria-sort={sortCol === 'total_revenue' ? sortDir : 'none'}
              >
                Revenue {sortIcon('total_revenue')}
              </th>
              <th>COGS</th>
              <th>Margin %</th>
              <th>Segment</th>
            </tr>
          </thead>
          <tbody>
            {paginated.length === 0 ? (
              <tr>
                <td colSpan={10} className="ledger-empty">
                  {sales.length === 0
                    ? 'No sales data. Upload a CSV or Excel file to get started.'
                    : 'No results match your filters.'}
                </td>
              </tr>
            ) : (
              paginated.map(s => (
                <tr key={s.id} className="ledger-row">
                  <td className="mono">{s.sale_date}</td>
                  <td className="product-cell-ledger">{s.product_name}</td>
                  <td className="mono sku-cell">{s.product_sku || '—'}</td>
                  <td><span className="cat-chip">{s.product_category}</span></td>
                  <td className="mono">{s.quantity_sold}</td>
                  <td className="mono">{formatMoneyDetailed(s.unit_price, currency)}</td>
                  <td className="mono revenue-col">{formatMoneyDetailed(s.total_revenue, currency)}</td>
                  <td className="mono">{s.cogs != null ? formatMoneyDetailed(s.cogs, currency) : '—'}</td>
                  <td>
                    {s.gross_margin != null ? (
                      <span className="margin-pct-cell" style={{ color: marginColor(s.gross_margin) }}>
                        {s.gross_margin.toFixed(1)}%
                      </span>
                    ) : '—'}
                  </td>
                  <td>{s.customer_segment || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ── */}
      {totalPages > 1 && (
        <div className="ledger-pagination">
          <button
            className="mono-btn"
            disabled={page === 0}
            onClick={() => setPage(p => p - 1)}
            aria-label="Previous page"
          >
            ← Prev
          </button>
          <span className="mono">
            Page {page + 1} / {totalPages} &nbsp;·&nbsp; {filtered.length} records
          </span>
          <button
            className="mono-btn"
            disabled={page >= totalPages - 1}
            onClick={() => setPage(p => p + 1)}
            aria-label="Next page"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}

export default SalesLedger
