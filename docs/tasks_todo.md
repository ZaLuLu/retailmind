# RetailMind — Master Checklist & Task Logs

This checklist tracks the active tasks for both the completed **Visual Broadside & Telex Overhaul (v3.1.0)** and the upcoming **Phase 3: Machine Learning & Analytics Layer**. It helps team members easily coordinate, track what has been done, and see outstanding implementation items.

---

## 📅 Sprint 1: Broadsheet Polish & Telex Overhaul (v3.1.0) — ✅ COMPLETED

### Phase 1: Preparation & Verification
- [x] Verify Gemini AI Advisor API endpoints and domain-scoped guardrails (Fully verified with `test_advisor_valid.py`).
- [x] Establish high-fidelity implementation plan for physical print aesthetics.
- [x] Align on the typography palette (Google Font: `UnifrakturMaguntia` for the historic Masthead).
- [x] Initialize local workspace task checklist and synchronize public documentation folders in `docs/` (Completed).

### Phase 2: Metadata & Global Styling
- [x] **SEO & Brand Alignment (`frontend/index.html`):**
  - Update browser title to a short, professional name: `RetailMind — Store Analytics Ledger`.
  - Add SEO meta descriptions describing the broadsheet BI ledger.
- [x] **Authentic Crease & Hatch Textures (`frontend/src/index.css`):**
  - Import the blackletter `UnifrakturMaguntia` font family.
  - Implement a subtle physical vertical fold crease overlay down the middle of `#root`.
  - Create standard `.hatch-bg` and `.halftone-bg` print pattern utility classes.
  - Declare CSS `@keyframes` animations (`drawPath` for line charts, `riseBar` for bar charts, and `scaleIn` for donut segments).

### Phase 3: Broadsheet Masthead & Typography Details
- [x] **Historic Masthead Title (`frontend/src/components/IntelligenceDashboard.css` / `.jsx`):**
  - Apply `UnifrakturMaguntia` serif blackletter style to the primary logo to match classic newspapers.
  - Fine-tune tracking, kerning, and sizing for extreme visual premium.
- [x] **Gold Drop Cap Insight (`frontend/src/components/IntelligenceDashboard.css`):**
  - Style `.insight-quote::first-letter` to render as a dropped capital letter (ornate gold color, serif typeface, padded and offset).
- [x] **Double Border Dividers:**
  - Add broadsheet double-borders (`border-bottom: 4px double var(--navy)`) to columns and sections.

### Phase 4: Lively & Multiple Interactive SVG Charts
- [x] **Multi-Graph Integration (`frontend/src/components/SalesTrendGraph.jsx`):**
  - Create a third active chart view tab: **Category Share** donut chart.
  - Build a custom interactive SVG Donut Chart representing category contribution.
- [x] **Smooth SVG Entry Animations:**
  - Add path-drawing animations (`stroke-dasharray` and `stroke-dashoffset`) to the Sales Trend bezier line.
  - Add height scaling animations to the Cost Comparison bars to make them rise dynamically on load or tab toggles.
  - Implement tooltip hover cards showing category percentages on segment hovers.

### Phase 5: Telex Telegram Advisor Dispatch
- [x] **Heavy Monospace Telex Layout (`frontend/src/App.css`):**
  - Overhaul `.chat-card` with an authentic, typewriter-style border and heavy padding.
  - Render messages inside simulated Courier paper tape strips with printed dotted borders.
- [x] **Typewriter Stamped Content (`frontend/src/components/AdvisorChat.jsx`):**
  - Format titles and advisor messages with stamped category badges and monospace Courier details.

### Phase 6: Compilation & Launch
- [x] Compile the frontend using `npm run build` to verify there are no compilation errors.
- [x] Manually click through the new charts and verify the responsive layout of the Telex chat on all screen sizes.

---

## 📅 Sprint 2: Phase 3 Machine Learning & Analytics Layer — 🔲 PLANNED / UPCOMING

### Phase 3.1: Adaptive Z-Score Anomaly Engine
- [ ] Implement standard deviation ($\sigma$) and rolling window mean ($\mu$) calculations in `retail_intelligence.py`.
- [ ] Group SKU quantities into weekly bins over 12-week windows.
- [ ] Compute current Z-scores: $Z = \frac{Q - \mu}{\sigma}$ with $Z > 2.0$ thresholds.
- [ ] Implement robust fallback mechanisms to rule-based models for young SKUs ($<4$ data points).
- [ ] Update frontend `DemandSignals.jsx` to render Z-score metadata alongside multiplier stats.

### Phase 3.2: Product Portfolio Clustering ($K$-Means)
- [ ] Extract clustering dimensions per active product (normalized revenue, margin %, volume, recency).
- [ ] Apply `StandardScaler` to ensure scales are normalized and uniform.
- [ ] Fit `KMeans(n_clusters=4)` and map centroids to business quadrants (Stars, Hidden Gems, Cash Cows, Dead Weight).
- [ ] Create FastAPI endpoint `GET /api/v1/retail/portfolio-clusters`.
- [ ] Build the interactive SVG 2x2 coordinate grid scatter-matrix component `PortfolioMatrix.jsx` in frontend.
- [ ] Connect scatter nodes with hover tooltips and interactive quadrant filtering on the main product leaderboard.

### Phase 3.3: Holt-Winters Exponential Smoothing Forecasting
- [ ] Align and reconstruct continuous daily time series per product, interpolating missing days as `0.0`.
- [ ] Fit statsmodels additive `ExponentialSmoothing` with weekly seasonality ($p=7$).
- [ ] Project quantities 14 days out and aggregate into weekly blocks.
- [ ] Implement rolling average forecast fallback for products with sparse data ($<90$ sales days).
- [ ] Render dashed forecasted trend projections forward on the SVG line chart in `SalesTrendGraph.jsx`.

### Phase 3.4: Customer Segment SQL Analytics
- [ ] Write SQL grouping queries by `customer_segment` (Walk-in / Online / B2B) over the chosen period.
- [ ] Calculate blended gross margin, Average Order Value (AOV), contribution share %, and MoM growth rate.
- [ ] Create vintage broadsheet horizontal bar segment graph panel `CustomerSegmentsPanel.jsx`.
- [ ] Mount the segment metrics ledger panel onto the dashboard grid.

### Phase 3.5: Validation Suite & Verification
- [ ] Write automated verification script `backend/scripts/test_ml_layer.py`.
- [ ] Validate cluster counts, Z-Score boundary fallbacks, and forecasting accuracy.
- [ ] Audit user interactions and mobile screen layout responsiveness.
