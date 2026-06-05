from __future__ import annotations

import secrets
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import Optional


class Settings(BaseSettings):
    """
    Centralised, typed application configuration.
    All values are read from environment variables (or .env file).
    NEVER set production secrets here — use environment variables only.
    """

    # ─── Application ─────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"

    # ─── Security ────────────────────────────────────────────────────────────
    # No default — must be set explicitly in all environments.
    # In development, a random secret is generated per-process (tokens won't
    # survive restarts, which is acceptable in dev).
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ─── Database ────────────────────────────────────────────────────────────
    # No default — must be configured via environment variable.
    DATABASE_URL: Optional[str] = None

    # ─── Redis (optional) ────────────────────────────────────────────────────
    REDIS_URL: Optional[str] = None

    # ─── Google Gemini ───────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT_SECONDS: int = 30

    # ─── File Uploads ────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 20
    MAX_UPLOAD_ROWS: int = 50_000
    ALLOWED_FILE_TYPES: str = "pdf,jpg,jpeg,png,webp,csv,xlsx,xls"
    UPLOAD_DIR: str = "./storage/uploads"

    # ─── CORS ────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = "*"

    # ─── Monitoring ──────────────────────────────────────────────────────────
    SENTRY_DSN: Optional[str] = None

    # ─── Demo Mode ───────────────────────────────────────────────────────────
    DEMO_MODE: bool = False
    DEMO_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    DEMO_STORE_ID: str = "00000000-0000-0000-0000-000000000002"

    # ─── Input Limits ────────────────────────────────────────────────────────
    ADVISOR_QUESTION_MAX_LEN: int = 1000
    BULK_SALES_MAX_RECORDS: int = 500

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_production_requirements(self) -> "Settings":
        """Fail fast if critical settings are missing in production."""
        if self.ENVIRONMENT == "production":
            missing = []
            if not self.DATABASE_URL:
                missing.append("DATABASE_URL")
            if not self.JWT_SECRET:
                missing.append("JWT_SECRET")
            if missing:
                print(
                    f"FATAL: Missing required environment variables for production: {', '.join(missing)}",
                    file=sys.stderr,
                )
                raise ValueError(f"Missing required env vars: {', '.join(missing)}")

        # In non-production, generate an ephemeral secret if none provided
        if not self.JWT_SECRET:
            self.JWT_SECRET = secrets.token_hex(32)

        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL must be set. "
                "Example: postgresql+asyncpg://user:pass@host/dbname"
            )

        return self

    @field_validator("JWT_EXPIRE_MINUTES")
    @classmethod
    def validate_jwt_expiry(cls, v: int) -> int:
        if v < 5 or v > 1440:
            raise ValueError("JWT_EXPIRE_MINUTES must be between 5 and 1440")
        return v


settings = Settings()
