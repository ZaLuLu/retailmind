# RetailMind — Feature Log
**Tracks completed, in-progress, and planned features**
**Last Updated:** 2026-05-19

---

## ✅ Completed (v2.1.0)

### Core Analytics
- [x] RetailIntelligenceService with full analytics engine
- [x] `/retail/summary` endpoint (revenue KPIs, top products, signals, AI insight)
- [x] `/retail/sales` paginated ledger endpoint
- [x] `/retail/upload-csv` with auto-detect header mapping (15+ aliases)
- [x] `/retail/template-csv` download endpoint
- [x] Demand spike detection (7d vs 30d weekly avg, ≥1.5x threshold)
- [x] Dead stock alerts (no sales in 30d, had prior sales in 31–90d window)
- [x] Margin erosion alerts (avg margin < 20%, min 2 records)
- [x] Gemini AI one-liner insight (FT-headline style)

### Frontend
- [x] RevenueHero KPI strip (Revenue, GP, Margin %, MoM)
- [x] TopProductsTable sortable leaderboard (Revenue / Margin / Qty)
- [x] DemandSignals tabbed panel (Spikes / Dead Stock / Margin Erosion)
- [x] SalesLedger with search, category filter, pagination
- [x] SalesTrendGraph — pure SVG daily trend + category COGS comparison
- [x] Retail-domain AdvisorChat (Gemini, scoped to retail metrics)
- [x] Currency selector in Settings (INR, USD, EUR, GBP, AED)
- [x] INR compact notation (L, Cr)
- [x] OnboardingWizard — store name, category targets, currency picker, demo shortcut
- [x] Full broadsheet CSS design system (navy + gold, Playfair + JetBrains Mono)

### Infrastructure
- [x] 220+ demo retail seed records with intentional anomalies
- [x] JWT auth with access + refresh tokens
- [x] Sentry error tracking
- [x] PostgreSQL on Neon.tech (prod)

---

## 🔧 Phase 1 — Foundation Fixes (Current Sprint)

### Cleanup
- [x] Remove legacy `intelligence.py` and `documents.py` router registrations from `main.py`
- [x] Mark `Transaction` and `Budget` models as LEGACY in `db.py`
- [x] Add `store_id` FK to `SaleRecord` (nullable, Phase 2 readiness)
- [x] Delete `app/api/intelligence.py` and `app/api/documents.py` files
- [x] Delete `app/services/intelligence.py` file

### API Client Hardening
- [x] Rewrite `api.js` with central `request()` interceptor
- [x] Implement automatic token refresh on 401 (retry original request after refresh)
- [x] Queue concurrent requests during refresh to prevent race conditions
- [x] Clear tokens and dispatch `auth:logout` event on refresh failure

### UX Fixes
- [x] Replace all `alert()` calls in `App.jsx` with `useToast()`
- [x] Build `useToast` hook + `ToastProvider` + `ToastContainer` component
- [x] Add React global error boundary (`ErrorBoundary.jsx`)
- [x] Wire `auth:logout` event listener in `App.jsx` for forced session expiry
- [x] Disable submit buttons while requests are in-flight (prevent duplicate submissions)

---

## 🔧 Phase 2 — Core Product Completion

### Date Range Filtering
- [x] Add `period` query param to `/retail/summary` (`7d` / `30d` / `90d` / `custom`)
- [x] Wire date range toggle to frontend dashboard header
- [x] Update all chart components to respect active date range

### Multi-Store Support
- [x] Wire up existing `Store` model — add `POST /stores`, `GET /stores` endpoints
- [x] Add store selector to masthead
- [x] Scope all `SaleRecord` queries by `store_id`
- [x] Update onboarding to create first store on completion

### File Upload Improvements
- [x] Add `openpyxl` support for `.xlsx` direct upload (no manual CSV export needed)
- [x] Add file size validation on frontend before upload (max 10MB)
- [x] Show per-file upload progress indicator

### Export
- [x] `GET /retail/export-csv` — download filtered ledger as CSV
- [x] Export button in SalesLedger respecting active search/category filters

### Demand Forecasting v1
- [x] `GET /retail/forecast` endpoint — weighted 7-day rolling average per product
- [x] Return: predicted qty next 7 days, trend direction, "order by" date suggestion
- [x] Add "Forecast" tab to DemandSignals panel alongside Spikes/Dead Stock/Margin

---

## 🔧 Phase 3 — ML Layer

### Anomaly Detection Upgrade
- [/] Replace hardcoded 1.5x spike threshold with per-product z-score model
- [/] Adapts to each product's natural variance (fewer false positives)
- [/] Handles seasonality via rolling window normalization

### Product Clustering
- [/] K-means clustering on (revenue, margin_pct, qty_sold, days_since_last_sale)
- [/] Auto-segment products: Stars / Cash Cows / Dead Weight / Hidden Gems
- [/] 2×2 matrix visualization on dashboard

### Demand Forecasting v2
- [/] Swap rolling average for statsmodels Holt-Winters Exponential Smoothing per-product model
- [/] Handles weekly seasonality automatically
- [/] Return 14-day forecast
- [/] Requires 90+ days of data per product to activate

### Customer Segment Analytics
- [/] Break down Walk-in vs Online vs B2B performance
- [/] Revenue, margin, and avg order value per segment
- [/] Segment trend over time (MoM per segment)

---

## 🔧 Phase 4 — Distribution & Monetisation

### WhatsApp Weekly Digest
- [ ] Twilio WhatsApp Business API integration
- [ ] Weekly summary message: revenue, top alert, dead stock count
- [ ] User opt-in in Settings with phone number field

### PDF Report Export
- [ ] `GET /retail/report/pdf` endpoint using weasyprint
- [ ] Broadsheet-style monthly summary PDF
- [ ] "Share with CA" one-click download

### Razorpay Billing
- [ ] Add `plan` field to User model (`free` / `pro`)
- [ ] Free tier: 90 days history, no forecasting, no PDF
- [ ] Pro tier (₹799/month): unlimited history, forecasting, PDF, multi-store
- [ ] Razorpay checkout with UPI support

---

## 💡 Backlog / Future

- [ ] **Inventory integration** — Link sales to stock levels, auto-flag reorder points
- [ ] **Price elasticity hints** — Suggest price adjustments based on margin + velocity
- [ ] **Multi-user teams** — Role-based access (owner, manager, analyst)
- [ ] **Mobile PWA** — Install-to-homescreen for SMB owners on mobile
- [ ] **Barcode scanner** — Scan product barcodes to log sales via mobile camera
- [ ] **Tally integration** — Import Tally exports directly
- [ ] **B2B customer analytics** — Separate B2B vs retail performance tracking
