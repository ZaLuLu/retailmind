.PHONY: dev test seed lint migrate clean

# ── Development ──────────────────────────────────────────────────────────────
dev:
	docker-compose up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	cd backend && python -m pytest -v --tb=short
	cd frontend && npm run test -- --run

test-backend:
	cd backend && python -m pytest -v --tb=short

test-frontend:
	cd frontend && npm run test -- --run

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	cd backend && python -m alembic upgrade head

migrate-new:
	cd backend && python -m alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	cd backend && python -m alembic downgrade -1

# ── Demo Data ─────────────────────────────────────────────────────────────────
seed:
	cd backend && python scripts/seed_demo_account.py

seed-force:
	cd backend && python scripts/seed_demo_account.py --force

# ── Linting ───────────────────────────────────────────────────────────────────
lint:
	cd backend && python -m ruff check . && python -m ruff format --check .
	cd frontend && npx eslint src/

lint-fix:
	cd backend && python -m ruff check . --fix && python -m ruff format .
	cd frontend && npx eslint src/ --fix

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf dist node_modules/.cache

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo "RetailMind — Available Commands"
	@echo ""
	@echo "  make dev          — Start full stack with Docker"
	@echo "  make dev-backend  — Start backend only (uvicorn --reload)"
	@echo "  make dev-frontend — Start frontend only (vite dev)"
	@echo "  make seed         — Seed demo account (idempotent)"
	@echo "  make seed-force   — Re-seed demo account (clears existing)"
	@echo "  make migrate      — Run pending Alembic migrations"
	@echo "  make migrate-new MSG='description' — Create new migration"
	@echo "  make lint         — Run ruff + eslint"
	@echo "  make lint-fix     — Auto-fix lint issues"
	@echo "  make test         — Run all tests"
	@echo "  make clean        — Remove build artifacts"
