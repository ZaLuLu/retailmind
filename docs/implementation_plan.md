# Implementation Plan: Advisor Chat Overhaul, Visual Distinctions & Premium Visual Graphs

This plan details the refinements to be made on **RetailMind** to:
1. **Align Advisor Chat Guardrails**: Update backend Gemini prompts to use specialized retail scoping and custom decline messaging.
2. **Stylize Distinct Message Bubbles**: Enhance CSS styling of user vs advisor dialogue blocks inside `App.css` using the broadsheet palette (gold left-border accent for the advisor and clean deep navy blocks for the user).
3. **Introduce a Premium Visual Graph**: Implement a gorgeous, responsive, custom SVG line/area trend graph and category margin scatter bar under Category Performance, keeping with the analytical editorial aesthetic.

---

## User Review Required

> [!IMPORTANT]
> The advisor chat will enforce strict boundaries focusing solely on retail analytics (margins, inventory, dead-stock, spikes). General queries like mental health or cooking will be politely deflected with a custom RetailMind decline signature.

---

## Proposed Changes

### Backend Components

#### [MODIFY] [gemini.py](file:///d:/CODING/documind/backend/app/services/gemini.py)
* **What**: Re-phrase the `ask_advisor` Gemini instructions.
* **Details**:
  * Set advisor identity to `RetailMind Business Advisor`.
  * Update strict boundaries to focus exclusively on retail business operations, store sales, margin analysis, product pricing, and inventory.
  * Change decline message to: `"I am RetailMind's Business Intelligence Advisor. I can only assist you with questions related to your retail store sales, margins, dead stock, demand spikes, and inventory trends."`

---

### Frontend Components

#### [MODIFY] [App.css](file:///d:/CODING/documind/frontend/src/App.css)
* **What**: Refine chat bubble colors for superior visual differentiation.
* **Details**:
  * **User Message**: Solid deep navy (`#0D1B2A`) background with warm linen (`#F5F0E8`) text and crisp 4px rounded borders.
  * **Advisor Message**: Rich linen/sand (`#EDE8D8`) background with a gold accent left-border (`4px solid #C9A84C`), deep navy (`#0D1B2A`) text.

#### [NEW] [SalesTrendGraph.jsx](file:///d:/CODING/documind/frontend/src/components/SalesTrendGraph.jsx)
* **What**: Create a premium interactive SVG charting component.
* **Details**:
  * **Area Trend Chart**: Automatically parses the `sales` prop to plot aggregate daily revenue over the last 15 days using a custom inline SVG element (drawing clean grids, warm editorial fills, crisp navy trend lines, and tooltips).
  * **Interactive Highlights**: Allows users to hover/click individual days to display exact revenue values formatted using the active currency symbol and local settings (thousands `K` / lakhs `L`).

#### [MODIFY] [IntelligenceDashboard.jsx](file:///d:/CODING/documind/frontend/src/components/IntelligenceDashboard.jsx)
* **What**: Mount the new trend chart in place of or immediately above the static progress bar category table.
* **Details**: Include the new `<SalesTrendGraph />` component in the main column under KPI cards to maximize aesthetic and analytical impact.

---

## Verification Plan

### Automated/Manual Verification
1. **Interactive Chart Test**: Verify charts render correctly in both INR and USD notations and react smoothly to settings updates.
2. **Advisor Guardrail Test**: Type off-topic questions (e.g. mental health, recipes) to verify the new deflection message.
3. **Chat Visuals Audit**: Verify bubbles have distinct navy/cream backdrops and gold accents.
