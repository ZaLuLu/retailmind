# RetailMind — Upgrade Roadmap
**Created:** 2026-05-19
**Status:** Phase 1 Active

---

## Overview

| Phase | Focus | Status |
|---|---|---|
| Phase 1 | Foundation Fixes (cleanup, token refresh, toasts, error boundary) | ✅ Completed |
| Phase 2 | Core Product Completion (date range, multi-store, forecasting v1, export) | ✅ Completed |
| Phase 3 | ML Layer (z-score anomaly, product clustering, statsmodels forecasting) | ✅ Completed |
| Phase 4 | Distribution & Monetisation (WhatsApp digest, PDF export, Razorpay) | ⏳ Queued |

---

## Phase 1 — Foundation Fixes

**Goal:** Make the existing product solid before adding features. These are blockers.

### 1.1 Legacy Code Removal
**Why:** Dead code creates confusion and maintenance burden.

Files to remove:
- `backend/app/services/intelligence.py`
- `backend/app/api/intelligence.py`
- Remove `Transaction` and `Budget` model classes from `backend/app/models/db.py`
- Remove legacy router registration from `backend/app/main.py`
- Frontend: remove `EvidenceViewer.jsx` (personal finance artifact)

### 1.2 API Client Rewrite (`api.js`)
**Why:** Current client has no token refresh. A 401 mid-session silently logs the user out.

New architecture:
```javascript
// Central request() function
async function request(method, endpoint, data) {
  // 1. Attach token
  // 2. Execute fetch
  // 3. If 401 → refresh → retry once
  // 4. If refresh fails → logout
  // 5. Normalize errors (network vs server vs client)
}
```

All existing methods (`get`, `post`, `patch`, `upload`) become thin wrappers over `request()`.

### 1.3 Toast Notification System
**Why:** `alert()` calls break the premium aesthetic and block the UI thread.

Implementation:
- `useToast()` hook — returns `{ showToast, dismissToast }`
- `ToastContainer` component — fixed bottom-right, max 3 visible, auto-dismiss after 4s
- Toast types: `success`, `error`, `warning`, `info`
- Broadsheet styling: navy background, gold accent border, JetBrains Mono for codes

Replace all `alert()` calls in `App.jsx`:
- `alert('Onboarding failed')` → `showToast('error', 'Onboarding failed. Please try again.')`
- `alert('Upload failed: ' + err.message)` → `showToast('error', err.message)`
- `alert('Failed to update settings')` → `showToast('error', 'Settings update failed.')`

### 1.4 React Error Boundary
**Why:** An unhandled render error currently blanks the entire screen.

Implementation:
- `ErrorBoundary` class component wrapping `<App />`
- Fallback UI: broadsheet-style "Something went wrong" page with reload button
- Log error to Sentry in `componentDidCatch`

---

## Phase 2 — Core Product Completion

**Goal:** Fill the gaps that limit real-world usability.

### 2.1 Date Range Filter
**Why:** MTD-only view is limiting. Owners want to compare periods.

Backend:
- Add `period` query param to `GET /retail/summary`: `7d` | `30d` | `90d` | `custom`
- Add `date_from` and `date_to` params for custom range
- All aggregation queries respect the active date window

Frontend:
- Pill toggle in dashboard header: `7D | 30D | 90D | Custom`
- Custom range shows a date picker
- All chart components re-fetch when period changes

### 2.2 Multi-Store Support
**Why:** The `Store` model already exists. Wiring it up unlocks the CA/accountant use case.

Backend:
- `POST /api/v1/stores` — create store (name, address, category)
- `GET /api/v1/stores` — list user's stores
- Add `store_id` FK to `SaleRecord` (nullable, defaults to user's first store)
- Scope all `/retail/*` queries by `store_id` when provided

Frontend:
- Store selector dropdown in masthead
- Onboarding creates first store on completion
- All dashboard data scoped to selected store

### 2.3 Excel Upload (.xlsx)
**Why:** Most Indian SMBs export from Tally to Excel, not CSV.

Backend:
- Add `openpyxl` to `requirements.txt`
- Detect file extension in `upload_sales_csv` endpoint
- If `.xlsx`: use `openpyxl.load_workbook()` to read, convert to same row dict format
- Same header auto-detect logic applies

### 2.4 Export Sales CSV
**Why:** Owners need to share data with their CA or import into other tools.

Backend:
- `GET /api/v1/retail/export-csv` — accepts same filter params as `/retail/sales`
- Returns CSV with headers: product_name, sku, category, qty, unit_price, revenue, cogs, margin, date, segment

Frontend:
- "Export CSV" button in SalesLedger controls bar
- Respects active search/category filters
- Triggers browser download

### 2.5 Demand Forecasting v1
**Why:** This is the single highest-value feature for SMB owners. Drives purchasing decisions.

Backend:
- `GET /api/v1/retail/forecast` endpoint
- Algorithm: weighted 7-day rolling average per product
  ```python
  weights = [1, 2, 3, 4, 5, 6, 7]  # day -7 to day -1
  forecast_qty = sum(w * qty for w, qty in zip(weights, daily_qtys)) / sum(weights)
  ```
- Returns: product_name, forecast_qty_7d, trend (up/flat/down), confidence (low/medium/high based on data points)

Frontend:
- "Forecast" tab added to DemandSignals panel
- Shows: product name, predicted qty next 7 days, trend arrow, confidence badge
- "Order by" date shown if trend is up and qty is high

---

## Phase 3 — ML Layer

**Goal:** Replace rule-based thresholds with adaptive models. This is the defensible moat.

### 3.1 Z-Score Anomaly Detection
**Why:** The 1.5x hardcoded threshold generates false positives for high-variance products and misses spikes in low-variance ones.

```python
# Per product, rolling 12-week window
mean = statistics.mean(weekly_qtys)
std = statistics.stdev(weekly_qtys)
z_score = (current_week_qty - mean) / std if std > 0 else 0
is_spike = z_score > 2.0  # ~95th percentile
```

Requires minimum 4 weeks of data per product to activate. Falls back to 1.5x rule otherwise.

### 3.2 Product Clustering (K-Means)
**Why:** Owners need a simple mental model for their portfolio. Stars/Cash Cows/Dead Weight/Hidden Gems is immediately actionable.

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

features = ['revenue_norm', 'margin_pct', 'qty_norm', 'days_since_last_sale']
# Normalize, fit KMeans(k=4), assign cluster labels
# Map clusters to quadrant names based on centroid positions
```

Frontend: 2×2 scatter matrix on dashboard. Click a quadrant to filter the product table.

### 3.3 Demand Forecasting v2 (Statsmodels Holt-Winters)
**Why:** Rolling average doesn't handle seasonality (e.g., weekends). Holt-Winters Exponential Smoothing does, and is lightweight enough for Vercel serverless deployment.

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Per product with 90+ days of data
model = ExponentialSmoothing(daily_qtys, seasonal_periods=7, trend='add', seasonal='add')
fit_model = model.fit()
forecast = fit_model.forecast(14)
# Return forecast for next 14 days
```

Activates automatically when a product has 90+ days of history.

### 3.4 Customer Segment Analytics
**Why:** The `customer_segment` field (Walk-in/Online/B2B) is already being captured but never analyzed.

Backend:
- Add segment breakdown to `/retail/summary`: revenue, margin, avg_order_value per segment
- Add MoM segment trend

Frontend:
- New "Segments" section in dashboard
- Bar chart: revenue by segment
- Table: segment × metric matrix

---

## Phase 4 — Distribution & Monetisation

**Goal:** Turn the product into a business.

### 4.1 WhatsApp Weekly Digest
**Why:** SMB owners check WhatsApp 50x/day. They don't check dashboards.

- Twilio WhatsApp Business API
- Weekly cron job (Monday 9am IST)
- Message format:
  ```
  📊 RetailMind Weekly — Sharma Retail & Co.
  Revenue: ₹4.8L (+12% vs last week)
  Top alert: Sony XM5 demand spike (3.2x)
  Dead stock: 3 items need attention
  View full report: [link]
  ```
- User opt-in in Settings with phone number field

### 4.2 PDF Report Export
**Why:** Owners share monthly summaries with their CA or business partner.

- `GET /api/v1/retail/report/pdf` using `weasyprint`
- Broadsheet-style layout: masthead, KPI strip, top products table, alerts summary
- "Share with CA" button triggers download
- Print-optimized CSS (black and white, no backgrounds)

### 4.3 Razorpay Billing
**Why:** Monetisation. ₹799/month is the right price for Indian SMBs.

Plan gating:
| Feature | Free | Pro (₹799/mo) |
|---|---|---|
| Data history | 90 days | Unlimited |
| Forecasting | ❌ | ✅ |
| PDF export | ❌ | ✅ |
| Multi-store | 1 store | Unlimited |
| WhatsApp digest | ❌ | ✅ |

Implementation:
- Add `plan` field to `User` model (`free` / `pro`)
- Add `plan_expires_at` datetime field
- Razorpay checkout with UPI support (5-minute integration)
- Webhook to update `plan` on payment success

---

## Go-To-Market Strategy

### Target Segments (Priority Order)
1. **Electronics retailers** — High SKU count, high margin variance, most need for dead stock alerts
2. **Apparel shops** — Seasonal demand, need forecasting for festival stock
3. **FMCG distributors** — High volume, need margin erosion detection

### Distribution Channels
1. **Direct SMB outreach** — WhatsApp groups, local business associations, Indiamart seller communities
2. **CA/Accountant channel** — One CA brings 20-50 clients. Build "share with CA" feature first.
3. **Tally integration** — 90% of Indian SMBs use Tally. Import Tally exports = zero friction onboarding.

### Demo Strategy
- 2-minute screen recording: "upload your Excel → see your insights"
- Use the seed data with intentional dead stock + margin erosion scenarios
- The "aha moment" is when the owner sees a product they forgot about flagged as dead stock

### Pricing Rationale
- ₹799/month = less than one hour of a CA's time
- Free tier with 90 days data is enough to demonstrate value
- UPI payment removes friction for Indian users
