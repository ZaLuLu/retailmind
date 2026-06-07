# RetailMind Environment Setup Guide

This guide details how to configure your local development environment.

---

## 1. Prerequisites
Ensure you have the following software installed:
* **Python**: Version 3.11 or higher.
* **Node.js**: Version 20 or higher (with `npm`).
* **PostgreSQL**: Version 14 or higher (or a serverless instance on Neon.tech).
* **Git**: To clone the repository.

---

## 2. Setting Up Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     source .venv/bin/activate
     ```
4. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Configure your local settings:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and set the required variables:
   * `DATABASE_URL`: Connection string. Example: `postgresql+asyncpg://postgres:secret@localhost:5432/retailmind`
   * `JWT_SECRET`: High-entropy key for token signing. You can generate one via:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   * `GROQ_API_KEY`: Your Groq Cloud Console API key.
   * `GROQ_MODEL`: `llama-3.3-70b-versatile` (default).

---

## 3. Initializing Database

Run the schema script to create the necessary tables, indexes, and relationships:
```bash
psql -U your_pg_user -d your_db_name -f schema.sql
```
Alternatively, copy the contents of `schema.sql` and run them inside your SQL client (e.g. DBeaver, pgAdmin, or Neon SQL Editor).

---

## 4. Setting Up Frontend

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. (Optional) Set up local environment variables:
   Create a `.env.local` file:
   ```text
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

---

## 5. Running the Application

### 5.1 Start Backend Server
```bash
cd backend
.venv\Scripts\activate  # Windows
uvicorn app.main:app --reload --port 8000
```
The backend API documentation will be available at `http://localhost:8000/docs`.

### 5.2 Start Frontend Client
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser. Log in using the guest demo account credentials:
* **Email**: `demo@retailmind.com`
* **Password**: `demo123`
