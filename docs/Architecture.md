# RetailMind — Architecture
**Version:** 3.0.0 · Updated: 2026-05-19

---

## System Overview

```
Browser (React + Vite)
    │
    ├── GET /retail/summary     ──► RetailIntelligenceService
    │                                    ├── SaleRecord queries (SQLAlchemy async)
    │                                    └── Gemini API (AI insight)
    │
    ├── GET /retail/sales       ──► SaleRecord paginated SELECT
    │
    ├── POST /retail/upload-csv ──► CSV/XLSX parser → bulk SaleRecord INSERT
    │
    ├── GET /retail/forecast    ──► ForecastService (Phase 2: rolling avg → Phase 3: Prophet)
    │
    └── POST /advisor/ask       ──► GeminiService.ask_advisor()
                                         └── Google Gemini Flash

PostgreSQL (Neon.tech)
    ├── users                ← auth + currency + plan
    ├── refresh_tokens       ← JWT refresh token store
    ├── stores               ← multi-store (Phase 2)
    ├── sale_records         ← PRIMARY retail data table
    ├── transactions         ← LEGACY — scheduled removal Phase 1
    └── budgets              ← LEGACY — scheduled removal Phase 1
```

---

## Backend Module Map

```
app/
├── main.py                   FastAPI entry point, router registration
├── core/
│   ├── config.py             Pydantic settings (env vars)
│   └── db.py                 Async SQLAlchemy engine + session
├── models/
│   └── db.py                 SQLAlchemy ORM models
│                             Active: User, SaleRecord, Store
│                             Legacy (Phase 1 removal): Transaction, Budget
├── api/
│   ├── deps.py               get_current_user dependency
│   ├── auth.py               login / register / demo-login / refresh
│   ├── retail.py             /retail/* (summary, sales, upload-csv, template, forecast)
│   ├── advisor.py            /advisor/ask (Gemini retail chat)
│   ├── onboarding.py         /onboarding/complete
│   ├── users.py              /users/me GET/PATCH (incl. currency, plan)
│   └── intelligence.py       LEGACY — scheduled removal Phase 1
└── services/
    ├── retail_intelligence.py    RetailIntelligenceService (primary analytics)
    ├── gemini.py                 GeminiService (shared AI layer)
    ├── demo.py                   Demo data helpers
    └── intelligence.py           LEGACY — scheduled removal Phase 1
```

---

## Frontend Component Tree

```
App.jsx
├── Login.jsx / Register.jsx
├── OnboardingWizard.jsx              store name, currency, demo shortcut
├── [ErrorBoundary]                   Phase 1: global crash fallback
├── [ToastProvider]                   Phase 1: replaces all alert() calls
├── IntelligenceDashboard.jsx         main shell
│   ├── [DateRangeToggle]             Phase 2: 7d/30d/90d/custom
│   ├── RevenueHero.jsx               MTD KPIs (Revenue, GP, Margin, MoM)
│   ├── SalesTrendGraph.jsx           SVG daily trend + category COGS bars
│   ├── TopProductsTable.jsx          Sortable product leaderboard
│   ├── DemandSignals.jsx             Tabbed: Spikes | Dead Stock | Margin | Forecast(P2)
│   ├── [ProductClusterMatrix]        Phase 3: Stars/Cash Cows/Dead Weight/Hidden Gems
│   ├── [CSV/XLSX Upload panel]       Phase 2: adds .xlsx support
│   └── SalesLedger.jsx               Paginated table with search/filter/export
├── AdvisorChat.jsx                   Gemini retail advisor overlay
└── MLArchitectureMap.jsx             System diagram overlay
```

---

## API Client Architecture (Phase 1 Upgrade)

Current `api.js` makes direct fetch calls with no retry logic. Phase 1 replaces this with a central interceptor:

```
request(method, endpoint, data)
    │
    ├── Attach Authorization header
    ├── Execute fetch
    │
    ├── If 200-299 → return data
    │
    ├── If 401 AND not already retrying
    │       ├── POST /auth/refresh with refresh_token
    │       ├── If success → store new tokens → retry original request
    │       └── If failure → clear tokens → redirect to /login
    │
    └── If 4xx/5xx → throw structured error (status + message)
```

---

## SaleRecord Data Flow

```
CSV/XLSX Upload
    → POST /retail/upload-csv
    → Header auto-detect (15+ aliases) + openpyxl for .xlsx (Phase 2)
    → Parse rows: qty × unit_price → total_revenue
    → Compute cogs, gross_margin
    → Bulk INSERT SaleRecord[] (batch size 100)
    → Frontend calls onRefresh() → re-fetches summary + sales

Seed / Manual
    → seed_demo.py inserts 220+ records directly
```

---

## Intelligence Algorithms

### Current (Rule-Based)

**Demand Spike Detection**
```
recent_qty       = SUM(qty) for product, last 7 days
prior_qty        = SUM(qty) for product, days -37 to -7
prior_weekly_avg = prior_qty / 4.3
spike            = recent_qty >= prior_weekly_avg * 1.5
```

**Dead Stock Detection**
```
had_sales_prior  = products with sales between -90d and -30d
active_recently  = products with sales in last 30d
dead_stock       = had_sales_prior - active_recently
```

**Margin Erosion**
```
erosion = products where AVG(gross_margin) < 20%
         AND COUNT(records) >= 2
ordered by margin ASC, limit 5
```

### Phase 2 — Forecasting v1 (Rolling Average)
```
For each product:
    weights = [1, 2, 3, 4, 5, 6, 7]  # recent days weighted higher
    forecast_qty = weighted_avg(daily_qty[-7:], weights)
    order_by_date = today + (current_stock / forecast_qty)  # if stock data available
```

### Phase 3 — ML Upgrades

**Z-Score Anomaly Detection (replaces 1.5x threshold)**
```
For each product:
    mean = AVG(weekly_qty, rolling 12 weeks)
    std  = STDDEV(weekly_qty, rolling 12 weeks)
    z    = (current_week_qty - mean) / std
    spike = z > 2.0
```

**Product Clustering (K-Means, k=4)**
```
features = [revenue_normalized, margin_pct, qty_sold_normalized, days_since_last_sale]
clusters → Stars | Cash Cows | Dead Weight | Hidden Gems
```

**Demand Forecasting v2 (Statsmodels Holt-Winters)**
```
Per product with 90+ days history:
    model = ExponentialSmoothing(qty_sold_series, seasonal_periods=7, trend='add', seasonal='add')
    fit_model = model.fit()
    forecast = fit_model.forecast(14)
    return forecast
```

---

## Data Model: SaleRecord

```python
class SaleRecord(Base):
    id                UUID, primary key
    user_id           FK → users.id
    store_id          FK → stores.id (Phase 2, nullable)
    product_name      str
    product_sku       str, nullable
    product_category  str
    quantity_sold     Numeric
    unit_price        Numeric
    total_revenue     Numeric  (qty × unit_price)
    cogs              Numeric, nullable  (total cost for qty sold)
    gross_margin      Numeric, nullable  (% margin)
    sale_date         Date
    customer_segment  str, nullable  (Walk-in / Online / B2B)
    currency          str  (INR / USD / EUR / GBP / AED)
    ml_meta           JSONB  (reserved for ML feature storage)
    source            str  (csv_upload / seed / manual)
    created_at        DateTime
```

---

## Environment Variables (backend/.env)

```
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3-flash-preview
FRONTEND_URL=http://localhost:5173
SENTRY_DSN=...
ENVIRONMENT=development
UPLOAD_DIR=storage/uploads
```

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Seed demo data
python seed_demo.py

# Frontend
cd frontend
npm install
npm run dev       # → http://localhost:5173
```
