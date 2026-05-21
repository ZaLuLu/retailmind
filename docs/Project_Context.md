# RetailMind — Project Context
**Last Updated:** 2026-05-19
**Version:** 3.0.0 (Upgrade Roadmap Active)
**Status:** Active Development

---

## What is RetailMind?

RetailMind (formerly DocuMind) is a professional-grade **Retail Business Intelligence platform** for SMB owners. It transforms raw sales data into actionable insights via an editorial broadsheet-style dashboard powered by rule-based analytics and ML forecasting.

Target user: A small-to-medium business owner (electronics retailer, apparel shop, FMCG distributor) who needs to understand margin health, demand trends, and dead-stock risks — without needing a data analyst.

---

## Core Value Proposition

| Feature | What it does | Status |
|---|---|---|
| Revenue KPI Strip | MTD Revenue, Gross Profit, Overall Margin %, MoM change | ✅ Live |
| Top Products Table | Sortable leaderboard by revenue/margin/qty | ✅ Live |
| Demand Signals | Rule-based spike detection (7d vs 30d avg) | ✅ Live |
| Dead Stock Alerts | Products with 0 sales in 30 days but had prior sales | ✅ Live |
| Margin Erosion Alerts | Products with blended margin < 20% | ✅ Live |
| AI Insight (Gemini) | One-line FT-headline style business insight | ✅ Live |
| Sales Ledger | Full paginated table of sale records with search + filter | ✅ Live |
| CSV Upload | Auto-detects column headers; supports Excel-exported CSV | ✅ Live |
| SVG Charts | Daily sales trend + category revenue/COGS comparison | ✅ Live |
| AI Retail Advisor | Gemini-powered chat scoped to retail domain | ✅ Live |
| Token Refresh | Automatic session renewal without re-login | ✅ Live |
| Toast Notifications | Replace all alert() calls with inline toasts | ✅ Live |
| Date Range Filter | 7d / 30d / 90d / custom toggle on summary | ✅ Live |
| Multi-store Support | Tag records by store, scope all queries by store_id | ✅ Live |
| Excel Upload | .xlsx support via openpyxl | ✅ Live |
| Export Sales CSV | Download filtered ledger as CSV | ✅ Live |
| Demand Forecasting | Weighted rolling average per product, next 7-day projection | ✅ Live |
| Z-Score Anomaly Detection | Replace 1.5x threshold with per-product z-score model | 🔧 Phase 3 |
| Product Clustering | K-means Stars/Cash Cows/Dead Weight/Hidden Gems matrix | 🔧 Phase 3 |
| Holt-Winters Forecasting | Seasonal demand forecasting (replaces rolling avg) | 🔧 Phase 3 |
| WhatsApp Digest | Weekly AI bulletin via WhatsApp Business API | ⏳ Phase 4 |
| PDF Report Export | Printable broadsheet-style monthly report | ⏳ Phase 4 |
| Razorpay Billing | Free/Pro plan gating with UPI payments | ⏳ Phase 4 |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy (async) · PostgreSQL |
| AI/ML | Google Gemini (`gemini-3-flash-preview`) · scikit-learn (Phase 3) · statsmodels (Phase 3) |
| Auth | JWT (access + refresh) · bcrypt |
| Frontend | React 18 · Vite · Vanilla CSS |
| Design | Playfair Display + Source Serif 4 + JetBrains Mono · Navy + Gold broadsheet palette |
| DB Host | PostgreSQL (local dev / Neon for prod) |
| Payments | Razorpay (Phase 4) |
| Notifications | Twilio WhatsApp API (Phase 4) |

---

## Repository Layout

```
documind/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── retail.py              ← /retail/* endpoints (primary)
│   │   │   ├── auth.py                ← login / register / refresh
│   │   │   ├── advisor.py             ← /advisor/ask (Gemini retail chat)
│   │   │   ├── onboarding.py          ← /onboarding/complete
│   │   │   ├── users.py               ← /users/me GET/PATCH (incl. currency)
│   │   │   ├── deps.py                ← get_current_user dependency
│   │   │   └── intelligence.py        ← legacy (to be removed in Phase 1)
│   │   ├── models/
│   │   │   └── db.py                  ← User, SaleRecord, Store (+ legacy Transaction/Budget)
│   │   ├── services/
│   │   │   ├── retail_intelligence.py ← RetailIntelligenceService (primary)
│   │   │   ├── gemini.py              ← GeminiService (shared AI layer)
│   │   │   ├── demo.py                ← Demo data helpers
│   │   │   └── intelligence.py        ← legacy (to be removed in Phase 1)
│   │   ├── core/
│   │   │   ├── config.py              ← Pydantic settings
│   │   │   └── db.py                  ← Async SQLAlchemy engine + session
│   │   └── main.py
│   ├── seed_demo.py                   ← 220+ retail SaleRecord entries
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── IntelligenceDashboard.jsx  ← Main RetailMind dashboard shell
│       │   ├── IntelligenceDashboard.css  ← Full design system
│       │   ├── RevenueHero.jsx            ← MTD KPI strip
│       │   ├── TopProductsTable.jsx       ← Product leaderboard
│       │   ├── DemandSignals.jsx          ← Tabbed alerts panel
│       │   ├── SalesLedger.jsx            ← Full ledger view
│       │   ├── SalesTrendGraph.jsx        ← SVG charts
│       │   ├── AdvisorChat.jsx            ← Gemini retail advisor overlay
│       │   ├── MLArchitectureMap.jsx      ← System diagram overlay
│       │   ├── Login.jsx / Register.jsx
│       │   └── OnboardingWizard.jsx
│       ├── services/
│       │   ├── api.js                 ← API client (token refresh interceptor: Phase 1)
│       │   └── currency.js            ← Client-side currency conversion
│       ├── App.jsx
│       └── App.css
└── docs/
    ├── Project_Context.md             ← This file
    ├── Architecture.md
    ├── Feature_Log.md
    ├── Changelog.md
    ├── Coding_Rules.md
    └── Roadmap.md                     ← NEW: Full upgrade roadmap
```

---

## Demo Credentials

| Field | Value |
|---|---|
| Email | `rahul@retailmind.com` |
| Password | `password123` |
| Data | 220+ sale records, 5 categories, 6-month history |

Run `python seed_demo.py` from `backend/` to (re-)seed.

---

## API Endpoints

| Method | Path | Description | Status |
|---|---|---|---|
| GET | `/api/v1/retail/summary` | Full BI summary (KPIs + signals + alerts + AI) | ✅ Live |
| GET | `/api/v1/retail/sales` | Paginated sale records | ✅ Live |
| POST | `/api/v1/retail/upload-csv` | Upload sales CSV (auto-detects headers) | ✅ Live |
| GET | `/api/v1/retail/template-csv` | Download CSV template | ✅ Live |
| GET | `/api/v1/retail/forecast` | Per-product demand forecast (next 7d) | ✅ Live |
| GET | `/api/v1/retail/export-csv` | Download filtered ledger as CSV | ✅ Live |
| GET | `/api/v1/stores` | List user's stores | ✅ Live |
| POST | `/api/v1/stores` | Create a new store | ✅ Live |

---

## Known Legacy (Scheduled for Removal — Phase 1)

- `Transaction`, `Budget` models in `db.py`
- `app/services/intelligence.py`
- `app/api/intelligence.py` and `/intelligence/summary` endpoint
- Frontend: `EvidenceViewer.jsx`, old `TransactionVault` references
