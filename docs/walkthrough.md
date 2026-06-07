# Walkthrough - Groq AI Advisor Migration & Dynamic Pricing Integration

This walkthrough documents the full verification of the **RetailMind Platform**'s dashboard panels, local data routing, and Groq-based Advisor Chat guardrails.

---

## 1. Local Verification & Launch Checks

### 1.1 Python Test Suite Run
We ran the validation script suites inside the Python virtual environment:
```powershell
# Verify Groq AI Advisor and Deflections
.venv\Scripts\python.exe scripts/test_groq.py

# Verify Advisor context mapping
.venv\Scripts\python.exe scripts/test_advisor_valid.py

# Verify Holt-Winters & K-Means mathematical models
.venv\Scripts\python.exe scripts/test_ml_layer.py
```
**Results:** All test suites executed successfully with **100% assertions green**.

### 1.2 Frontend Linting & Build
We ran the React client checks:
```powershell
# Run ESLint validation
npm run lint

# Compile production Vite assets
npm run build
```
**Results:** Client code complies fully with zero warnings. The build compiles successfully.

---

## 2. Dynamic Feature Demos

### 2.1 Pricing Simulator & Elasticity Calculator
The Pricing Simulator loads in the right-hand sidebar. It allows merchants to adjust prices and see estimated volume impacts and margin shifts dynamically.

### 2.2 Telex Telegram Briefing Modal
Clicking the `"📰 View Telex"` button in the header opens a vintage, monospaced modal summarizing current metrics.
* Click **Download Telex** to download a clean `.txt` teleprinter dispatch.
* Click **Print Telegram** to open the browser's print utility, formatted as a physical teletype page.

### 2.3 Operations Checklist Persistence
Clicking any alert card expands the checklist panel. Checkbox selections are saved to `localStorage` and persist across reloads.

### 2.2 Domain Guardrails Deflection
The AI Advisor blocks off-topic queries (e.g. general trivia) and defles them with the standard operational warning:
> I am RetailMind's Business Intelligence Advisor. I can only assist with retail store sales, margins, dead stock, demand spikes, and inventory trends.
