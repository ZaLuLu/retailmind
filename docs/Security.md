# RetailMind Security Blueprint & Audit Report

This document specifies the security measures, input validations, token authorization policies, and headers integrated into the **RetailMind Platform**.

---

## 1. Security Architecture

```text
 Client (Browser)
       │
 [SSL / HTTPS]
       ▼
Security Headers Middleware
 ├── Content-Security-Policy (CSP)
 ├── Strict-Transport-Security (HSTS)
 └── X-Content-Type-Options
       │
       ▼
Rate Limiter (SlowAPI) ──► Rejects >30 req/min
       │
       ▼
Token Validator (deps.py)
 ├── Rejects expired signatures (JWT)
 └── Enforces User database existences
       │
       ▼
Input Sanitizer (advisor.py / retail.py)
 ├── Regex prompt injection blockers
 ├── Context shape whitelist validation
 └── SQLAlchemy parameterized statements (Prevents SQLi)
```

---

## 2. Security Measures

### 2.1 Parameterized Queries & SQL Injection Mitigation
* Direct SQL text strings are banned. All operations are defined via **SQLAlchemy ORM expressions** or explicit parameterized `select()` clauses.
* Variable bindings are isolated, preventing attackers from injecting escape commands into user input fields.

### 2.2 JWT Signature Verification & Token Rotation
* Uses JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).
* **Rotation Policy**: Access tokens expire after 60 minutes. Clients must exchange their rotation token (`POST /auth/refresh`) to keep active sessions. Refresh tokens are stored in the database and invalidated on logout or user credential changes.

### 2.3 Input Sanitization & Prompt Injection Shielding
Before prompt contexts are sent to the Groq API, advisor input queries are pre-sanitized in `app/api/advisor.py`:
* Length bounds are enforced (maximum 1000 characters).
* Injection strings (e.g. `ignore previous instructions`, `forget all constraints`, `pretend you are`) are filtered out using regex patterns, raising `422 Unprocessable Entity` errors if violations occur.

### 2.4 Secure Response Headers Middleware
An asynchronous security header middleware (`app/middleware/security.py`) intercepts all HTTP responses:
* **HSTS**: `max-age=63072000; includeSubDomains; preload` (enforces HTTPS browser queries).
* **Frame Options**: `DENY` (prevents clickjacking attacks).
* **X-Content-Type-Options**: `nosniff` (mitigates MIME-sniffing exploits).
* **Referrer Policy**: `strict-origin-when-cross-origin`.
* **Content-Security-Policy (CSP)**: Blocks inline script executions and enforces strict origin loading constraints.

### 2.5 API Rate Limiting
A SlowAPI decorator is mounted on high-cost endpoints (`/api/v1/advisor/stream`, `/api/v1/advisor/ask`, `/api/v1/retail/upload-csv`):
* Enforces bounds of **30 requests per minute per IP address**, shielding the Groq backend from denial-of-service attempts.
