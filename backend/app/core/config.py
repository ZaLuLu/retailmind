from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    
    # Security
    JWT_SECRET: str = "42894b6d5f7564614d696e6450726f6a6563745365637265744b657932303236"
    JWT_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_6wR5NIHQpDUs@ep-dark-unit-ao08r0r8-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT_SECONDS: int = 30
    
    # Uploads
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "pdf,jpg,jpeg,png,webp"
    UPLOAD_DIR: str = "./storage/uploads"
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    # Default to "*" so Vercel deployments work without needing env vars.
    # main.py sets allow_credentials=False when this is "*" (required by CORS spec).
    ALLOWED_ORIGINS: str = "*"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
