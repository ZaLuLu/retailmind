# RetailMind Architecture Design Blueprint

This document specifies the structural architecture, module directories, database patterns, and user request lifecycles of the **RetailMind Platform**.

---

## 1. System Overview

```text
       Browser client (React + Vite)
                     │
         [JSON over HTTP / HTTPS]
                     ▼
         FastAPI Gate Router (uvicorn)
          ├── api/auth.py        ───► Session tokens
          ├── api/users.py       ───► User context & configurations
          ├── api/retail.py      ───► Sales records & Forecast calculation
          ├── api/advisor.py     ───► Groq Llama-3 AI advisor
          └── api/admin.py       ───► Data reset and seeding
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
Services Layer                 ML Engine
  ├── llm.py (Groq client)      ├── statsmodels (Holt-Winters)
  └── demo_store.py             └── scikit-learn (K-Means)
      │                             │
      └──────────────┬──────────────┘
                     ▼
             SQLAlchemy Async
                     ▼
          PostgreSQL Database (Neon)
           ├── users (settings, currency, plan)
           ├── stores (roster locations)
           ├── sale_records (raw ledger data)
           ├── alerts (in-app issues cache)
           └── ml_results ( Holt-Winters & K-Means cache)
```

---

## 2. Directory Responsibilities

### 2.1 Backend Component Map
```text
backend/
├── app/
│   ├── main.py               # Application engine initialization & routing
│   ├── core/
│   │   ├── config.py         # Type-safe environment settings reading
│   │   ├── db.py             # SQLAlchemy async engine session creation
│   │   └── limiter.py        # SlowAPI rate limits config
│   ├── models/
│   │   └── db.py             # Core SQLAlchemy database entities (User, Store, SaleRecord, Alert, MLResult)
│   ├── api/
│   │   ├── deps.py           # Dependency injections (get_current_user, get_db)
│   │   ├── auth.py           # Authentication and demo token generation
│   │   ├── retail.py         # CSV upload, ledger retrieval, and template paths
│   │   ├── advisor.py        # Advisor routing (Ask / Stream endpoints)
│   │   └── onboarding.py     # Onboarding wizard updates
│   │   └── users.py          # User configurations
│   │   └── admin.py          # Admin endpoints for database resets and seeds
│   └── services/
│       ├── llm.py            # AsyncGroq interface, fallback handler, and domain prompt injection
│       ├── retail_intelligence.py # Holt-Winters additive smoothing, K-Means clustering, SQL segments
│       └── demo_store.py     # Hardcoded demo seed values (220+ records)
└── scripts/
    ├── seed_demo_account.py  # Manual database seed execution
    ├── test_groq.py          # Groq integration testing
    ├── test_advisor_valid.py # Advisor context validation suite
    └── test_ml_layer.py      # Holt-Winters & K-Means unit validations
```

### 2.2 Frontend Component Map
```text
frontend/
├── src/
│   ├── components/
│   │   ├── Login.jsx                 # Broadsheet login portal
│   │   ├── Register.jsx              # Broadsheet user registration
│   │   ├── OnboardingWizard.jsx      # Initial currency & store registration
│   │   ├── GuidedTour.jsx            # Interactive tour steps mapping
│   │   ├── IntelligenceDashboard.jsx # Dashboard shell layout
│   │   ├── RevenueHero.jsx           # Top summary MTD KPI cards
│   │   ├── SalesTrendGraph.jsx       # SVG chart mapping daily totals & forecasts
│   │   ├── TopProductsTable.jsx      # Leaderboard table of products
│   │   ├── CustomerSegmentsPanel.jsx # SQL segment breakdown cards
│   │   ├── PortfolioMatrix.jsx       # K-Means four-quadrant SVG matrix
│   │   ├── DemandSignals.jsx         # Tabs for Spikes, Dead Stock, Margin, Forecast
│   │   ├── PricingSimulator.jsx      # Dynamic elasticity margin calculator
│   │   ├── TelexBriefing.jsx         # Vintage modal for printing & downloading
│   │   ├── AdvisorChat.jsx           # AI chat sidebar modal (Groq client)
│   │   ├── Toast.jsx                 # Standard in-app notification toasts
│   │   └── ErrorBoundary.jsx         # Recovery boundary for nested failures
│   ├── services/
│   │   ├── api.js                    # Centralized axios-like fetch wrapper
│   │   └── currency.js               # Conversion logic & dynamic formatting
│   └── App.jsx                       # Routing tree & bootstrap state
└── index.html                        # Application viewport entry
```

---

## 3. Data Processing Models

### 3.1 Unsupervised K-Means clustering (Quadrants)
The matrix classifies products into four quadrants using scikit-learn standard scaled features:
* **Stars** (High Revenue, High Margin)
* **Cash Cows** (High Revenue, Low Margin)
* **Hidden Gems** (Low Revenue, High Margin)
* **Dead Weight** (Low Revenue, Low Margin)

### 3.2 14-Day Holt-Winters Time-Series Projection
Projects daily revenues for the store and safety stock quantities per item using additive Level ($l_t$), Trend ($b_t$), and Seasonality ($s_t$) calculations. The algorithm optimizes alpha, beta, and gamma coefficients dynamically to minimize Sum of Squared Errors (SSE) over a rolling 90-day history.

---

## 4. User Request Lifecycles

### 4.1 AI Advisor Ingestion Pipeline
1. The user inputs a chat question in `AdvisorChat.jsx`.
2. The client fetches the current store telemetry parameters (MTD numbers, dead stock alerts, and margins) and serializes it as a JSON `context` block.
3. The client calls `/api/v1/advisor/stream` sending the question, history, and context.
4. FastAPI validates inputs against prompt injection scripts and checks SlowAPI rate limits (30/min).
5. FastAPI calls `llm_service.stream_advisor()`.
6. If the question is off-topic, a strict system guardrail intercepts it, outputting the default deflection reply.
7. Otherwise, the service forwards the compiled messages block to Groq (`llama-3.3-70b-versatile`) with a 30-second timeout.
8. Groq returns response chunks, which are yielded to the client via a Server-Sent Events (SSE) data stream.

### 4.2 CSV/Excel Ledger Ingestion Pipeline
1. The user drops a CSV or Excel (`.xlsx`) sheet into the Data Import box.
2. The client checks size bounds (< 10 MB) and calls `api.uploadSalesCsv(file)`.
3. The backend maps headers against 15+ column name aliases (e.g. `qty` -> `quantity_sold`).
4. The backend computes computed fields (`total_revenue = quantity_sold * unit_price`, `gross_margin = (total_revenue - cogs) / total_revenue * 100`).
5. Rows are committed to `sale_records` using async batch operations (chunks of 100).
6. The database triggers alert sweeps (dead stock, margin warnings, demand spikes) and updates the cached `ml_results` model.
7. The client triggers `onRefresh()`, causing dashboard panels to reload with the new ledger context.
