# RetailMind Frontend Documentation

This document describes the React 19 + Vite 8 frontend client architecture, styling layout variables, component breakdown, and state syncing mechanisms.

---

## 1. Design Philosophy: Vintage Broadsheet Editorials
The UI implements a high-fidelity monospaced and serif editorial layout resembling a 19th-century financial press broadsheet:
* **Typography**: Playfair Display (Serif header), Source Serif 4 (Readability copy), JetBrains Mono (Financial telemetry).
* **Colors**: Light beige-yellow weathered paper backgrounds (`--paper`), solid black/navy ink (`--ink`), crimson stamps (`--red`), amber highlights (`--gold`).
* **Borders**: Double rule borders (`border: 4px double var(--ink)`).
* **Animations**: Gentle micro-animations for card hovers and alert stamps.

---

## 2. Component Structure

### 2.1 Shell Layout
* `App.jsx` — Bootstraps state, handles routing views (login vs. onboarding vs. dashboard), and checks active token sessions.
* `components/IntelligenceDashboard.jsx` — Renders main layout. Splits workspace into a primary left column (revenue hero, trend charts, matrices) and a right sidebar (alerts, elasticity simulator, data import, AI insights dispatch).

### 2.2 Financial Telemetry Panels
* `RevenueHero.jsx` — Renders KPI summaries for gross profit, total revenue, average margins, and MoM percentages.
* `SalesTrendGraph.jsx` — Implements custom interactive SVG graphs mapping daily sales, Holt-Winters 14-day future forecasts, and 95% confidence bands. 
* `TopProductsTable.jsx` — A sortable listing of the catalog ranked by revenue, quantity, or gross profit margins.

### 2.3 Machine Learning Visuals
* `PortfolioMatrix.jsx` — Renders the unsupervised K-Means quadrant plot using clean SVG points. Double-clicking any quadrant filters the transaction ledger instantly.
* `CustomerSegmentsPanel.jsx` — Renders target metrics for Online, Walk-In, and B2B channels.

### 2.4 Interactive Tools
* `PricingSimulator.jsx` — Slider control to adjust retail prices and dynamically model category elasticity volume offsets.
* `TelexBriefing.jsx` — Teleprinter dispatch modal displaying summarized telemetry. Suppress standard UI elements in `@media print` to optimize for clean A4 printing.
* `DemandSignals.jsx` — Lists alert cards. Expands on click to display checkable operations tasks with `localStorage` persistence.
* `AdvisorChat.jsx` — Retail advisor chat pane displaying real-time streaming SSE completions.

---

## 3. API Communication Layer (`src/services/api.js`)
Exposes a unified axios-like custom fetch wrapper:
* Automatically attaches `Authorization` JWT headers.
* Intercepts `401 Unauthorized` responses. If a session token expires, it silently requests a token refresh (`POST /auth/refresh`). If the refresh token is valid, it retries the original request. Otherwise, it redirects to the login screen.
