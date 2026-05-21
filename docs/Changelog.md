# RetailMind — Changelog
**Format:** Most recent first

---

## [3.2.0] — 2026-05-21 · Phase 3 ML Layer Complete

### 🤖 Adaptive Z-Score Anomaly Engine
- Replaced the hardcoded `1.5×` demand spike threshold with a **per-product adaptive Z-score model** using a rolling 12-week window of historical volumes.
- Anomaly is flagged when `Z > 2.0` (≈95th percentile of natural product volatility).
- Graceful fallback to rolling average for products with `< 4 active weeks` of data or `σ ≤ 0.1`.
- Frontend `DemandSignals.jsx` updated to render Z-score and deviation % alongside each spike alert.

### 📊 K-Means Product Portfolio Clustering
- Implemented `sklearn.cluster.KMeans(n_clusters=4)` clustering over 4 normalized features: **Revenue, Gross Margin %, Velocity, Recency** (using `StandardScaler`).
- K-Means centroids auto-mapped to four business quadrants: **🌟 Stars**, **💎 Hidden Gems**, **🐄 Cash Cows**, **🪨 Dead Weight**.
- New API endpoint: `GET /api/v1/retail/portfolio-clusters` returning product nodes with SVG coordinates and cluster assignments.
- New component: **`PortfolioMatrix.jsx`** — interactive 2×2 SVG scatter grid with broadsheet double-ruled axes, hoverable Courier typewriter tooltips, and click-to-filter ledger integration.
- `PortfolioMatrix.css` — newspaper quadrant background styles with halftone fills.

### 📈 Holt-Winters Seasonal Forecasting
- Upgraded demand forecasting from weighted rolling average to **statsmodels `ExponentialSmoothing`** with additive trend and additive weekly seasonality (`seasonal_periods=7`).
- Forecasts **14 days** into the future for products with ≥ 90 days of dense history (≥ 15 active days).
- Dense time-series reconstruction: fills missing sale days with `0.0` to preserve continuity.
- Defensive fallback to rolling average for products with insufficient history.
- 14-day store-level aggregate revenue forecast exposed via `summary.revenue_forecast_14d`.
- `SalesTrendGraph.jsx` updated to render dashed forecast path with halftone shade projection area.

### 👥 Customer Segment Analytics
- SQL group-by aggregations by `customer_segment` (Walk-in / Online / B2B) computing:
  - Revenue & COGS totals, blended margin %, AOV (`revenue / num_orders`), contribution share %, MoM growth.
- New component: **`CustomerSegmentsPanel.jsx`** — vintage broadsheet ledger panel with progress bars per segment and telex-stamped metric cards.
- Mounted on dashboard sidebar below Demand Signals.

### 🧪 Automated Test Suite
- Created `backend/scripts/test_ml_layer.py` — 165-record seeded isolated test against live PostgreSQL.
- **Test Case A (Z-Score):** Z-spike, high-variance fallback, and rolling-average fallback — all passing.
- **Test Case B (K-Means):** All 4 quadrants assigned, coordinates clamped `[-2.5, 2.5]`, metric structure verified.
- **Test Case C (Holt-Winters):** Dense product uses holt-winters, valid 14-day store forecast — passing.
- **Test Case D (Segments):** 3 segments present, shares sum to 100%, AOV & margin formulas correct — passing.
- **All 4 test cases GREEN ✅**

### 📦 Dependencies Added
- `statsmodels==0.14.6` — Holt-Winters exponential smoothing
- `scikit-learn==1.8.0` — KMeans clustering and StandardScaler

---


### 🎨 Visual & Typography
- Added Google Fonts calligraphic blackletter **UnifrakturMaguntia** to the main `RetailMind` masthead logo.
- Added a tactile physical broadsheet paper fold crease overlay on `#root` via custom linear-gradients.
- Added printed hatch and halftone pattern utility classes (`.hatch-bg`, `.halftone-bg`).
- Configured a golddropped capital initial letter drop-cap style on the main dashboard highlights `.insight-quote`.
- Implemented authentic printed broadsheet double rules.
- Hardened page SEO: updated index title to `RetailMind — Store Analytics Ledger` and added clear meta tags.

### 📈 Lively SVG Charts & Donut View
- Added a third chart visualization: **Category Share** custom SVG Donut chart, showing relative percentage contributions of store revenue.
- Added smooth keyframe animations to trend lines (`drawPath` drawing effect) and bar charts (`riseBar` vertical transition) for high visual feedback.
- Configured interactive hover tags and tooltips detailing category margins on segment hovers.

### 📠 Telex Telegram chat
- Redesigned the AI Advisor overlay as an authentic, heavy-bordered **Confidential Telex Telegram Dispatch Desk** using monospace Courier.
- Formatted messages as simulated Courier print paper tape strips with dotted borders.

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
