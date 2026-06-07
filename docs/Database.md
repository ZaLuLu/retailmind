# RetailMind Database Design & Schemas

This document specifies the relational schemas, indexes, and caching strategies of the PostgreSQL database.

---

## 1. Database Schemas

### 1.1 Users Table (`users`)
Stores authenticated accounts and settings:
* `id`: `UUID` (Primary Key).
* `email`: `VARCHAR(255)` (Unique, Indexed).
* `hashed_password`: `VARCHAR(255)`.
* `currency`: `VARCHAR(3)` (Default: `INR`).
* `plan`: `VARCHAR(50)` (Default: `free`).
* `onboarding_completed`: `BOOLEAN` (Default: `FALSE`).
* `created_at`: `TIMESTAMP WITH TIME ZONE`.

### 1.2 Stores Table (`stores`)
Supports multi-store rosters:
* `id`: `UUID` (Primary Key).
* `user_id`: `UUID` (Foreign Key -> `users.id`, Cascades).
* `name`: `VARCHAR(255)`.
* `location`: `VARCHAR(255)` (Nullable).
* `created_at`: `TIMESTAMP WITH TIME ZONE`.

### 1.3 Sale Records Table (`sale_records`)
The primary transactional ledger:
* `id`: `UUID` (Primary Key).
* `user_id`: `UUID` (Foreign Key -> `users.id`, Cascades).
* `store_id`: `UUID` (Foreign Key -> `stores.id`, Nullable, Cascades).
* `product_name`: `VARCHAR(255)` (Indexed).
* `product_sku`: `VARCHAR(100)` (Nullable).
* `product_category`: `VARCHAR(100)` (Indexed).
* `quantity_sold`: `NUMERIC(12, 2)`.
* `unit_price`: `NUMERIC(12, 2)`.
* `total_revenue`: `NUMERIC(15, 2)`.
* `cogs`: `NUMERIC(12, 2)` (Nullable).
* `gross_margin`: `NUMERIC(5, 2)` (Nullable).
* `sale_date`: `DATE` (Indexed).
* `customer_segment`: `VARCHAR(50)` (Nullable).
* `currency`: `VARCHAR(3)`.
* `source`: `VARCHAR(50)`.
* `created_at`: `TIMESTAMP WITH TIME ZONE`.

### 1.4 In-App Alerts Table (`alerts`)
Stores pre-computed operational alerts:
* `id`: `UUID` (Primary Key).
* `user_id`: `UUID` (Foreign Key -> `users.id`, Cascades).
* `store_id`: `UUID` (Foreign Key -> `stores.id`, Nullable, Cascades).
* `alert_type`: `VARCHAR(50)` (Spike, Dead Stock, Margin Erosion).
* `product_name`: `VARCHAR(255)`.
* `severity`: `VARCHAR(50)`.
* `payload`: `JSONB`.
* `is_read`: `BOOLEAN` (Default: `FALSE`).
* `created_at`: `TIMESTAMP WITH TIME ZONE`.

### 1.5 ML Results Table (`ml_results`)
Caches pre-computed forecasting arrays and K-Means coordinates:
* `id`: `UUID` (Primary Key).
* `user_id`: `UUID` (Foreign Key -> `users.id`, Cascades).
* `result_type`: `VARCHAR(100)`.
* `payload`: `JSONB` (Stores raw arrays, coordinates, and metrics).
* `data_hash`: `VARCHAR(64)` (SHA-256 hash of the store's data state).
* `computed_at`: `TIMESTAMP WITH TIME ZONE`.

---

## 2. Caching Strategy
To maintain low response latencies during rendering, expensive ML calculations (Holt-Winters forecasts, K-Means clustering, and segment summaries) are cached in the `ml_results` table:
1. Before computing, the backend generates an SHA-256 hash of the store's data state using:
   * Record count.
   * Latest `created_at` timestamp.
   * Total revenue sum.
   * Total quantity sold.
   * Active date range params.
2. It queries `ml_results` for the corresponding `result_type` and `user_id`.
3. If a record is found and its `data_hash` matches, the cached JSON payload is returned immediately, skipping Python computation.
4. If the hash differs (e.g. new records were uploaded), the backend re-runs the calculations, updates the cache record with the new payload and hash, and commits the transaction.
