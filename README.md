# RetailMind — AI-Powered Retail Business Intelligence

RetailMind is an open-source business intelligence platform for SMB retail store owners.
Upload your sales data, and get instant AI insights on revenue, margins, demand spikes, dead stock, and customer segments — powered by Google Gemini.

---

## Features

- 📊 **Intelligence Briefing** — KPI cards, revenue trends, top products
- 🔮 **Demand Forecasting** — Holt-Winters triple exponential smoothing
- 🧩 **Portfolio Matrix** — K-Means clustering (Stars, Cash Cows, Hidden Gems, Dead Weight)
- 👥 **Customer Segments** — Walk-in vs Online vs B2B analytics
- ⚠️ **Smart Alerts** — Dead stock detection, margin erosion alerts, demand spikes
- 🤖 **Retail Advisor** — Gemini-powered AI chat for business questions
- 📁 **CSV / XLSX Upload** — Auto-detects column headers (15+ aliases)
- 🏬 **Multi-Store Support** — Manage and switch between multiple locations
- 📤 **CSV Export** — Download filtered ledger data

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite 8 |
| Backend | FastAPI + SQLAlchemy (async) |
| Database | PostgreSQL (Neon.tech recommended) |
| AI | Google Gemini 1.5 Flash |
| ML | scikit-learn (K-Means), statsmodels (Holt-Winters) |
| Auth | JWT + Refresh Token Rotation |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL database (Neon.tech free tier works great)
- Google Gemini API key ([Get one here](https://aistudio.google.com/))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET, GEMINI_API_KEY

# Initialize database (run schema.sql on your Postgres DB)
# Then start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional for local dev)
cp .env.example .env.local
# Edit .env.local to set VITE_API_BASE_URL if needed

# Start dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) | ✅ |
| `JWT_SECRET` | Secret key for JWT signing (min 32 chars) | ✅ |
| `GEMINI_API_KEY` | Google AI Studio API key | ⚠️ Optional (disables AI features) |
| `GEMINI_MODEL` | Model name (default: `gemini-1.5-flash`) | No |
| `ENVIRONMENT` | `development` or `production` | No |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | No |
| `SENTRY_DSN` | Sentry DSN for error tracking | No |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API URL (e.g., `https://api.yourdomain.com/api/v1`) |

---

## Database Setup

Run `schema.sql` on your PostgreSQL database:

```bash
psql your_connection_string < schema.sql
```

---

## Deployment

### Frontend → Vercel
1. Push this repo to GitHub
2. Import the repo in [Vercel](https://vercel.com)
3. Set **Root Directory** to `frontend`
4. Add environment variable: `VITE_API_BASE_URL` → your backend URL
5. Deploy ✅

### Backend → Railway / Render / Fly.io
The FastAPI backend can be deployed on any platform that supports Python.

**Recommended: [Railway](https://railway.app)**
1. Create a new project → Deploy from GitHub
2. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Add all environment variables from `.env.example`

---

## CSV Upload Format

| Column | Required | Aliases |
|--------|----------|---------|
| `product_name` | ✅ | product, item, item_name, name |
| `quantity` | ✅ | qty, quantity_sold, units, units_sold |
| `unit_price` | ✅ | price, selling_price, sale_price, mrp |
| `date` | ✅ | sale_date, transaction_date, order_date |
| `sku` | No | product_sku, item_code, barcode |
| `category` | No | product_category, type |
| `cogs` | No | cost, cost_price, purchase_price |
| `customer_segment` | No | — |
| `currency` | No | — |

Download the template from the app's **Data Import** section.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ for small business owners who deserve enterprise-grade analytics.*
