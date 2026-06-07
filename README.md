# RetailMind — AI-Powered Retail Business Intelligence Terminal

RetailMind is an elegant, vintage-themed, high-fidelity business intelligence platform designed for SMB retail merchants and store owners. 

By utilizing advanced machine learning pipelines (Holt-Winters time-series forecasting, unsupervised K-Means clustering, and Z-Score anomalies) alongside a secure, guardrailed **Groq Llama-3 AI Retail Advisor**, RetailMind translates raw transaction records into immediate, high-fidelity financial insights, pricing simulations, and teletype briefings.

---

## Technical Masthead

* **Frontend**: React 19 + Vite 8 (monospaced broadsheet typography, high-contrast, pure SVG charts)
* **Backend**: FastAPI + SQLAlchemy (async PG driver)
* **Database**: PostgreSQL (Neon.tech serverless cloud integration)
* **AI Engine**: Groq Cloud API (Llama-3.3-70b-versatile, 30s timeouts, strict retail guardrails)
* **ML Layer**: scikit-learn (K-Means customer & product clustering), statsmodels (14-day Holt-Winters triple exponential smoothing forecasts)
* **Authentication**: JWT + Session Refresh Token Rotation
* **Styling**: Vanilla CSS, layout variables, custom print sheets (teletype briefings)

---

## Core Features

* 📊 **Financial Telemetry Briefing** — KPI highlights tracking MTD Revenue, COGS, Gross Profit, and MoM trend percentage indices.
* 🔮 **Demand Forecasting** — Holt-Winters triple exponential smoothing projecting a 14-day future ledger with 95% confidence intervals.
* 🧩 **Catalog Quadrant Matrix** — Unsupervised K-Means clustering classifying inventory into **Stars**, **Cash Cows**, **Hidden Gems**, and **Dead Weight**.
* 👥 **Customer Segment Breakdown** — Deep SQL metrics mapping contribution margins, average order values (AOV), and growth rates across **B2B**, **Online**, and **Walk-In** channels.
* 📈 **Margin & Price Simulator** — Slide price variances from `-30%` to `+30%` to model dynamic elastic volume responses, margin shifts, and net profit differences.
* 📰 **Teletype Telex Briefing** — View and download plain text dispatches, or print to a clean physical telegram layout via customized print-stylesheets.
* 📋 **Operations Action Checklists** — Expand alert cards for Spikes, Dead Stock, and Margins to tick off operational action plans with local storage persistence.
* 🤖 **Groq AI Retail Advisor** — Converse with a world-class analytics expert, fortified with smart domain-scoped guardrails that professionally block off-topic queries.
* 🏬 **Multi-Store Roster** — Register and switch store contexts instantly; metrics re-cluster and recalculate dynamically.

---

## Showcase Demo Credentials

RetailMind includes a pre-seeded guest demo store containing a full year of retail sales history:

* **Email**: `demo@retailmind.com`
* **Password**: `demo123`
* **Active Store**: RetailMind Demo Store
* **Pre-Seeded Data**: 220+ historical daily ledger logs

> To re-run data seeding manually: `python backend/scripts/seed_demo_account.py`

---

## Local Setup & Configuration

### Prerequisites
* Python 3.11+
* Node.js 20+
* PostgreSQL DB (Neon.tech recommended)
* Groq Cloud API Key ([Console Signup](https://console.groq.com/))

### 1. Backend Ingestion
```bash
cd backend

# Create & activate virtual env
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up Environment Config
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET, and GROQ_API_KEY
```

**Run Database Migrations:**
Initialize your database by running the schema script:
```bash
# Using PostgreSQL Client
psql your_connection_string < schema.sql
```

**Launch Server:**
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Development
```bash
cd frontend

# Install package modules
npm install

# Start Local Dev Server
npm run dev
```
Open `http://localhost:5173` to view your broadsheet terminal.

---

## Verification Suite

Ensure backend logic compiles and matches structural ML/Advisor schemas:
```bash
cd backend

# Run Groq API & Guardrails verification
.venv\Scripts\python.exe scripts/test_groq.py

# Run Advisor context validation
.venv\Scripts\python.exe scripts/test_advisor_valid.py

# Run Holt-Winters & K-Means calculations checks
.venv\Scripts\python.exe scripts/test_ml_layer.py
```

---

## Project Directory Organization

```text
documind/
├── backend/
│   ├── app/
│   │   ├── api/            # Route controllers (auth, retail, advisor, admin)
│   │   ├── core/           # Security, config.py, database configs
│   │   ├── models/         # ORM entities (User, Store, SaleRecord, Alert)
│   │   └── services/       # Analytical logic & llm.py (Groq)
│   └── scripts/            # Database seed and Python test suites
├── frontend/
│   ├── src/
│   │   ├── components/     # UI elements (Dashboard, PricingSimulator, TelexBriefing)
│   │   ├── services/       # api.js and currency calculators
│   │   └── App.jsx         # App router
│   └── index.html          # Entry document
└── docs/                   # Architectural blueprints & guides
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
