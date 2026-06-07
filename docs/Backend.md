# RetailMind Backend Documentation

This document describes the FastAPI backend service architecture, endpoints, database models, and analytics processes.

---

## 1. Stack Specifications
* **Runtime**: Python 3.11+
* **Framework**: FastAPI (Asynchronous AsyncIO endpoints)
* **SQL ORM**: SQLAlchemy 2.0 (Async Engine + asyncpg PostgreSQL driver)
* **API Rate Limiter**: SlowAPI (token bucket algorithm backed by memory or Redis)
* **Data Processing**: numpy, scikit-learn (K-Means), statsmodels (Holt-Winters)
* **Configuration**: Pydantic Settings reading `.env` variables

---

## 2. API Endpoints

### 2.1 Auth Module (`app/api/auth.py`)
* `POST /api/v1/auth/register` — Registers a new user account.
* `POST /api/v1/auth/login` — Verifies email/password and returns JWT access + refresh tokens.
* `POST /api/v1/auth/demo-login` — Generates temporary access session tokens bound to isolated mock databases.
* `POST /api/v1/auth/refresh` — Standard rotation endpoint: exchanges a valid refresh token for a new set of credentials.

### 2.2 Retail Module (`app/api/retail.py`)
* `GET /api/v1/retail/summary` — Evaluates active date period (7d / 30d / 90d / custom / mtd) and pulls MTD stats, category averages, demand spikes, and K-Means clusters.
* `GET /api/v1/retail/sales` — Paginated database transaction log, supporting search filters and category tags.
* `POST /api/v1/retail/upload-csv` — Bulk uploads sale records. Parses file, validates, maps columns, and writes rows.
* `GET /api/v1/retail/forecast` — Daily rolling demand forecasts and safety buffer stock calculations.
* `GET /api/v1/retail/template-csv` — Serves a template CSV sheet specifying mandatory columns.

### 2.3 Advisor Module (`app/api/advisor.py`)
* `POST /api/v1/advisor/ask` — Synchronous single-response chat query.
* `POST /api/v1/advisor/stream` — SSE stream endpoint. Stream Llama-3 chunks from Groq.

### 2.4 Admin Console (`app/api/admin.py`)
* `POST /api/v1/admin/reset-db` — Deletes all records matching the current user context.
* `POST /api/v1/admin/seed-demo` — Seed the user profile with 220+ historical demo transaction records.

---

## 3. Database Layer Models (`app/models/db.py`)

### 3.1 User Table (`users`)
Stores user emails, password hashes, preferred store currencies (INR/USD/etc.), subscription plans, and active onboarding completion flags.

### 3.2 Store Table (`stores`)
Holds registered storefront identifiers, names, locations, and user mappings.

### 3.3 Sale Record Table (`sale_records`)
The primary ledger of transactions:
* Columns: `product_name`, `product_category`, `quantity_sold`, `unit_price`, `total_revenue`, `cogs`, `gross_margin`, `sale_date`, `customer_segment`, `currency`.

### 3.4 In-App Alerts Table (`alerts`)
A temporary cache storing computed alerts for inventory spikes, margin drops, and dead stock items.

### 3.5 ML Results Table (`ml_results`)
Caches pre-computed K-Means classifications and forecast arrays, indexed by user and store. When new data is uploaded, the hash changes, triggering recalculation.
