from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sentry_sdk
import os
from .core.config import settings
from .api.auth import router as auth_router
from .api.advisor import router as advisor_router
from .api.onboarding import router as onboarding_router
from .api.users import router as users_router
from .api.retail import router as retail_router

# Initialize Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
    )

app = FastAPI(
    title="RetailMind API",
    description="AI-Powered Retail Business Intelligence for SMB Owners",
    version="3.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
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
