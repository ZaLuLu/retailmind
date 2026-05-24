from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Centralised, typed application configuration.
    All values are read from environment variables (or .env file).
    Antigravity IDE can autocomplete `settings.` across the entire codebase.
    """

    # ─── Application ─────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"

    # ─── Security ────────────────────────────────────────────────────────────
    JWT_SECRET: str = "42894b6d5f7564614d696e6450726f6a6563745365637265744b657932303236"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ─── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_6wR5NIHQpDUs@ep-dark-unit-ao08r0r8-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

    # ─── Redis (optional — used for caching & rate limiting) ─────────────────
    REDIS_URL: Optional[str] = None

    # ─── Google Gemini ───────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT_SECONDS: int = 30

    # ─── File Uploads ────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10
    MAX_UPLOAD_ROWS: int = 50_000
    ALLOWED_FILE_TYPES: str = "pdf,jpg,jpeg,png,webp,csv,xlsx,xls"
    UPLOAD_DIR: str = "./storage/uploads"

    # ─── CORS ────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"
    # Default to "*" so Vercel deployments work without needing env vars.
    # main.py sets allow_credentials=False when this is "*" (required by CORS spec).
    ALLOWED_ORIGINS: str = "*"

    # ─── Monitoring ──────────────────────────────────────────────────────────
    SENTRY_DSN: Optional[str] = None

    # ─── Demo Mode ───────────────────────────────────────────────────────────
    # Set DEMO_MODE=true to bypass all authentication.
    # Every request is served as the fixed demo user identity below.
    # This is the single env-var switch that enables the public demo deployment.
    DEMO_MODE: bool = False
    DEMO_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    DEMO_STORE_ID: str = "00000000-0000-0000-0000-000000000002"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
