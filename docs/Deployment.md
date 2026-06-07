# RetailMind Deployment Playbook

This document provides production deployment instructions for the RetailMind client and backend API service.

---

## 1. Environment Configurations

Before launching, compile the mandatory values for production:

### 1.1 Backend Production Vars
* `DATABASE_URL`: Connection string containing username, password, host, and database name. Use an async driver compatible URI:
  `postgresql+asyncpg://neondb_owner:<pwd>@<host>/neondb?sslmode=require`
* `JWT_SECRET`: High-entropy secret key for token encryption (minimum 32-character hexadecimal string).
* `GROQ_API_KEY`: Groq API key (`gsk_...`).
* `GROQ_MODEL`: Set to `llama-3.3-70b-versatile` (or another active Llama-3 model).
* `ENVIRONMENT`: Set to `production`.
* `ALLOWED_ORIGINS`: Comma-separated CORS whitelist mapping target production domains:
  `https://your-frontend.vercel.app`
* `DEMO_MODE`: Set to `false` for real multi-tenant environments.

### 1.2 Frontend Production Vars
* `VITE_API_BASE_URL`: Fully qualified root URL of your deployed backend service:
  `https://retailmind-api.onrender.com/api/v1`

---

## 2. Deploying Backend (e.g. Render / Railway)

### 2.1 Deploying on Render (via `render.yaml`)
1. Commit the repository to GitHub.
2. Open the [Render Dashboard](https://render.com) and click **New** -> **Blueprint**.
3. Link the GitHub repository. Render will automatically parse the `render.yaml` blueprint:
   * Installs Python packages via `pip install -r requirements.txt`.
   * Triggers the startup server command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`.
4. Render will prompt you for the undefined environment variable sync keys. Put in your production credentials (`DATABASE_URL`, `GROQ_API_KEY`).
5. Click **Deploy**.

---

## 3. Deploying Frontend (Vercel)

1. Sign in to your [Vercel account](https://vercel.com).
2. Click **Add New Project** and choose the synced GitHub repository.
3. In the project setup panel, configure the following options:
   * **Framework Preset**: Vite.
   * **Root Directory**: `frontend`.
   * **Build Command**: `npm run build`.
   * **Output Directory**: `dist`.
4. Toggle the **Environment Variables** accordion and add:
   * `VITE_API_BASE_URL` -> your production backend URL prefix.
5. Click **Deploy**. Vercel will build and host the broadsheet terminal.
