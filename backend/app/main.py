from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sentry_sdk
import os
from .core.config import settings
from .api.auth import router as auth_router
from .api.advisor import router as advisor_router
from .api.onboarding import router as onboarding_router
from .api.users import router as users_router
from .api.retail import router as retail_router
from .middleware.security import SecurityHeadersMiddleware

# Initialize Sentry for monitoring
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
    )

# Initialize Rate Limiter (using client IP addresses)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="RetailMind API",
    description="AI-Powered Retail Business Intelligence for SMB Owners",
    version="3.0.0",
)

# Bind Rate Limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware (restrict origins in production)
allowed_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)

# Mount Secure Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Static Files Ingestion
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(advisor_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(retail_router, prefix="/api/v1")

@app.get("/health/live")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
