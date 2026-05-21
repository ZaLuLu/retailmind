-- RetailMind — Complete PostgreSQL Schema
-- Run this on a fresh database (Neon.tech or any Postgres 14+)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ──────────────────────────────────────────────────────────────────────────────
-- 1. Users
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             VARCHAR(255) UNIQUE NOT NULL,
    password          VARCHAR(255) NOT NULL,
    full_name         VARCHAR(255),
    store_name        VARCHAR(255),
    initial_balance   DECIMAL(15, 2) DEFAULT 0.0,
    is_onboarded      BOOLEAN DEFAULT FALSE,
    currency          VARCHAR(3) DEFAULT 'INR',
    intelligence_meta JSONB,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ──────────────────────────────────────────────────────────────────────────────
-- 2. Refresh Tokens
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────────────────────
-- 3. Stores (Multi-Store Support)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE stores (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    location    VARCHAR(255),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────────────────────
-- 4. Sale Records (Core RetailMind Model)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE sale_records (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id         UUID REFERENCES stores(id) ON DELETE SET NULL,

    -- Product info
    product_name     VARCHAR(255) NOT NULL,
    product_sku      VARCHAR(100),
    product_category VARCHAR(100) NOT NULL DEFAULT 'Other',

    -- Sales figures
    quantity_sold    FLOAT NOT NULL DEFAULT 1.0,
    unit_price       DECIMAL(12, 2) NOT NULL,
    total_revenue    DECIMAL(12, 2) NOT NULL,
    cogs             DECIMAL(12, 2),           -- Cost of Goods Sold
    gross_margin     DECIMAL(5, 2),            -- Percentage, e.g. 42.50

    -- Context
    sale_date        DATE NOT NULL,
    customer_segment VARCHAR(50),              -- Walk-in | Online | B2B
    currency         VARCHAR(3) DEFAULT 'INR',

    -- ML metadata (auto-populated by ml_engine)
    ml_meta          JSONB,

    -- Audit
    source           VARCHAR(50) DEFAULT 'csv_upload', -- csv_upload | excel_upload | manual
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sale_user_date     ON sale_records(user_id, sale_date);
CREATE INDEX idx_sale_user_category ON sale_records(user_id, product_category);
CREATE INDEX idx_sale_sku           ON sale_records(user_id, product_sku);
CREATE INDEX idx_sale_store         ON sale_records(store_id);

-- ──────────────────────────────────────────────────────────────────────────────
-- 5. Budgets (Legacy — personal finance, may be removed in future)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE budgets (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category      VARCHAR(50) NOT NULL,
    monthly_limit DECIMAL(10, 2) NOT NULL,
    month         DATE NOT NULL,
    UNIQUE (user_id, category, month)
);

CREATE INDEX idx_user_category_month ON budgets(user_id, category, month);

-- ──────────────────────────────────────────────────────────────────────────────
-- 6. Transactions (Legacy — personal finance, may be removed in future)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE transactions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vendor_name      VARCHAR(255),
    amount           DECIMAL(10, 2) NOT NULL,
    category         VARCHAR(50) NOT NULL DEFAULT 'Other',
    transaction_date DATE NOT NULL,
    confidence       DECIMAL(5, 2),
    notes            TEXT,
    document_path    VARCHAR(500),
    intelligence_meta JSONB,
    created_by_ai    BOOLEAN DEFAULT FALSE,
    deleted_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_user     ON transactions(user_id, transaction_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_transactions_category ON transactions(user_id, category)             WHERE deleted_at IS NULL;
