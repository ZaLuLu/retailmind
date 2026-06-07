# RetailMind Contributing Guidelines

Welcome to RetailMind! Thank you for helping build better analytics tools for small business owners.

---

## 1. Local Coding Standards

### 1.1 Python Backend
* Follow PEP 8 style guidelines.
* Run type checks and imports sorting before pushing.
* Use Pydantic models for request/response serialization (strict validation).
* All raw database transactions must use async queries and parameterized SQL expressions.

### 1.2 React Frontend
* Use clean functional components with destructuring props.
* Do not write inline styled elements for common layouts; reuse variables from `index.css` or component sheets.
* Handle empty states, loading indicators, and boundary fallbacks for all cards.
* Keep renders pure. Do not instantiate state using impure functions (like `Math.random()` or `new Date()`) directly inside render bodies (wrap them inside state/memo blocks).

---

## 2. Test Verification

Before submitting a Pull Request, run the validation checks:

### 2.1 Run Python Tests
```bash
cd backend
.venv\Scripts\python.exe scripts/test_groq.py
.venv\Scripts\python.exe scripts/test_advisor_valid.py
.venv\Scripts\python.exe scripts/test_ml_layer.py
```

### 2.2 Run Frontend Checks
```bash
cd ../frontend
npm run lint
npm run build
```

Ensure all verification runs complete with **zero errors or warnings**.
