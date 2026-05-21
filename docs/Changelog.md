# RetailMind — Changelog
**Format:** Most recent first

---

## [3.0.0] — 2026-05-19 · Phase 1 Foundation Fixes

### 🧹 Cleanup
- Removed legacy `documents` and `intelligence` router registrations from `main.py`
- Marked `Transaction` and `Budget` models as LEGACY in `db.py`
- Added `store_id` FK to `SaleRecord` (nullable, Phase 2 multi-store readiness)
- API version bumped to `3.0.0`

### 🔧 API Client Rewrite (`api.js`)
- Central `request()` interceptor with automatic token refresh on 401
- Request queuing during refresh (prevents race conditions on concurrent requests)
- Forced logout via `auth:logout` custom event when refresh token is expired
- Structured error normalization: network errors, server errors (500), client errors (4xx)
- All methods (`get`, `post`, `patch`, `delete`, `uploadFile`) route through interceptor
- Added `getRetailForecast()` and `getExportCsvUrl()` stubs for Phase 2

### 🍞 Toast Notification System
- New `Toast.jsx` — `ToastProvider` + `useToast()` hook
- Types: `success`, `error`, `warning`, `info`
- Max 3 visible, auto-dismiss after 4s, broadsheet navy + gold styling
- Replaced all `alert()` calls in `App.jsx` with `showToast()`
- Session expiry shows `warning` toast before redirecting to login

### 🛡️ Error Boundary
- New `ErrorBoundary.jsx` — class component wrapping entire app
- Broadsheet-style fallback UI with "Reload Page" and "Try Again" actions
- Logs to Sentry via `window.Sentry.captureException` if available

### 📋 Docs Updated
- All 6 docs rewritten: Project_Context, Architecture, Feature_Log, Coding_Rules, Changelog
- New `Roadmap.md` with full 4-phase upgrade plan and go-to-market strategy

---

## [2.1.0] — 2026-05-19 · Business Graphing & Scoped Advisor Chat

### 🚀 New Features
- **`SalesTrendGraph.jsx`**: Pure SVG-based newspaper-style data analytics graphing
  - Line/Area Sales Trend (MTD): dynamic scaling, bezier lines, broadsheet fills
  - Revenue vs COGS Comparison: grouped category bar graphs
  - Hoverable tooltips with currency-aware formatting

### ♻️ Modified
- **`gemini.py`**: Gemini prompt guardrails scoped strictly to retail metrics
- **`App.css`**: Chat bubble redesign — navy user bubbles, gold-accented sand advisor cards
- **`IntelligenceDashboard.jsx`**: SalesTrendGraph mounted at top of briefing column

---

## [2.0.0] — 2026-05-19 · RetailMind Overhaul

### 🚀 New Features
- **RetailIntelligenceService** (`services/retail_intelligence.py`)
  - Revenue KPIs: total_revenue, total_cogs, gross_profit, overall_margin_pct
  - MoM revenue change calculation
  - Top 5 products by revenue with avg margin
  - Category performance breakdown (revenue + margin per category)
  - Demand spike detection: 7-day qty vs 30-day weekly average (spike at ≥1.5x)
  - Dead-stock alerts: products with sales 31-90 days ago but none in last 30 days
  - Margin erosion alerts: products with blended margin < 20% (min 2 records)
  - Gemini AI one-liner insight (FT-headline style)
- **`/retail` API Router** (`api/retail.py`)
  - `GET /retail/summary` — full BI summary
  - `GET /retail/sales` — paginated sale records
  - `POST /retail/upload-csv` — CSV upload with auto-detect header mapping
  - `GET /retail/template-csv` — downloadable CSV template
- **`RevenueHero.jsx`** — 4-KPI broadsheet stat block
- **`TopProductsTable.jsx`** — sortable product leaderboard with revenue bars + margin badges
- **`DemandSignals.jsx`** — tabbed alerts panel (Demand Spikes / Dead Stock / Margin Alert)
- **`SalesLedger.jsx`** — full ledger with search, category filter, pagination
- **CSV auto-detect** — maps 15+ common column name aliases to canonical fields
- **Currency selector** — user can set INR / USD / EUR / GBP / AED in Settings
- **INR compact notation** — values render as ₹4.8L, ₹1.2Cr etc.
- **Retail demo seeder** — 220+ sale records across 5 categories with dead-stock, spike, and margin-erosion scenarios

### ♻️ Modified
- `IntelligenceDashboard.jsx` — full rewrite for RetailMind layout
- `IntelligenceDashboard.css` — full rewrite: deep navy + gold broadsheet palette
- `App.jsx` — rewired to `getRetailSummary` + `getRetailSales`; inline SettingsForm with currency picker
- `api.js` — added `getRetailSummary`, `getRetailSales`, `uploadSalesCsv`, `getTemplateCsvUrl`
- `AdvisorChat.jsx` — domain updated to retail
- `seed_demo.py` — completely replaced with retail SaleRecord seeder
- `main.py` — retail router registered; API title updated to RetailMind v2.0.0

### 🗄️ Preserved (Backward Compat — Removal in Phase 1)
- `Transaction`, `Budget` models kept in `db.py`
- Legacy `/intelligence/summary` endpoint kept but not used by frontend

---

## [1.5.0] — 2026-05-18 · Retail Intelligence Bulletin (Pivot)

- Pivoted product from personal finance to retail BI
- Added `SaleRecord` and `Store` models to `db.py`
- Editorial broadsheet aesthetic (newspaper Serif design)

---

## [1.3.0] — 2026-05-18 · Newspaper/Broadsheet UI

- Newspaper broadsheet design system (Playfair Display)
- Masthead, section kickers, column rules
- Stripped Neo-Brutalist heavy borders

---

## [1.2.0] — 2026-05-17 · Neo-Brutalist Design + Portfolio Demo

- Neo-Brutalist design identity
- 500+ Kaggle-style personal finance transactions (seeded)
- Guest/Demo mode

---

## [1.0.0] — 2026-05-13 · Initial Launch

- FastAPI backend with JWT auth
- Gemini AI receipt scanning (OCR)
- Monthly budget tracking and anomaly detection
- Personal finance ledger with category breakdown
- React frontend with onboarding wizard
