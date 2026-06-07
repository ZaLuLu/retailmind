# RetailMind Troubleshooting Guide

This document lists common issues, diagnostics, and solutions for the RetailMind platform.

---

## 1. Database Connection Failures

### Symptom: `OperationalError: DB connection failed` or `asyncpg.exceptions`
* **Root Cause**: The backend cannot reach the PostgreSQL instance or the connection URI format is incorrect.
* **Solution**:
  1. Verify the database server is running and reachable.
  2. Ensure the connection string in your `.env` starts with `postgresql+asyncpg://` (the asyncpg driver is required for async execution).
  3. If using Neon.tech, ensure `sslmode=require` is appended to the connection string.

---

## 2. Groq AI Advisor Connectivity Issues

### Symptom: Chat returns `Groq API key is not set` or `Failed to fetch`
* **Root Cause**: The `GROQ_API_KEY` env variable is missing, invalid, or rate-limited.
* **Solution**:
  1. Verify `GROQ_API_KEY` is defined in `backend/.env`.
  2. Test connection by running `python scripts/test_groq.py` inside the backend virtual env.
  3. Check your Groq console usage quotas. If limits are exceeded, the Advisor will automatically degrade to static local rule-based fallbacks.

---

## 3. CORS Policies Blockages

### Symptom: Frontend console shows `Access-Control-Allow-Origin` errors
* **Root Cause**: The backend's allowed origins list does not include the frontend URL.
* **Solution**:
  1. In development, the backend defaults to allowing all origins (`*`) if `ENVIRONMENT=development` is set.
  2. In production, configure the `ALLOWED_ORIGINS` variable in `backend/.env` with a comma-separated list of your client URLs (no trailing slashes):
     `ALLOWED_ORIGINS=https://your-app.vercel.app,https://another-domain.com`

---

## 4. File Upload Ingestion Errors

### Symptom: CSV upload returns `400 Bad Request: Column mapping failure`
* **Root Cause**: Mandatory columns (`product_name`, `quantity`, `unit_price`, `date`) are missing or their headers cannot be recognized.
* **Solution**:
  1. Download the template file from the **Data Import** panel to review structure.
  2. Check spelling. The importer supports 15+ common alias headers, but completely custom names will fail.
  3. Ensure numeric fields (like unit price and quantities) do not contain currency symbols or commas.
