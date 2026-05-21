CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Users
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 2. Refresh tokens
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL,
    expires_at  TIMESTAMP NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 3. Budgets
CREATE TABLE budgets (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    category      VARCHAR(50) NOT NULL,
    monthly_limit DECIMAL(10,2) NOT NULL CHECK (monthly_limit > 0),
    month         DATE NOT NULL,
    UNIQUE(user_id, category, month)
);

-- 4. Transactions
CREATE TABLE transactions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID REFERENCES users(id) ON DELETE CASCADE,
    vendor_name      VARCHAR(255),
    amount           DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    category         VARCHAR(50) NOT NULL DEFAULT 'Other',
    transaction_date DATE NOT NULL,
    confidence       DECIMAL(5,2),
    notes            TEXT,
    document_path    VARCHAR(500),
    created_by_ai    BOOLEAN DEFAULT FALSE,
    deleted_at       TIMESTAMP NULL,
    created_at       TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_transactions_user
ON transactions(user_id, transaction_date DESC)
WHERE deleted_at IS NULL;

CREATE INDEX idx_transactions_category
ON transactions(user_id, category)
WHERE deleted_at IS NULL;
