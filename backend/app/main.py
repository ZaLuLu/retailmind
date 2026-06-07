from __future__ import annotations

import logging
import os

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .api.auth import router as auth_router
from .api.advisor import router as advisor_router
from .api.demo import router as demo_router
from .api.onboarding import router as onboarding_router
from .api.users import router as users_router
from .api.retail import router as retail_router
from .api.analytics import router as analytics_router
from .api.admin import router as admin_router
from .middleware.security import SecurityHeadersMiddleware
from .core.limiter import limiter

logger = logging.getLogger(__name__)

# Initialize Sentry for monitoring
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
    )

from contextlib import asynccontextmanager
from .core.redis import cache
from .core.db import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dynamically create tables on startup if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await cache.initialize()
    yield
    if cache.is_redis_available and cache.redis:
        try:
            await cache.redis.aclose()
        except Exception:
            pass

app = FastAPI(
    title="RetailMind API",
    description="AI-Powered Retail Business Intelligence for SMB Owners",
    version="3.0.0",
    lifespan=lifespan,
)

# Bind Rate Limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware Configuration
_raw_origins = settings.ALLOWED_ORIGINS.strip() if settings.ALLOWED_ORIGINS else ""
# Only fall back to FRONTEND_URL if ALLOWED_ORIGINS is completely empty
if not _raw_origins:
    if settings.FRONTEND_URL:
        _raw_origins = settings.FRONTEND_URL
    else:
        _raw_origins = "*"

if _raw_origins == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    _origins_list = [o.strip() for o in _raw_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-Admin-Pin"],
    )


# Mount Secure Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Static Files Ingestion (only on environments with a writable local filesystem)
try:
    if not os.path.exists(settings.UPLOAD_DIR):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
except Exception:
    # On Vercel serverless, the local filesystem is read-only — skip mounting
    pass

# Include Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(advisor_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(retail_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

@app.get("/health")
@app.get("/health/live")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.DEMO_MODE,
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler: log to Sentry, return structured error."""
    import sentry_sdk as _sentry
    _sentry.capture_exception(exc)
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    detail = str(exc) if settings.ENVIRONMENT == "development" else "An internal error occurred."
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": detail},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
