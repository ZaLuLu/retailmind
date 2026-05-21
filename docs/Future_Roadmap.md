# RetailMind — Future Roadmap
**Created:** 2026-05-21
**Status:** Phases 1–3 Complete. This document outlines all planned future phases.

> Phases 1–3 are complete. This document tracks everything **beyond** the current build — the path from prototype to production SaaS.

---

## Phase Summary

| Phase | Focus | Priority | Estimated Effort |
|---|---|---|---|
| Phase 4 | Distribution & Monetisation | 🔴 High | 3–4 weeks |
| Phase 5 | Mobile-First PWA & Responsive Overhaul | 🔴 High | 2–3 weeks |
| Phase 6 | Advanced Analytics & AI | 🟡 Medium | 4–6 weeks |
| Phase 7 | Integrations & Ecosystem | 🟢 Low | Ongoing |

---

## Phase 4 — Distribution & Monetisation

**Goal:** Turn RetailMind into a revenue-generating product. This is the bridge between a great demo and a real business.

---

### 4.1 WhatsApp Weekly Digest
**Why:** Indian SMB owners check WhatsApp 50× per day. They do not check dashboards. Meeting them where they live is the highest-leverage distribution play available.

**Implementation:**
- Twilio WhatsApp Business API integration in `backend/app/services/whatsapp.py`
- Weekly cron job running Monday 9:00 AM IST via `APScheduler` or `Celery Beat`
- Message format (example):
  ```
  📊 RetailMind Weekly — Sharma Retail & Co.
  Week ending 19 May 2026

  Revenue: ₹4.8L (+12% vs last week)
  Top Spike: Sony XM5 — 3.2× demand surge
  Dead Stock: 3 items need attention
  Portfolio: 6 Stars · 4 Cash Cows · 2 Hidden Gems

  View full report → [link]
  Reply STOP to unsubscribe
  ```
- User opt-in via Settings page with phone number field
- `User` model: add `whatsapp_number` (str, nullable) and `whatsapp_opt_in` (bool)
- New endpoint: `POST /api/v1/user/whatsapp-optin`

**Files to Create/Modify:**
- `backend/app/services/whatsapp.py` (new)
- `backend/app/api/notifications.py` (new)
- `backend/app/models/db.py` — add whatsapp fields to User
- `frontend/src/components/Settings.jsx` — add opt-in UI

---

### 4.2 PDF Intelligence Report
**Why:** Owners share monthly summaries with their CA or business partner. The PDF is the physical artifact that proves value.

**Implementation:**
- `GET /api/v1/retail/report/pdf` endpoint using `weasyprint`
- Broadsheet-style layout faithful to the dashboard:
  - Masthead with store name and report period
  - 4-KPI revenue hero strip
  - Top Products table with margin bars
  - Portfolio quadrant text summary (not SVG — print-compatible)
  - Demand Signals summary (top 5 alerts)
  - 14-day forecast table
  - Customer segment breakdown
  - AI insight quote
- Print-optimised CSS: black-on-white, no backgrounds, serif typography
- "Download Report" button in dashboard header
- "Share with CA" generates a direct download link with time-limited token

**Files to Create/Modify:**
- `backend/app/services/pdf_report.py` (new)
- `backend/app/api/retail.py` — add `/report/pdf` route
- `backend/app/templates/report.html` (new — Jinja2 template for weasyprint)
- `frontend/src/components/IntelligenceDashboard.jsx` — add Download Report button

---

### 4.3 Razorpay Billing & Plan Gating
**Why:** Monetisation. ₹799/month is less than one hour of a CA's time — this is the right price anchor for Indian SMBs.

**Plan Structure:**

| Feature | Free | Pro (₹799/mo) |
|---|---|---|
| Sales history | 90 days | Unlimited |
| Stores | 1 | Unlimited |
| ML Forecasting | ❌ | ✅ |
| Portfolio Matrix | ❌ | ✅ |
| PDF Export | ❌ | ✅ |
| WhatsApp Digest | ❌ | ✅ |
| AI Advisor | 10 queries/day | Unlimited |

**Implementation:**
- `User` model: add `plan` (enum: `free` / `pro`), `plan_expires_at` (datetime)
- `GET /api/v1/billing/create-order` — Razorpay order creation
- `POST /api/v1/billing/webhook` — payment success webhook updates plan
- UPI support enabled by default (Razorpay handles this)
- Feature gating middleware: `backend/app/core/plan_guard.py`
- Frontend: Upgrade prompt modal shown when free-tier user attempts a Pro feature

**Files to Create/Modify:**
- `backend/app/services/billing.py` (new)
- `backend/app/api/billing.py` (new)
- `backend/app/core/plan_guard.py` (new)
- `backend/app/models/db.py` — add plan fields to User
- `frontend/src/components/UpgradePrompt.jsx` (new)

---

## Phase 5 — Mobile-First PWA & Responsive Overhaul

**Goal:** The dashboard was designed desktop-first. Indian SMB owners primarily use mobile. This phase makes RetailMind a genuine mobile tool.

---

### 5.1 Responsive Layout Overhaul
**Why:** The current two-column briefing grid breaks on screens < 900px.

**Implementation:**
- Audit all CSS grid layouts in `IntelligenceDashboard.css`
- Convert `briefing-grid` to single-column stack below 768px breakpoint
- Make `SalesTrendGraph` SVG dynamically resize via `ResizeObserver`
- Collapse `PortfolioMatrix` SVG to full-width single panel on mobile
- Add `overflow-x: scroll` container to `TopProductsTable` on small screens
- Touch-friendly nav: replace pill nav bar with a bottom tab bar on mobile

**Files to Modify:**
- `frontend/src/components/IntelligenceDashboard.css`
- `frontend/src/components/PortfolioMatrix.css`
- `frontend/src/components/SalesTrendGraph.jsx` (ResizeObserver integration)

---

### 5.2 Progressive Web App (PWA)
**Why:** "Install to homescreen" removes the friction of opening a browser. The owner gets an app icon without an app store.

**Implementation:**
- Add `manifest.json` to frontend public directory
  - `name`: RetailMind, `short_name`: RetailMind
  - `theme_color`: `#1a2744` (broadsheet navy)
  - 192×192 and 512×512 PNG icons (broadsheet masthead logo)
- Register a `service-worker.js` via `vite-plugin-pwa`
- Cache strategy: **Network First** for API calls, **Cache First** for static assets
- Offline fallback page: broadsheet-style "No connection — cached data shown below"
- Add `<meta name="theme-color">` and iOS splash screen metas to `index.html`

**Files to Create/Modify:**
- `frontend/public/manifest.json` (new)
- `frontend/public/sw.js` (new, via vite-plugin-pwa)
- `frontend/vite.config.js` — register PWA plugin
- `frontend/index.html` — add PWA metas

---

### 5.3 Mobile Sales Quick-Entry
**Why:** Most SMB owners log sales manually. A quick 3-tap entry screen from mobile beats the CSV upload workflow entirely.

**Implementation:**
- New modal: "Quick Log Sale" — accessible from a floating action button on mobile
- Fields: Product Name (autocomplete from existing products), Qty, Unit Price, Category, Segment
- COGS optional — can be derived from last recorded margin % for that product
- `POST /api/v1/retail/sales/quick-entry` endpoint
- Voice-to-text entry via Web Speech API (browser-native, no API key needed)

**Files to Create/Modify:**
- `frontend/src/components/QuickSaleEntry.jsx` (new)
- `backend/app/api/retail.py` — add `/sales/quick-entry` route

---

## Phase 6 — Advanced Analytics & AI

**Goal:** Push the intelligence layer to a defensible competitive moat. This phase turns RetailMind from "good dashboards" into a genuine decision engine.

---

### 6.1 Cross-Store Performance Benchmarking
**Why:** Users with multiple stores need comparative insights — which location is underperforming and why.

**Implementation:**
- New `GET /api/v1/retail/compare-stores` endpoint
  - Accepts `store_ids[]` array, `period`, and `metric` (revenue / margin / velocity)
  - Returns normalised side-by-side metrics per store
- New frontend view: "Store Comparison" — horizontal bar chart per KPI
- Heatmap overlay showing which store has the most dead stock, highest margin erosion
- K-Means cross-store clustering: flag which stores are "Stars" vs "Dead Weight" at location level

---

### 6.2 Price Elasticity & Margin Optimiser
**Why:** Every retailer underprices high-demand items and overprices slow movers. This feature surfaces those mismatches automatically.

**Implementation:**
- Compute elasticity estimate: `Δ% Qty / Δ% Price` across recorded price points per product
- Margin sensitivity model: simulate the revenue impact of a ±5% price change
- Surface in `TopProductsTable` as a "Price Hint" badge:
  - 📈 "Consider +8% — demand is inelastic at this level"
  - 📉 "Discount 10% — velocity will outperform margin loss"
- Backend: `backend/app/services/price_elasticity.py` (new)

---

### 6.3 Inventory Reorder Point Engine
**Why:** Dead stock and stockouts are two sides of the same coin. Knowing *when* to reorder prevents both.

**Implementation:**
- Per-product reorder point formula:
  ```
  ROP = (Average Daily Demand × Lead Time) + Safety Stock
  Safety Stock = Z × σ_demand × √Lead Time
  ```
  where `Z = 1.65` (95% service level) and `Lead Time` is user-configurable (default: 7 days)
- Reorder alerts surfaced in `DemandSignals` with a new "Reorder" tab
- New `reorder_points` table in PostgreSQL storing user-overridable lead times per product
- Alert fires when `current_stock_estimate ≤ ROP` (stock estimate derived from sales velocity)

---

### 6.4 Gemini Contextual Intelligence Upgrade
**Why:** The current AI chat has no awareness of the live analytics data. A contextually-aware advisor is 10× more useful.

**Implementation:**
- Inject live analytics context into every Gemini prompt:
  ```python
  context = f"""
  Store: {store.name}. Period: {period}.
  Revenue: {summary.total_revenue}. MoM: {summary.mom_change}%.
  Portfolio: {stars_count} Stars, {dead_count} Dead Weight items.
  Top spike: {top_spike.product_name} (Z={top_spike.z_score:.1f}).
  Segments: B2B {b2b_share}%, Online {online_share}%, Walk-in {walkin_share}%.
  """
  ```
- Proactive AI suggestions: surface 3 daily AI tips based on current anomalies (no query needed)
- "Explain this" button on every alert card — one-click to ask the AI to explain that specific signal in plain language

---

### 6.5 Natural Language Query Interface
**Why:** "Which products did I sell the most of last month?" is faster to type than navigating filters.

**Implementation:**
- Input bar in dashboard header: "Ask your data..."
- Gemini function-calling API converts natural language to structured query params:
  - "Top 5 products by margin this week" → `{sort: margin, limit: 5, period: 7d}`
  - "Dead stock in Electronics" → `{filter: dead_stock, category: Electronics}`
- Results rendered inline in a Ledger-style answer card below the search bar

---

## Phase 7 — Integrations & Ecosystem

**Goal:** Zero-friction data ingestion from the tools Indian SMBs already use.

---

### 7.1 Tally ERP Integration
**Why:** Tally is used by ~90% of Indian SMBs for accounting. A native Tally export importer removes the biggest onboarding friction point.

**Implementation:**
- Parse Tally XML export format (`*.xml` from Tally Prime's "Export Data" function)
- Auto-map Tally fields (`StockItem`, `Quantity`, `Rate`, `Amount`) to `SaleRecord` schema
- New upload endpoint: `POST /api/v1/retail/upload-tally-xml`
- "Import from Tally" button in Data Import section alongside CSV/Excel

---

### 7.2 Zoho Books & QuickBooks Import
**Why:** Larger SMBs and exporters use Zoho Books or QuickBooks. OAuth-based direct sync is the gold standard.

**Implementation:**
- OAuth2 connection flow for Zoho Books and QuickBooks Online
- Sync sales invoices as `SaleRecord` entries daily via background job
- `integrations` table: store `{user_id, provider, access_token, refresh_token, last_sync_at}`
- "Connected Accounts" section in Settings

---

### 7.3 Shopify & WooCommerce Connector
**Why:** D2C brands and online-first SMBs run on Shopify. Pulling online order data automatically closes the loop between digital and physical sales.

**Implementation:**
- Shopify: `GET /orders.json` API via private app credentials
- WooCommerce: REST API (`/wp-json/wc/v3/orders`)
- Map order line items to `SaleRecord` entries (product_name, qty, revenue, segment=Online)
- Configurable sync frequency: hourly / daily / manual

---

### 7.4 Barcode Scanner (Mobile)
**Why:** Instead of typing product names, scan a barcode. Reduces manual entry errors to zero.

**Implementation:**
- Integrate `@zxing/library` (web-native barcode scanner, no native app needed)
- Camera-based scanner in `QuickSaleEntry.jsx` modal
- Barcode → product name lookup via OpenFoodFacts API (for FMCG) or local product catalog
- Fallback to manual entry if barcode is not in catalog

---

## Architecture Considerations for Future Phases

### Scalability
- **Current:** Single FastAPI server, single PostgreSQL instance (Neon.tech serverless)
- **Phase 4:** Add a task queue (Redis + Celery) for WhatsApp digest cron jobs and PDF generation
- **Phase 6:** Consider read replica for analytics queries to avoid contending with write path
- **Phase 7:** Add connector microservices (separate FastAPI apps) for Tally/Zoho/Shopify to isolate failure domains

### Security
- Plan gating must be enforced server-side (never client-side)
- Razorpay webhook must verify signature using `razorpay.utility.verify_webhook_signature`
- OAuth tokens for integrations must be encrypted at rest (`cryptography.fernet`)
- WhatsApp phone numbers are PII — must be stored encrypted

### Deployment
- **Current:** Manual deploy (dev server)
- **Phase 4:** CI/CD via GitHub Actions → Railway (backend) + Vercel (frontend)
- **Phase 5:** Add Cloudflare CDN for static assets and regional edge caching
- **Phase 6+:** Consider moving ML inference to a dedicated worker process or AWS Lambda to avoid blocking the FastAPI event loop

---

*Last updated: 2026-05-21 | RetailMind v3.2.0*
