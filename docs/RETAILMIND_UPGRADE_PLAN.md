# RetailMind — Comprehensive Upgrade Plan
> **Target:** Full-stack overhaul optimized for Antigravity IDE efficiency  
> **Repo:** https://github.com/ZaLuLu/retailmind  
> **Stack:** React 19 + Vite · FastAPI · PostgreSQL · Google Gemini · scikit-learn  
> **Date:** May 2026

---

## Table of Contents

1. [Antigravity IDE Compatibility Layer](#1-antigravity-ide-compatibility-layer)
2. [Repository Structure Overhaul](#2-repository-structure-overhaul)
3. [Database / Schema Upgrades](#3-database--schema-upgrades)
4. [Backend (FastAPI) Upgrades](#4-backend-fastapi-upgrades)
5. [Frontend (React + Vite) Upgrades](#5-frontend-react--vite-upgrades)
6. [UI/UX Component-by-Component Overhaul](#6-uiux-component-by-component-overhaul)
7. [AI / ML Engine Upgrades](#7-ai--ml-engine-upgrades)
8. [DevOps, Deployment & CI/CD](#8-devops-deployment--cicd)
9. [Security Hardening](#9-security-hardening)
10. [Testing Strategy](#10-testing-strategy)
11. [Priority Execution Roadmap](#11-priority-execution-roadmap)

---

## 1. Antigravity IDE Compatibility Layer

Antigravity IDE relies on structured context, deterministic file layouts, and AI-navigable codebases. Every change below is designed to maximize how well the IDE can parse, suggest, and auto-complete across the monorepo.

### 1.1 Project-Level Config Files

Add these files to the repo root:

```
retailmind/
├── .antigravity/
│   ├── context.json          ← project metadata for IDE AI context window
│   ├── component-map.json    ← explicit component dependency graph
│   └── api-map.json          ← route → handler → schema mapping
├── .vscode/
│   └── settings.json         ← shared editor config (also read by Antigravity)
├── jsconfig.json             ← path aliases for frontend (IDE navigation)
├── pyproject.toml            ← replaces setup.py; Antigravity reads this
└── .editorconfig             ← universal formatting baseline
```

**`.antigravity/context.json` template:**
```json
{
  "project": "RetailMind",
  "type": "fullstack-monorepo",
  "frontend": { "root": "frontend/src", "entry": "main.jsx", "framework": "react19" },
  "backend": { "root": "backend/app", "entry": "main.py", "framework": "fastapi" },
  "db": { "engine": "postgresql", "schema": "schema.sql", "orm": "sqlalchemy-async" },
  "ai": { "provider": "google-gemini", "model": "gemini-2.5-flash" },
  "aliases": {
    "@components": "frontend/src/components",
    "@hooks": "frontend/src/hooks",
    "@api": "frontend/src/api",
    "@store": "frontend/src/store"
  }
}
```

### 1.2 Path Aliases (Frontend)

Update `vite.config.js` to define path aliases so the IDE resolves imports instantly:

```js
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@api': path.resolve(__dirname, 'src/api'),
      '@store': path.resolve(__dirname, 'src/store'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@types': path.resolve(__dirname, 'src/types'),
    },
  },
})
```

Add matching `jsconfig.json` at `frontend/`:
```json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"],
      "@components/*": ["components/*"],
      "@hooks/*": ["hooks/*"],
      "@api/*": ["api/*"],
      "@store/*": ["store/*"],
      "@utils/*": ["utils/*"]
    }
  }
}
```

### 1.3 Backend Module Structure for IDE Navigation

Convert the backend to a fully explicit package structure so Antigravity can build the call graph:

```
backend/app/
├── __init__.py
├── main.py
├── config.py              ← all env vars as typed Pydantic Settings
├── database.py
├── dependencies.py        ← FastAPI Depends() factories in one place
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── sales.py
│   ├── analytics.py
│   ├── forecasting.py
│   ├── stores.py
│   └── advisor.py
├── models/                ← SQLAlchemy ORM models
│   ├── __init__.py
│   ├── user.py
│   ├── sale.py
│   ├── store.py
│   └── refresh_token.py
├── schemas/               ← Pydantic request/response schemas
│   ├── __init__.py
│   ├── auth.py
│   ├── sale.py
│   ├── analytics.py
│   └── store.py
├── services/              ← business logic, decoupled from routes
│   ├── __init__.py
│   ├── auth_service.py
│   ├── sales_service.py
│   ├── analytics_service.py
│   └── advisor_service.py
└── ml/
    ├── __init__.py
    ├── forecasting.py     ← Holt-Winters
    ├── clustering.py      ← K-Means portfolio matrix
    └── alerts.py          ← dead stock / margin erosion logic
```

**Why this matters for Antigravity:** Every layer is a separate file with a single responsibility. The IDE can resolve `from app.services.sales_service import calculate_margins` without ambiguity and suggest completions across the full dependency tree.

### 1.4 Type Annotations Everywhere

- Backend: All functions must have full Python type hints (params + return types). Use `from __future__ import annotations` at the top of every file.
- Frontend: Migrate from plain JSX to TypeScript (`.tsx`). Add `frontend/tsconfig.json`. This is the single highest-leverage Antigravity improvement — the IDE uses types to power autocomplete, refactoring, and error detection.

---

## 2. Repository Structure Overhaul

### Current Structure (problems)
```
retailmind/
├── Demo_data/        ← loose Excel files, no versioning strategy
├── backend/          ← flat, unclear sub-structure
├── docs/             ← likely sparse
├── frontend/         ← unknown component organization
├── schema.sql        ← at repo root, no migration history
├── start_retailmind.bat  ← Windows-only dev script
├── render.yaml
└── vercel.json       ← experimental multi-service config (fragile)
```

### Target Structure
```
retailmind/
├── .antigravity/              ← IDE context (new)
├── .github/
│   └── workflows/
│       ├── ci.yml             ← lint + test on PR
│       └── deploy.yml         ← prod deploy on merge to main
├── backend/
│   ├── app/                   ← structured as above in §1.3
│   ├── migrations/            ← Alembic migration files (replaces schema.sql)
│   │   ├── env.py
│   │   └── versions/
│   ├── scripts/
│   │   └── seed_demo_account.py
│   ├── tests/
│   ├── pyproject.toml         ← replaces requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/        ← organized by feature domain (see §6)
│   │   ├── hooks/
│   │   ├── api/               ← all fetch logic centralized
│   │   ├── store/             ← Zustand stores
│   │   ├── types/             ← shared TypeScript interfaces
│   │   ├── utils/
│   │   └── pages/             ← route-level components
│   ├── public/
│   ├── tsconfig.json          ← migrate to TypeScript
│   ├── vite.config.ts
│   └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md                 ← auto-generated from OpenAPI
│   ├── CONTRIBUTING.md
│   └── UPGRADE_PLAN.md        ← this document
├── Demo_data/
│   └── README.md              ← explain the sample data format
├── docker-compose.yml         ← local dev: postgres + backend + frontend
├── docker-compose.prod.yml
├── Makefile                   ← `make dev`, `make test`, `make migrate`
├── .editorconfig
├── .gitignore
├── README.md
├── render.yaml
└── vercel.json
```

**Add `Makefile` for one-command workflows:**
```makefile
.PHONY: dev test migrate lint seed

dev:
	docker-compose up --build

test:
	cd backend && pytest -v
	cd frontend && npm run test

migrate:
	cd backend && alembic upgrade head

lint:
	cd backend && ruff check . && mypy app/
	cd frontend && npx eslint src/ && npx tsc --noEmit

seed:
	cd backend && python scripts/seed_demo_account.py
```

---

## 3. Database / Schema Upgrades

### 3.1 Replace Raw SQL with Alembic Migrations

The current `schema.sql` at root is a one-shot file with no history tracking. Replace with Alembic:

```bash
cd backend
pip install alembic
alembic init migrations
# Initial migration auto-generated from SQLAlchemy models
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

**Why:** Antigravity IDE tracks migration history. Every schema change becomes a versioned, reviewable file — not an ad-hoc SQL edit.

### 3.2 Schema Improvements

**`users` table:**
- Add `timezone VARCHAR(50) DEFAULT 'UTC'` — currently missing, causes date calculation bugs for non-UTC stores
- Add `plan VARCHAR(20) DEFAULT 'free'` — future monetization hook
- Add `last_login_at TIMESTAMPTZ` — for security audit

**`sale_records` table:**
- Add `notes TEXT` — allows manual annotations on records
- Add `tags TEXT[]` — flexible labeling without schema changes
- Add `is_return BOOLEAN DEFAULT FALSE` — handle refunds without negative quantities
- Change `gross_margin DECIMAL(5,2)` to `GENERATED ALWAYS AS ((unit_price - COALESCE(cogs,0)) / NULLIF(unit_price,0) * 100) STORED` — computed column eliminates inconsistency bugs
- Add `CHECK (quantity_sold > 0 OR is_return = TRUE)` constraint

**`stores` table:**
- Add `currency VARCHAR(3) DEFAULT 'INR'` — per-store currency (not just per-user)
- Add `timezone VARCHAR(50)` — critical for multi-timezone retail chains
- Add `is_active BOOLEAN DEFAULT TRUE` — soft-delete for stores

**Remove legacy tables cleanly:**
- `budgets` and `transactions` are marked "Legacy — may be removed". Create a migration that drops them, or move them to a `_legacy` schema. Don't leave dead tables in production.

**New table: `alerts`**
```sql
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
  alert_type VARCHAR(50) NOT NULL,  -- 'dead_stock' | 'margin_erosion' | 'demand_spike'
  product_sku VARCHAR(100),
  product_name VARCHAR(255),
  severity VARCHAR(20) DEFAULT 'warning',  -- 'info' | 'warning' | 'critical'
  payload JSONB,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_alerts_user_unread ON alerts(user_id, is_read) WHERE is_read = FALSE;
```

**New table: `ai_conversations`**
```sql
CREATE TABLE ai_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  messages JSONB NOT NULL DEFAULT '[]',
  context_snapshot JSONB,   -- KPI snapshot at conversation start
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3 Add Full-Text Search

```sql
ALTER TABLE sale_records ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english', product_name || ' ' || COALESCE(product_category,'') || ' ' || COALESCE(product_sku,''))
  ) STORED;

CREATE INDEX idx_sale_fts ON sale_records USING GIN(search_vector);
```

Enables instant product search without a separate search service.

### 3.4 Partitioning for Scale

For stores with 100k+ records, add range partitioning by `sale_date`:

```sql
-- Partition sale_records by year
CREATE TABLE sale_records_2024 PARTITION OF sale_records
  FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE sale_records_2025 PARTITION OF sale_records
  FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

---

## 4. Backend (FastAPI) Upgrades

### 4.1 Dependency & Tooling

| Current | Upgrade To | Reason |
|---|---|---|
| `requirements.txt` | `pyproject.toml` + `uv` | Faster installs, lockfile, IDE-parseable |
| Ad-hoc env loading | `pydantic-settings` `BaseSettings` | Type-safe config, IDE completion on `settings.X` |
| No linting | `ruff` + `mypy` | Fastest Python linter, type checking |
| No formatting | `ruff format` | Replaces black |
| `uvicorn --reload` only | `uvicorn` + `gunicorn` workers in prod | Proper multi-process production serving |

**`pyproject.toml`:**
```toml
[project]
name = "retailmind-backend"
version = "2.0.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "sqlalchemy[asyncio]>=2.0",
  "asyncpg>=0.29",
  "alembic>=1.13",
  "pydantic-settings>=2.3",
  "pydantic>=2.7",
  "python-jose[cryptography]>=3.3",
  "passlib[bcrypt]>=1.7",
  "google-generativeai>=0.7",
  "scikit-learn>=1.5",
  "statsmodels>=0.14",
  "pandas>=2.2",
  "openpyxl>=3.1",
  "python-multipart>=0.0.9",
  "sentry-sdk[fastapi]>=2.0",
  "httpx>=0.27",   # async HTTP client for testing
]

[dependency-groups]
dev = ["pytest", "pytest-asyncio", "ruff", "mypy", "factory-boy"]
```

### 4.2 Typed Config (`config.py`)

```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    environment: str = "development"
    allowed_origins: list[str] = ["http://localhost:5173"]
    sentry_dsn: str | None = None
    max_upload_rows: int = 50_000

settings = Settings()
```

**IDE benefit:** Antigravity can autocomplete `settings.` with full type information across all 30+ files that import config.

### 4.3 API Versioning

Current routes are under `/api/v1`. Make this explicit and robust:

```python
# main.py
from fastapi import FastAPI
from app.routers import auth, sales, analytics, forecasting, stores, advisor

app = FastAPI(title="RetailMind API", version="2.0.0")

v1 = APIRouter(prefix="/api/v1")
v1.include_router(auth.router, prefix="/auth", tags=["Auth"])
v1.include_router(sales.router, prefix="/sales", tags=["Sales"])
v1.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
v1.include_router(forecasting.router, prefix="/forecast", tags=["Forecasting"])
v1.include_router(stores.router, prefix="/stores", tags=["Stores"])
v1.include_router(advisor.router, prefix="/advisor", tags=["AI Advisor"])

app.include_router(v1)
```

### 4.4 Background Tasks for ML

Currently ML computations (K-Means, Holt-Winters) likely run synchronously in request handlers, blocking the event loop. Move to background workers:

```python
# Use FastAPI BackgroundTasks for lightweight jobs
# Use Celery + Redis for heavier batch recomputation

from fastapi import BackgroundTasks

@router.post("/upload")
async def upload_sales(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    records = await parse_and_save(file, db, user)
    background_tasks.add_task(recompute_ml_metadata, user.id, db)
    return {"uploaded": len(records), "status": "processing"}
```

For the portfolio matrix (K-Means) and forecasting (Holt-Winters), add a dedicated endpoint that returns a job ID and allows the frontend to poll for completion — preventing timeouts on large datasets.

### 4.5 Streaming for AI Advisor

The Retail Advisor currently likely sends a single blocking response. Switch to Server-Sent Events (SSE) streaming:

```python
from fastapi.responses import StreamingResponse
import google.generativeai as genai

@router.post("/advisor/chat")
async def chat(request: ChatRequest, user: User = Depends(current_user)):
    async def generate():
        model = genai.GenerativeModel(settings.gemini_model)
        async for chunk in await model.generate_content_async(
            build_prompt(request, user), stream=True
        ):
            yield f"data: {chunk.text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 4.6 CSV/XLSX Upload — Upgrade Parser

Current parser handles 15+ column aliases. Improvements:

- Add `pandas` chunked reading for files > 10k rows (`pd.read_csv(..., chunksize=5000)`)
- Add server-side validation with detailed error responses (row number + column + reason)
- Support `date` column in 12+ formats using `dateutil.parser`
- Return a preview of first 5 parsed rows before full commit (two-phase upload)
- Add duplicate detection: hash `(product_sku, sale_date, quantity, user_id)` and warn on collision

### 4.7 Error Handling & Observability

```python
# Structured error responses
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": str(exc) if settings.environment == "development" else "An error occurred"}
    )
```

Add structured logging with `structlog` — outputs JSON in production, human-readable in dev. Antigravity IDE can parse JSON logs for error tracing.

---

## 5. Frontend (React + Vite) Upgrades

### 5.1 Migrate to TypeScript

This is the most impactful single change. Convert all `.jsx` → `.tsx` and all `.js` → `.ts`.

**Migration order (safest path):**
1. Add `tsconfig.json` with `"allowJs": true` — existing JS still works
2. Convert `types/` and `api/` files first (highest ROI for IDE)
3. Convert hooks, then store, then components
4. Remove `"allowJs": true` when done

**Shared types file (`src/types/index.ts`):**
```typescript
export interface User {
  id: string
  email: string
  fullName: string
  storeName: string
  currency: string
  isOnboarded: boolean
}

export interface SaleRecord {
  id: string
  productName: string
  productSku?: string
  productCategory: string
  quantitySold: number
  unitPrice: number
  totalRevenue: number
  cogs?: number
  grossMargin?: number
  saleDate: string
  customerSegment?: 'Walk-in' | 'Online' | 'B2B'
  currency: string
  storeId?: string
}

export interface KPIData {
  totalRevenue: number
  totalMargin: number
  avgOrderValue: number
  totalOrders: number
  topProducts: ProductSummary[]
  revenueByDay: TimeSeriesPoint[]
}

export interface Alert {
  id: string
  alertType: 'dead_stock' | 'margin_erosion' | 'demand_spike'
  productName: string
  severity: 'info' | 'warning' | 'critical'
  payload: Record<string, unknown>
  isRead: boolean
  createdAt: string
}
```

### 5.2 State Management — Zustand

Replace any ad-hoc prop drilling or Context with Zustand stores:

```
frontend/src/store/
├── authStore.ts        ← user, tokens, login/logout
├── salesStore.ts       ← sale records, filters, pagination
├── analyticsStore.ts   ← KPI data, chart data
├── uiStore.ts          ← sidebar open/close, active page, theme
├── alertsStore.ts      ← unread alerts count, alert list
└── storeStore.ts       ← active store, store list (multi-store)
```

```typescript
// store/authStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@types'

interface AuthState {
  user: User | null
  accessToken: string | null
  setUser: (user: User, token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      setUser: (user, accessToken) => set({ user, accessToken }),
      logout: () => set({ user: null, accessToken: null }),
    }),
    { name: 'auth' }
  )
)
```

### 5.3 API Layer — Centralized with `@api`

Replace scattered `fetch()` calls with a typed API client:

```typescript
// api/client.ts
import { useAuthStore } from '@store/authStore'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = useAuthStore.getState().accessToken
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  })
  if (!res.ok) throw new APIError(res.status, await res.json())
  return res.json()
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    refresh: () => request<{ access_token: string }>('/auth/refresh', { method: 'POST' }),
  },
  analytics: {
    getKPIs: (storeId?: string, dateRange?: DateRange) =>
      request<KPIData>(`/analytics/kpis${buildQuery({ storeId, ...dateRange })}`),
    getPortfolioMatrix: () => request<PortfolioMatrix>('/analytics/portfolio'),
  },
  // ... etc
}
```

### 5.4 React Query for Server State

Add `@tanstack/react-query` for caching, background refetch, and loading states:

```typescript
// hooks/useKPIs.ts
import { useQuery } from '@tanstack/react-query'
import { api } from '@api/client'

export function useKPIs(storeId?: string, dateRange?: DateRange) {
  return useQuery({
    queryKey: ['kpis', storeId, dateRange],
    queryFn: () => api.analytics.getKPIs(storeId, dateRange),
    staleTime: 5 * 60 * 1000,  // 5 min cache
    retry: 2,
  })
}
```

This eliminates all manual `useEffect` + `useState` data-fetching patterns and gives the IDE a clear `queryKey` taxonomy to navigate.

### 5.5 Routing — React Router v7

Upgrade to React Router v7 with file-based route conventions:

```
frontend/src/pages/
├── (auth)/
│   ├── login.tsx
│   └── register.tsx
├── (app)/
│   ├── _layout.tsx          ← sidebar + topbar shell
│   ├── dashboard.tsx        ← Intelligence Briefing
│   ├── forecast.tsx         ← Demand Forecasting
│   ├── portfolio.tsx        ← Portfolio Matrix
│   ├── customers.tsx        ← Customer Segments
│   ├── alerts.tsx           ← Smart Alerts
│   ├── advisor.tsx          ← AI Chat
│   ├── import.tsx           ← CSV/XLSX Upload
│   ├── ledger.tsx           ← Sales Ledger + Export
│   └── settings.tsx
└── index.tsx                ← redirects to /dashboard
```

---

## 6. UI/UX Component-by-Component Overhaul

### 6.1 Design System Foundation

Create a token-based design system before touching any components:

```
frontend/src/components/ui/
├── tokens.css               ← CSS custom properties
├── Button.tsx
├── Card.tsx
├── Badge.tsx
├── Input.tsx
├── Select.tsx
├── Modal.tsx
├── Skeleton.tsx             ← loading placeholders
├── Toast.tsx                ← notifications
├── Tooltip.tsx
├── DataTable.tsx            ← sortable, filterable, paginated
└── Chart/
    ├── LineChart.tsx
    ├── BarChart.tsx
    ├── ScatterChart.tsx     ← Portfolio Matrix
    └── AreaChart.tsx
```

**`tokens.css`:**
```css
:root {
  /* Colors */
  --color-brand: #6366f1;
  --color-brand-hover: #4f46e5;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-surface: #ffffff;
  --color-surface-muted: #f8fafc;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #64748b;

  /* Spacing */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px;
  --space-4: 16px; --space-6: 24px; --space-8: 32px;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Radii */
  --radius-sm: 6px; --radius-md: 10px; --radius-lg: 16px;

  /* Shadows */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
}

[data-theme="dark"] {
  --color-surface: #0f172a;
  --color-surface-muted: #1e293b;
  --color-border: #334155;
  --color-text: #f1f5f9;
  --color-text-muted: #94a3b8;
}
```

### 6.2 Component Upgrades by Feature

#### Intelligence Briefing (Dashboard)

**Current issues:** KPI cards likely use hardcoded styles; charts probably re-fetch on every render; no skeleton states.

**Upgrades:**
- KPI cards: add sparkline micro-charts (7-day trend inline in card), delta badges (+12% vs last month), and currency formatting via `Intl.NumberFormat`
- Revenue trend: upgrade from basic line to area chart with gradient fill and zoom/pan controls
- Top products table: add inline mini bar chart per row showing revenue share
- Add date range picker (Last 7d / 30d / 90d / Custom) that syncs all widgets simultaneously
- Add store selector dropdown if multi-store — context persisted in `uiStore`
- Skeleton loading for all cards (prevents layout shift)

#### Demand Forecasting

**Current issues:** Holt-Winters output probably shown as static chart; no confidence intervals; no product filter.

**Upgrades:**
- Show forecast confidence bands (shaded area between lower/upper bounds)
- Add product/category filter so users can forecast individual SKUs
- Show "accuracy score" from last forecast vs actual (MAE, MAPE)
- Add export forecast as CSV button
- Streaming progress indicator while model runs for large datasets

#### Portfolio Matrix (K-Means)

**Current issues:** Static scatter chart; quadrant labels may not be accessible; no drill-down.

**Upgrades:**
- Interactive scatter (recharts `<ScatterChart>`): hover to see product details tooltip
- Click a dot → slide-over panel with full product analytics
- Quadrant legend with count badges (e.g., "Stars (12)", "Dead Weight (4)")
- Add "Recommended Actions" AI panel below the matrix (call Gemini with cluster context)
- Color-blind safe palette (use shape + color, not color alone)
- Allow adjusting K (number of clusters) from 3–6 via slider

#### Customer Segments

**Current issues:** Walk-in/Online/B2B split likely shown as pie chart — pies are hard to read.

**Upgrades:**
- Replace pie with stacked bar over time (monthly breakdown per segment)
- Add avg order value, top product, and visit frequency per segment
- Cohort retention mini-table for returning customers
- Segment comparison mode: select two segments and overlay metrics

#### Smart Alerts

**Current issues:** Alerts likely shown as a static list with no persistence or dismissal.

**Upgrades:**
- Persist alerts to the new `alerts` DB table (survives page refresh)
- Unread badge on nav item
- Alert severity color coding: info (blue), warning (amber), critical (red)
- One-click dismiss (mark as read) or "Take Action" button linking to relevant page
- Alert history tab (last 90 days)
- Email digest: weekly alert summary (add background task + SMTP config)

#### Retail Advisor (AI Chat)

**Current issues:** Likely full-page reload per message; no streaming; no conversation persistence.

**Upgrades:**
- Implement SSE streaming (see §4.5) — tokens appear as they're generated
- Persist conversation history in `ai_conversations` table — survives refresh
- Auto-inject current KPI snapshot as context with each message
- Add pre-built prompt chips: "What's dragging down my margin?", "Which products should I reorder?", "Why did sales drop last week?"
- Show data citations inline: when Gemini references a product, render a mini-card
- Add "Share this answer" button (copies formatted text to clipboard)

#### Data Import (CSV/XLSX Upload)

**Current issues:** Single-step upload with no preview; unclear error messages.

**Upgrades:**
- Two-phase upload: parse → preview table (first 10 rows) → confirm → commit
- Column mapping UI: if auto-detection fails, show drag-and-drop column matcher
- Progress bar for large files with per-chunk feedback
- Error report: download a CSV of rows that failed validation with reasons
- Drag-and-drop zone with file type validation before upload
- Support Google Sheets URL import (fetch as CSV via Sheets export link)

#### Sales Ledger

**Current issues:** Basic table with CSV export; likely no server-side pagination.

**Upgrades:**
- Server-side pagination (limit/offset or cursor-based)
- Column sorting (click header to sort)
- Multi-filter UI: date range + category + segment + store + SKU search
- Inline edit: click a cell to correct a value without full page reload
- Bulk actions: delete selected rows, re-categorize, export selection
- Full-text search (powered by the `search_vector` GIN index from §3.3)

#### Navigation / Shell

**Current issues:** Unknown — likely a basic sidebar.

**Upgrades:**
- Collapsible sidebar with icon-only mode (saves space)
- Keyboard shortcuts for every page (`G` then `D` = go to Dashboard, etc.)
- Global search bar (`Cmd+K`) — searches products, pages, and AI advisor
- Dark mode toggle with `data-theme` attribute on `<html>`
- Breadcrumbs on every page
- Mobile-responsive drawer (hamburger menu on < 768px)
- Notification bell with unread alert count

### 6.3 Accessibility (a11y)

- All interactive elements must have `aria-label` or visible label
- Keyboard navigation: Tab order follows visual layout
- Color contrast: minimum 4.5:1 for text (WCAG AA)
- Charts: add `role="img"` with descriptive `aria-label`
- Form errors announced via `aria-live="polite"`
- Run `axe-core` in CI as part of Playwright tests

---

## 7. AI / ML Engine Upgrades

### 7.1 Gemini Integration

**Current:** Uses `gemini-2.5-flash`, likely with a static prompt.

**Upgrades:**
- Switch to structured output mode (Gemini `response_schema`) for data-extraction queries
- Build a RAG-lite layer: store product summaries in PostgreSQL `pgvector` extension, do similarity search before calling Gemini to provide relevant context
- Add a system prompt library (`backend/app/services/prompts.py`) with versioned prompt templates
- Rate-limit AI calls per user per hour (track in Redis or PostgreSQL)
- Cache identical prompts + KPI snapshots (if data unchanged in 10 min, return cached response)

### 7.2 Forecasting (Holt-Winters) Upgrades

- Add `Prophet` (Meta's library) as an alternative model for products with strong weekly seasonality
- Run both models and return the one with lower cross-validated MAE
- Store forecast results in DB to avoid recomputing on every page load
- Expose confidence interval width as a "forecast reliability" score (shown to user)
- Add anomaly detection: flag actual sales that deviate > 2σ from forecast

### 7.3 Portfolio Matrix (K-Means) Upgrades

- Use `MiniBatchKMeans` for datasets > 5k SKUs (10x faster)
- Run silhouette score analysis to auto-select optimal K (3–6)
- Add UMAP dimensionality reduction for visualization when features > 2
- Persist cluster assignments in `sale_records.ml_meta` JSONB so they can be queried
- Schedule weekly recomputation as a background job

### 7.4 Dead Stock / Margin Alerts

Current logic is likely a simple threshold check. Upgrade to:
- Dynamic thresholds: alert when a product's sales velocity drops > 40% below its own 90-day average (not a fixed number)
- Margin erosion: alert when COGS increases but price stays flat → gross margin drops > 5pp
- Competitive demand spike: alert when a category's week-over-week growth > 3σ above baseline

---

## 8. DevOps, Deployment & CI/CD

### 8.1 Docker

Add `Dockerfile` for each service:

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
RUN uv pip install --system .
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```dockerfile
# frontend/Dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**`docker-compose.yml` for local dev:**
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: retailmind
      POSTGRES_USER: retailmind
      POSTGRES_PASSWORD: dev_password
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  backend:
    build: ./backend
    env_file: ./backend/.env
    ports: ["8000:8000"]
    depends_on: [db]
    volumes: ["./backend:/app"]
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    volumes: ["./frontend/src:/app/src"]
    command: npm run dev -- --host

volumes:
  pgdata:
```

### 8.2 GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI
on: [pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_DB: test, POSTGRES_USER: test, POSTGRES_PASSWORD: test }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install uv && uv pip install --system ".[dev]"
        working-directory: backend
      - run: ruff check . && mypy app/
        working-directory: backend
      - run: pytest -v --cov=app
        working-directory: backend

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci && npx tsc --noEmit && npm run test
        working-directory: frontend
```

### 8.3 Deployment Config Fixes

**`vercel.json` — current config uses `experimentalServices` which is fragile.**

Replace with proper split deployment:
- Frontend → Vercel (standard Vite deployment, no experimental config)
- Backend → Railway (better Python support than Render free tier)

**Fix the hardcoded CORS origins** in `render.yaml` — move to an environment variable so deployment URL changes don't require a config file edit.

### 8.4 Add Redis

Used for:
- Rate limiting AI advisor calls
- Caching KPI queries (5-minute TTL)
- Celery task queue for background ML jobs

```yaml
# docker-compose.yml addition
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

---

## 9. Security Hardening

### 9.1 JWT Security

- Current: JWT + refresh token rotation — good foundation.
- Add: `jti` (JWT ID) claim to access tokens; store `jti` blacklist in Redis for instant revocation on logout
- Add: device fingerprint check on refresh (user-agent hash)
- Reduce access token expiry from likely 30 min → 15 min

### 9.2 Upload Security

- Validate file magic bytes, not just extension (a `.csv` can be a zip bomb)
- Set maximum upload size: 10 MB hard limit in FastAPI + nginx
- Scan for formula injection in CSV cells (`=CMD(...)`) before inserting
- Run uploads in isolated async worker, not in the request handler

### 9.3 Database Security

- Use connection pooling (PgBouncer or SQLAlchemy pool) — never open a new connection per request
- Row-level security: add `user_id` filter in every query at the ORM level, never trust client-provided IDs alone
- Audit log: add `updated_at` + `updated_by` to critical tables

### 9.4 API Security

- Add rate limiting: `slowapi` library for FastAPI (`@limiter.limit("100/minute")`)
- Validate all UUIDs in path params before DB query (avoids SQL injection surface)
- Add `Content-Security-Policy` and `X-Frame-Options` headers in production
- Enable HTTPS redirect enforcement in production uvicorn config

---

## 10. Testing Strategy

### 10.1 Backend Tests

```
backend/tests/
├── conftest.py             ← async fixtures, test DB setup
├── unit/
│   ├── test_auth_service.py
│   ├── test_sales_parser.py   ← CSV/XLSX parsing edge cases
│   ├── test_ml_clustering.py
│   └── test_ml_forecasting.py
└── integration/
    ├── test_auth_routes.py
    ├── test_sales_routes.py
    ├── test_analytics_routes.py
    └── test_advisor_routes.py
```

Target: **>80% coverage** on `services/` and `ml/` modules.

Key test cases:
- CSV upload with 15 different column alias combinations
- K-Means with 1 product, 2 products, 100 products (edge cases)
- JWT expiry + refresh token rotation flow
- Concurrent upload handling (two uploads for same user simultaneously)

### 10.2 Frontend Tests

- Unit: `vitest` + `@testing-library/react` for all hooks and utility functions
- Component: snapshot tests for all UI components in `/ui`
- E2E: `Playwright` for critical paths: login → upload CSV → view dashboard → chat with advisor

### 10.3 Load Testing

Add `locust` load test for the analytics endpoints — these are the heaviest queries:

```python
# tests/load/locustfile.py
from locust import HttpUser, task

class RetailMindUser(HttpUser):
    @task
    def get_kpis(self):
        self.client.get("/api/v1/analytics/kpis", headers=self.auth_headers)

    @task(0.3)
    def get_portfolio(self):
        self.client.get("/api/v1/analytics/portfolio", headers=self.auth_headers)
```

---

## 11. Priority Execution Roadmap

### Phase 1 — Foundation (Week 1–2)
**Do these before anything else. Everything else depends on them.**

- [ ] Add `.antigravity/context.json` and `jsconfig.json`
- [ ] Restructure `backend/app/` into routers/models/schemas/services/ml
- [ ] Add `pyproject.toml` + `uv` lockfile
- [ ] Add `Makefile` with `make dev` and `make test`
- [ ] Set up Alembic, convert `schema.sql` to initial migration
- [ ] Add `docker-compose.yml` for local dev
- [ ] Add GitHub Actions CI (lint + test)

### Phase 2 — TypeScript Migration (Week 2–3)
- [ ] Add `tsconfig.json` with `allowJs: true`
- [ ] Create `src/types/index.ts` with all shared interfaces
- [ ] Migrate `src/api/` to typed client
- [ ] Migrate `src/hooks/` to typed hooks with React Query
- [ ] Migrate `src/store/` to Zustand

### Phase 3 — Backend Upgrades (Week 3–4)
- [ ] Schema additions (alerts table, ai_conversations table, FTS index)
- [ ] Typed config with `pydantic-settings`
- [ ] Background tasks for ML recomputation
- [ ] SSE streaming for AI Advisor
- [ ] Two-phase CSV upload with preview
- [ ] Rate limiting + security headers

### Phase 4 — UI/UX Overhaul (Week 4–6)
- [ ] Design token CSS + dark mode
- [ ] Skeleton loading states on all pages
- [ ] Dashboard: date range picker, sparklines, area chart
- [ ] Smart Alerts: DB persistence, severity UI, unread badge
- [ ] AI Advisor: streaming, conversation history, prompt chips
- [ ] Data Import: preview table, column mapper, error CSV download
- [ ] Navigation: collapsible sidebar, Cmd+K search, keyboard shortcuts

### Phase 5 — ML & AI Upgrades (Week 6–7)
- [ ] Confidence intervals on forecasting chart
- [ ] Dynamic alert thresholds
- [ ] pgvector RAG for AI Advisor context
- [ ] Silhouette score auto-K selection for K-Means
- [ ] Forecast result caching in DB

### Phase 6 — Production Hardening (Week 7–8)
- [ ] Playwright E2E test suite
- [ ] Load testing with locust
- [ ] JWT blacklist with Redis
- [ ] Deploy split: Vercel (frontend) + Railway (backend) with fixed CORS config
- [ ] Sentry error tracking live in production
- [ ] Remove legacy `budgets` and `transactions` tables

---

## Appendix: Antigravity IDE Checklist

Use this as a pre-commit checklist to ensure every new file is IDE-friendly:

- [ ] File has a single clear responsibility (< 200 lines preferred)
- [ ] All functions have type annotations (Python) or TypeScript types
- [ ] Imports use path aliases (`@components/`, `app.services.`) not relative `../../../`
- [ ] No magic strings — constants live in `config.py` or `constants.ts`
- [ ] Every public function has a JSDoc / docstring (one-line minimum)
- [ ] New API routes are registered in `api-map.json`
- [ ] New components are registered in `component-map.json`
- [ ] `make lint` passes before push

---

*This document is a living spec. Update the roadmap checkboxes as work is completed. Treat Phase 1 as non-negotiable before any feature work begins.*

---

---

# PART II — Demo Mode Specification
> **Requirement:** Authentication completely disabled. A fully public, pixel-perfect showcase of every feature. Users can clear pre-seeded data and upload their own CSV/XLSX at any time, triggering full ML recomputation with a loading screen. Charts are semi-interactive (filters work, data pre-cached on load).

---

## 12. Demo Mode Architecture

### 12.1 Core Design Principle

Demo Mode is **not a dumbed-down version** of RetailMind. It is the full product, running against a fixed demo identity, with auth bypassed at every layer. The experience must be indistinguishable from a logged-in production session — except there is no login screen.

### 12.2 How Auth Gets Disabled

**Backend — one environment variable controls everything:**

```python
# backend/app/config.py
class Settings(BaseSettings):
    demo_mode: bool = False
    demo_user_id: str = "00000000-0000-0000-0000-000000000001"  # fixed UUID
    demo_store_id: str = "00000000-0000-0000-0000-000000000002"
```

**FastAPI dependency override:**

```python
# backend/app/dependencies.py
from app.config import settings
from app.models.user import User

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if settings.demo_mode:
        # Skip ALL token validation — return the seeded demo user directly
        return await db.get(User, settings.demo_user_id)
    # ... normal JWT validation
```

Every single route already uses `Depends(get_current_user)` — so flipping `DEMO_MODE=true` in the environment disables auth globally with zero route-level changes.

**Frontend — hide all auth UI:**

```typescript
// frontend/src/config.ts
export const IS_DEMO = import.meta.env.VITE_DEMO_MODE === 'true'

// frontend/src/main.tsx
if (IS_DEMO) {
  // Pre-load auth store with a synthetic demo token
  useAuthStore.setState({
    user: DEMO_USER,
    accessToken: 'demo-passthrough',
    isDemoMode: true,
  })
}
```

```typescript
// frontend/src/App.tsx
const router = IS_DEMO
  ? createBrowserRouter(demoRoutes)   // no /login, no /register, redirects root → /dashboard
  : createBrowserRouter(appRoutes)    // normal routes with auth guards
```

**What gets hidden in Demo Mode:**
- Login and Register pages removed from routing entirely
- "Change password" and "Billing" settings tabs hidden
- Profile avatar shows "Demo Store" with a lock icon tooltip
- A persistent **Demo Mode banner** appears at the top of every page (see §12.5)

### 12.3 Demo Data Specification — Last 90 Days

The seeded dataset must be rich enough for every ML feature to produce meaningful, impressive outputs. Here is the exact spec:

**Store:** `RetailMind Demo Store` · Currency: `USD` · Timezone: `UTC`

**Date range:** `TODAY - 90 days` → `TODAY` (dynamically computed at seed time so the demo always feels current)

**Products & Categories (minimum for good ML outputs):**

| Category | Products | SKUs | Notes |
|---|---|---|---|
| Electronics | 8 | E001–E008 | High margin, moderate volume |
| Apparel | 12 | A001–A012 | High volume, lower margin, seasonal |
| Food & Beverage | 6 | F001–F006 | Very high frequency, thin margin |
| Home & Garden | 5 | H001–H005 | Low velocity — produces Dead Weight alerts |
| Stationery | 4 | S001–S004 | Steady cash cow behaviour |

**Volume targets (for ML quality):**
- Minimum **2,000 sale records** across 90 days
- At least **3 products with zero sales in last 30 days** → triggers Dead Stock alerts
- At least **2 products with margin below 10%** → triggers Margin Erosion alerts
- At least **1 product with week-over-week spike > 150%** → triggers Demand Spike alert
- Customer segments: `Walk-in` 45%, `Online` 35%, `B2B` 20%
- Revenue pattern: steady with a visible **Black Friday / month-end spike** in the most recent period

**Seed script (`backend/scripts/seed_demo_account.py`) must:**
1. Check if demo user already exists — skip seeding if yes (idempotent)
2. Generate dates dynamically: `base_date = date.today() - timedelta(days=90)`
3. Use `faker` library for realistic product names, not lorem ipsum
4. Inject pre-computed `ml_meta` JSONB on records so first-load ML is instant
5. Be runnable as: `make seed` or `python scripts/seed_demo_account.py --force` (force re-seeds)

### 12.4 Data Reset + Upload Flow (The Crown Jewel Feature)

This is the most important UX in demo mode. It must be flawless.

**Reset & Upload Button placement:**
- Primary CTA in the top-right of the **Data Import** page
- Also accessible via the **Demo Mode banner** ("Upload your own data →")
- Keyboard shortcut: `Cmd+U`

**The full flow, step by step:**

```
Step 1 — Confirmation Modal
  ┌─────────────────────────────────────────────────────┐
  │  🔄  Reset Demo Data                                 │
  │                                                      │
  │  This will clear all current demo records and        │
  │  replace them with your file. All ML models will     │
  │  recompute. This takes 15–60 seconds.                │
  │                                                      │
  │  [ Cancel ]              [ Clear & Upload My Data ]  │
  └─────────────────────────────────────────────────────┘

Step 2 — File Drop Zone (appears after confirmation)
  - Accepts: .csv, .xlsx, .xls
  - Shows column alias reference (same 15 aliases as production)
  - Download template button
  - Drag-and-drop OR click-to-browse

Step 3 — Parse & Preview
  - Backend parses file, returns first 10 rows + column mapping
  - Show preview table with detected column assignments
  - If any column is undetected → show column mapper dropdown
  - Show row count, date range detected, SKU count
  - [ Back ] [ Confirm & Run Analysis ]

Step 4 — Loading / Computation Screen (full-page overlay)
  ┌─────────────────────────────────────────────────────┐
  │                                                      │
  │   Analysing your data...                             │
  │                                                      │
  │   ✅  2,847 records imported                         │
  │   ⏳  Running demand forecasting...                  │
  │   ⏳  Building portfolio matrix...                   │
  │   ⏳  Detecting alerts...                            │
  │   ⏳  Segmenting customers...                        │
  │                                                      │
  │   [████████████░░░░░░░░]  62%                        │
  │                                                      │
  │   This usually takes 20–45 seconds                   │
  └─────────────────────────────────────────────────────┘
  - Each step checks off in real-time via SSE progress stream
  - Progress percentages: Import 20% → Forecast 40% → Clusters 60% → Alerts 75% → Segments 90% → Done 100%

Step 5 — Success & Reveal
  - Overlay fades out
  - Dashboard animates in with new data
  - Toast: "Your data is live! Showing insights for [date range]."
  - All charts, alerts, advisor context updated to new dataset
```

**Backend implementation — the reset endpoint:**

```python
# POST /api/v1/demo/reset-and-upload
@router.post("/demo/reset-and-upload")
async def demo_reset_and_upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),  # returns demo user in demo mode
):
    if not settings.demo_mode:
        raise HTTPException(403, "Not available outside demo mode")

    # 1. Hard-delete all sale_records for demo user
    await db.execute(
        delete(SaleRecord).where(SaleRecord.user_id == user.id)
    )
    await db.commit()

    # 2. Parse uploaded file (reuse existing parser)
    records = await parse_upload_file(file, user)
    db.add_all(records)
    await db.commit()

    # 3. Enqueue full ML recomputation with SSE progress
    job_id = str(uuid4())
    background_tasks.add_task(run_full_ml_pipeline, user.id, job_id)

    return {"job_id": job_id, "record_count": len(records)}

# GET /api/v1/demo/progress/{job_id}  — SSE stream
@router.get("/demo/progress/{job_id}")
async def demo_progress(job_id: str):
    async def stream():
        async for update in get_job_progress(job_id):
            yield f"data: {json.dumps(update)}\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")
```

**ML pipeline execution order and timing estimates:**

```python
async def run_full_ml_pipeline(user_id: str, job_id: str):
    await emit_progress(job_id, "import", 20, "Records imported")
    
    await run_demand_forecasting(user_id)        # Holt-Winters per SKU
    await emit_progress(job_id, "forecast", 40, "Demand forecasting complete")
    
    await run_portfolio_clustering(user_id)      # K-Means
    await emit_progress(job_id, "clusters", 60, "Portfolio matrix built")
    
    await run_alert_detection(user_id)           # Dead stock + margin erosion
    await emit_progress(job_id, "alerts", 75, "Smart alerts generated")
    
    await run_segment_analysis(user_id)          # Walk-in / Online / B2B
    await emit_progress(job_id, "segments", 90, "Customer segments ready")
    
    await cache_kpi_snapshot(user_id)            # Pre-cache for fast first load
    await emit_progress(job_id, "done", 100, "Analysis complete")
```

**Also: restore to original demo data button**

After a user uploads their own file, show a secondary CTA: `← Restore demo data`. This re-runs the seed script for the demo user only.

### 12.5 Demo Mode Banner

A fixed top banner, always visible, zero visual hierarchy conflict with the main UI:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  👁  DEMO MODE  ·  Showing 90-day sample dataset  ·  [ Upload Your Data ]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

- Height: 36px, sits above the main nav
- Background: `#1e293b` (dark slate) with white text — doesn't clash with any chart color
- "Upload Your Data" is a teal pill button → opens the reset flow directly
- In the right corner: `[ Restore Demo Data ]` link (appears only after user has uploaded their own file)
- Banner is NOT dismissible — demo mode is always explicit

---

## 13. ML Feature Showcase Specifications

### 13.1 Demand Forecasting — Holt-Winters Charts

**What the demo must show convincingly:**

The 90-day seeded dataset is specifically crafted to produce a compelling forecast — visible trend + weekly seasonality. The chart must show:

- **Actual sales** line (solid, brand color) for the full 90-day history
- **Forecast line** (dashed, lighter) extending 30 days into the future
- **Confidence band** (shaded area, 20% opacity) — upper and lower bounds
- **Anomaly markers** — orange dots on dates where actual deviated > 2σ from model
- **Accuracy badge** — "Model accuracy: 87.3% (MAE: $142)" shown in chart header

**Filter controls (pre-cached, semi-interactive):**
- Product / SKU dropdown — switches chart to per-product forecast (data pre-cached on load for all SKUs in demo)
- Forecast horizon: 14d / 30d / 60d toggle
- Smoothing level: Auto / Manual slider (shows how α, β, γ affect the curve — great for demos)

**Chart interactions:**
- Hover tooltip: shows date, actual value, forecast value, and confidence range
- Click on anomaly marker → popover explaining "Sales 234% above forecast — possible promotion or external event"
- Zoom: scroll-to-zoom on date axis (recharts built-in)

**Empty state (if user uploads sparse data):** "Your dataset needs at least 14 days of sales for 1 product to generate a forecast. Currently showing [N] qualifying products."

### 13.2 Portfolio Matrix — K-Means Clustering

**What the demo must show convincingly:**

The seeded data is designed so K-Means cleanly separates into 4 quadrants with no ambiguous middle-cluster products.

- **Axes:** X = Revenue contribution (%), Y = Sales velocity (units/day)
- **Dot size:** proportional to gross margin %
- **Color + label:** Stars (green), Cash Cows (blue), Hidden Gems (amber), Dead Weight (red/grey)
- **Quadrant shading:** subtle background fill per quadrant with label in corner
- **Count badges** in legend: "Stars (3)", "Cash Cows (8)", "Hidden Gems (5)", "Dead Weight (4)"

**Interactions (pre-cached):**
- Hover dot → tooltip with product name, SKU, revenue, velocity, margin, cluster label
- Click dot → slide-over panel (right side, 400px) with:
  - Full 90-day sales sparkline for that product
  - Recommended action from Gemini (pre-generated at seed time, cached in `ml_meta`)
  - "Ask Advisor about this product →" button that pre-fills the chat
- Category filter dropdown — filters dots to one category at a time
- K slider (3–6) → triggers recomputation with loading spinner (this one is truly live, not cached — it's fast enough)

**Recommended action strings (pre-generated in seed, stored in `sale_records.ml_meta`):**

```json
{
  "cluster": "Dead Weight",
  "recommended_action": "Consider a 20–30% clearance discount to liquidate stock. Last sold 34 days ago. Holding cost exceeds projected revenue at current velocity.",
  "action_cta": "Mark for clearance"
}
```

### 13.3 Smart Alerts — Dead Stock, Margin Erosion, Demand Spikes

**Alert generation rules (deterministic, not probabilistic — so demo always has alerts):**

The seed script deliberately creates:

- **3 Dead Stock alerts** — products with zero sales in last 30 days, with last sale date shown
- **2 Margin Erosion alerts** — products where COGS increased but price held flat, margin dropped > 8pp in last 30 days
- **1 Demand Spike alert** — one product with 200%+ WoW growth in most recent week

**Alerts page layout:**

```
┌── CRITICAL ──────────────────────────────────────────────────────┐
│  🔴  Margin Erosion — "Premium Wireless Headphones" (E003)        │
│      Gross margin dropped from 42% → 31% over 30 days            │
│      COGS increased $8.40/unit. Price unchanged at $129.99        │
│      [ View Product ]  [ Ask Advisor ]  [ Dismiss ]              │
└──────────────────────────────────────────────────────────────────┘

┌── WARNING ───────────────────────────────────────────────────────┐
│  🟡  Dead Stock — "Bamboo Garden Planter Set" (H004)              │
│      Last sold: 38 days ago. Estimated holding cost: $340/month  │
│      [ Mark for Clearance ]  [ Ask Advisor ]  [ Dismiss ]        │
└──────────────────────────────────────────────────────────────────┘
```

**"Ask Advisor" button:** Pre-fills the AI chat with the exact alert context — e.g., "The Bamboo Garden Planter Set hasn't sold in 38 days. What should I do?" and auto-submits.

**After user uploads own data:** Alert detection reruns and shows their actual alerts. If no alerts exist in their data, show a green "All Clear" state with a subtle animation — not an empty blank page.

### 13.4 AI Retail Advisor — Gemini Chat

**Demo mode AI context injection:**

Every chat message to Gemini in demo mode is prefixed with a snapshot of the current dataset state:

```python
DEMO_SYSTEM_PROMPT = """
You are the RetailMind AI Retail Advisor. You have access to the following store data:

Store: {store_name}
Period: {date_range}
Total Revenue: {total_revenue}
Top Category: {top_category}
Active Alerts: {alert_count} ({alert_summary})
Worst Performing Product: {dead_weight_product}
Best Performing Product: {star_product}

Answer questions as a concise, data-savvy retail analyst. Reference specific products,
numbers, and dates from the data above. Never give generic advice — always tie it to
the actual numbers. Keep responses under 200 words unless asked for detail.
"""
```

**Pre-built prompt chips shown above the chat input (demo page):**

```
[ What's dragging down my margin? ]
[ Which products should I reorder this week? ]
[ Why did sales spike on [most recent spike date]? ]
[ What should I clearance? ]
[ How does my B2B segment compare to Walk-in? ]
[ Give me a 30-day revenue forecast summary ]
```

Clicking a chip sends immediately — no need to type anything.

**Streaming response display:**
- Tokens stream in with a blinking cursor
- Numbers and product names render as highlighted `<mark>` tags
- At end of response, show 1–3 follow-up suggestion chips contextually generated

**Demo data freshness:** When user uploads their own file, the system prompt context snapshot is regenerated from their data before the next message.

### 13.5 Customer Segments Analytics

**Three segments: Walk-in · Online · B2B**

**Page layout:**

Top row — segment selector tabs with summary stats:
```
[ Walk-in  45% · $124 AOV ]  [ Online  35% · $187 AOV ]  [ B2B  20% · $892 AOV ]
```

Below — for the selected segment:
- Revenue over 90 days (area chart with segment color)
- Top 5 products for this segment (horizontal bar chart)
- Avg order value trend (line chart)
- Peak day of week heatmap (7 columns, color intensity = revenue)
- Returns rate and repeat purchase rate

**Comparison mode toggle:** "Compare segments" → overlays all three on one chart with distinct colors/patterns, color-blind safe.

**Filters (pre-cached):**
- Date range: Last 30d / 60d / 90d
- Category filter: All / Electronics / Apparel / etc.

### 13.6 Document / Receipt Scanning — Auto-Categorization

**Scope (per your selection):** Scan a document → extract line items → **auto-categorize each item** into the product taxonomy, then offer to add them to the ledger.

**Supported input formats:**
- PDF receipts/invoices
- JPEG/PNG photos of physical receipts (including slightly angled — Gemini Vision handles perspective)
- Scanned multi-page supplier invoices (PDF, up to 10 pages)

**Pipeline:**

```
Upload image/PDF
       ↓
Gemini Vision extracts structured data:
  {
    "line_items": [
      { "raw_text": "WIRELESS HDPHNS BLK 2x", "quantity": 2, "unit_price": 89.99 },
      { "raw_text": "GARDEN SET BAMB 1x",    "quantity": 1, "unit_price": 45.00 }
    ],
    "vendor": "Sunrise Wholesale",
    "document_date": "2025-02-14",
    "total": "224.98"
  }
       ↓
Category classification (second Gemini call with category taxonomy):
  "WIRELESS HDPHNS BLK" → Electronics
  "GARDEN SET BAMB"     → Home & Garden
       ↓
Show review UI to user
       ↓
User confirms / adjusts → records added to ledger
```

**Review UI:**

```
┌── Scanned Document — Sunrise Wholesale · Feb 14 2025 ────────────────────┐
│                                                                            │
│  Extracted 4 line items                                                    │
│                                                                            │
│  Product               Qty   Price    Category         Action              │
│  ─────────────────────────────────────────────────────────────────────    │
│  Wireless Headphones   2     $89.99   Electronics  ▾   ✓ Keep             │
│  Bamboo Garden Set     1     $45.00   Home & Garden ▾  ✓ Keep             │
│  USB-C Cable 3ft       5     $12.99   Electronics  ▾   ✓ Keep             │
│  Notebook A5           10    $3.50    Stationery   ▾   ✓ Keep             │
│                                                                            │
│  Category dropdowns are editable. Unchecked items are excluded.           │
│                                                                            │
│  [ Cancel ]                            [ Add 4 Items to Ledger ]         │
└────────────────────────────────────────────────────────────────────────────┘
```

**Demo mode behaviour:** In demo, the document scanner works fully against the demo store data. Scanned items add to the demo ledger and immediately show in the Sales Ledger page. They do NOT trigger a full ML recomputation (too slow for a single item scan) — instead show a toast: "Ledger updated. Recompute analysis? [ Yes, run analysis ]"

---

## 14. Charts — Storage & Caching Architecture

### 14.1 What "Semi-Interactive / Pre-Cached" Means

Charts are **not** static images. They are live Recharts components rendering real JSON. "Pre-cached" means the JSON payload is computed once (on page load / after upload) and stored — not recomputed per filter click.

**Cache architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    On Page Load                                  │
│                                                                  │
│  Frontend → GET /api/v1/analytics/chart-bundle                  │
│           ← { kpis, forecast_all_skus, portfolio, segments,     │
│               alerts, revenue_by_day, top_products }            │
│                                                                  │
│  React Query caches this bundle with staleTime: Infinity        │
│  (in demo mode — only invalidated after reset+upload)           │
│                                                                  │
│  Filter clicks (e.g., switch SKU in forecast) operate           │
│  on the in-memory bundle — ZERO additional API calls            │
└─────────────────────────────────────────────────────────────────┘
```

**Backend `chart-bundle` endpoint:**

```python
@router.get("/analytics/chart-bundle")
async def get_chart_bundle(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check Redis cache first (TTL: 5 min in production, infinite in demo)
    cache_key = f"chart_bundle:{user.id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Build full bundle
    bundle = {
        "kpis": await build_kpis(user.id, db),
        "revenue_by_day": await build_revenue_series(user.id, db),
        "top_products": await build_top_products(user.id, db),
        "forecast": await build_all_forecasts(user.id, db),   # per-SKU
        "portfolio": await build_portfolio_matrix(user.id, db),
        "segments": await build_segment_data(user.id, db),
        "alerts": await build_alerts(user.id, db),
        "generated_at": datetime.utcnow().isoformat(),
    }

    ttl = None if settings.demo_mode else 300  # infinite cache in demo
    await redis.set(cache_key, json.dumps(bundle), ex=ttl)
    return bundle
```

**After reset+upload:** The frontend invalidates the React Query cache (`queryClient.invalidateQueries(['chart-bundle'])`) and refetches once ML pipeline emits 100% progress.

### 14.2 What Data Is Stored Where

| Data Type | Storage | TTL / Persistence |
|---|---|---|
| Sale records | PostgreSQL `sale_records` | Permanent |
| ML cluster assignments | PostgreSQL `sale_records.ml_meta` JSONB | Updated per recomputation |
| Forecast results | PostgreSQL `ai_conversations.context_snapshot` / new `ml_results` table | Updated per recomputation |
| Smart alerts | PostgreSQL `alerts` table | Persistent until dismissed |
| AI conversations | PostgreSQL `ai_conversations` | Persistent (demo: scoped to demo user) |
| Chart bundle (full JSON) | Redis | Infinite in demo; 5 min in prod |
| Auth tokens | PostgreSQL `refresh_tokens` + Redis blacklist | Demo: not used |
| Document scan results | In-memory until user confirms → PostgreSQL | Ephemeral until confirmed |
| Demo user progress state | PostgreSQL (which step of reset flow) | Cleared on new reset |

**New table: `ml_results`** (add to migrations):

```sql
CREATE TABLE ml_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  result_type VARCHAR(50) NOT NULL,  -- 'forecast' | 'portfolio' | 'segments'
  payload JSONB NOT NULL,
  computed_at TIMESTAMPTZ DEFAULT NOW(),
  data_hash VARCHAR(64),             -- hash of input data; skip recompute if unchanged
  UNIQUE (user_id, result_type)      -- one current result per type per user
);
```

This is what the `chart-bundle` endpoint reads from — ML runs write here, charts read here. Clean separation.

---

## 15. Demo Mode — Additional UX Details

### 15.1 First-Time Visitor Experience

When someone hits the demo URL for the first time:

1. **Splash screen** (1.5 seconds, animated) — RetailMind logo + tagline "AI-powered retail intelligence for real business decisions"
2. **Auto-redirect to Dashboard** — no login, no onboarding wizard, straight to data
3. **Guided tooltip overlay** (optional, dismissible in one click):
   - Step 1: "These are your KPIs — revenue, margin, and order volume for the last 90 days"
   - Step 2: "Click any chart to drill down"
   - Step 3: "Try the AI Advisor — ask it anything about your store"
   - Step 4: "Upload your own data anytime from the Import page"
4. Tooltip state stored in `localStorage` — never shown again after dismissed

### 15.2 Navigation in Demo Mode

Sidebar items and their demo behaviour:

| Page | Demo Behaviour |
|---|---|
| Dashboard | Fully live — KPI cards, revenue trend, top products |
| Demand Forecast | Fully live — all SKUs pre-cached |
| Portfolio Matrix | Fully live — interactive scatter |
| Customer Segments | Fully live — all three segments |
| Smart Alerts | Fully live — 6 pre-seeded alerts |
| AI Advisor | Fully live — Gemini chat with demo context |
| Data Import | **Primary demo action page** — clear + upload flow |
| Sales Ledger | Fully live — sortable, filterable, paginated |
| Settings | Hidden (profile, billing, password) — shows read-only store info only |

### 15.3 Error States in Demo Mode

| Scenario | Response |
|---|---|
| User uploads a badly formatted file | Show column mapping UI — do not crash |
| User uploads a file with < 14 days of data | Warn: "Forecasting needs 14+ days. Showing what's available." |
| User uploads a file with < 3 products | Portfolio matrix shows message: "K-Means needs 3+ products to cluster" |
| Gemini API key missing / rate limited | Show a canned demo response with a note: "Live AI temporarily unavailable — showing example response" |
| Redis unavailable | Fall back to computing bundle fresh each time — slower but functional |
| File > 10MB | Reject at frontend before upload with size guidance |

### 15.4 Performance Targets for Demo

| Action | Target Time |
|---|---|
| Initial page load (Dashboard) | < 1.5 seconds (chart bundle cached in Redis) |
| SKU filter switch in Forecast chart | < 50ms (in-memory data slice) |
| Portfolio scatter render (100 products) | < 200ms |
| File parse + preview (1k rows) | < 3 seconds |
| Full ML recomputation (2k records) | < 45 seconds total |
| Document scan (1-page receipt) | < 8 seconds |
| AI Advisor first token | < 2 seconds (Gemini Flash) |

---

## 16. Updated Priority Roadmap (Incorporating Demo Mode)

### Phase 0 — Demo Mode Foundation (Week 1, do this first)
- [ ] Add `DEMO_MODE` env var and conditional auth bypass in `get_current_user`
- [ ] Create fixed demo user + store UUIDs in DB
- [ ] Write idempotent seed script with 90-day dynamic dataset
- [ ] Add `VITE_DEMO_MODE=true` frontend flag and conditional routing
- [ ] Add Demo Mode banner component

### Phase 1 — Infrastructure (Week 1–2)
*(same as original Phase 1 — see Part I §11)*

### Phase 2 — Chart Bundle & Caching (Week 2)
- [ ] Build `/analytics/chart-bundle` endpoint
- [ ] Add Redis integration
- [ ] Add `ml_results` table and migration
- [ ] Frontend: React Query cache with demo-mode infinite TTL

### Phase 3 — Reset + Upload Flow (Week 2–3)
- [ ] Backend: `POST /demo/reset-and-upload` endpoint
- [ ] Backend: SSE progress stream `GET /demo/progress/{job_id}`
- [ ] Backend: `run_full_ml_pipeline` with ordered steps and emit hooks
- [ ] Frontend: Confirmation modal → file drop zone → preview table → loading overlay → success reveal
- [ ] Frontend: "Restore demo data" CTA after user upload

### Phase 4 — ML Features (Week 3–4)
- [ ] Demand Forecasting: confidence bands, anomaly markers, accuracy badge, per-SKU cache
- [ ] Portfolio Matrix: click → slide-over, K slider, pre-generated action strings in seed
- [ ] Smart Alerts: 6 seeded alerts, "Ask Advisor" pre-fill, severity UI, post-upload regeneration
- [ ] Customer Segments: comparison mode, heatmap, per-segment metrics
- [ ] AI Advisor: context injection, prompt chips, streaming, follow-up suggestions

### Phase 5 — Document Scanning (Week 4–5)
- [ ] Backend: Gemini Vision extraction pipeline
- [ ] Backend: Category classification second-pass
- [ ] Frontend: Upload → review table → confirm → ledger add
- [ ] Demo mode: "Recompute?" toast after scan-add

### Phase 6 — Polish & Performance (Week 5–6)
- [ ] Splash screen + guided tooltip overlay
- [ ] All empty states and error states per §15.3
- [ ] Performance audit against targets in §15.4
- [ ] Accessibility pass (keyboard nav, aria labels, contrast)
- [ ] Cross-browser test: Chrome, Firefox, Safari, mobile Safari
- [ ] Load test the ML pipeline with 10k-row uploads

---

*Demo Mode is the product. Build it like it's the first thing every investor, customer, and user will ever see — because it is.*
