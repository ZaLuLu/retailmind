# backend/app/api/admin.py
import logging
import os
import secrets
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from ..core.db import get_db
from ..core.config import settings
from ..core.redis import cache
from ..models.db import User, Store, SaleRecord, Alert, MLResult
from ..api.deps import get_current_user
from ..core.limiter import limiter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin Management"])

# Resolve PIN safely: prevent hardcoded default leakage in production environments
ADMIN_PIN = os.getenv("ADMIN_PIN")
if not ADMIN_PIN:
    if settings.ENVIRONMENT == "production":
        # Generate an ephemeral secure random token so administrative functions are locked
        ADMIN_PIN = secrets.token_urlsafe(32)
        logger.warning("No ADMIN_PIN environment variable configured in production! Ephemeral random PIN generated.")
    else:
        ADMIN_PIN = "Retail.AdMin113"

class AdminVerifyRequest(BaseModel):
    pin: str

class BypassRequest(BaseModel):
    user_id: str
    bypass: bool

def verify_admin_pin(x_admin_pin: str = Header(None)) -> None:
    """Dependency that checks if the request has the correct admin PIN header."""
    if not x_admin_pin or not secrets.compare_digest(x_admin_pin, ADMIN_PIN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Admin PIN"
        )

@router.post("/verify")
@limiter.limit("5/minute")
async def verify_pin(
    request: Request,
    payload: AdminVerifyRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify if the provided PIN matches the admin configuration (rate-limited)."""
    if secrets.compare_digest(payload.pin, ADMIN_PIN):
        return {"success": True, "message": "Access granted"}
    
    # Introduce delay to slow down automated brute-force attempts
    await asyncio.sleep(1.0)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect Admin PIN"
    )

@router.get("/stats")
@limiter.limit("5/minute")
async def get_system_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(verify_admin_pin)
):
    """Get rows count from all core database tables."""
    try:
        user_count = await db.execute(select(func.count()).select_from(User))
        store_count = await db.execute(select(func.count()).select_from(Store))
        records_count = await db.execute(select(func.count()).select_from(SaleRecord))
        alerts_count = await db.execute(select(func.count()).select_from(Alert))
        ml_results_count = await db.execute(select(func.count()).select_from(MLResult))

        return {
            "success": True,
            "stats": {
                "users": user_count.scalar() or 0,
                "stores": store_count.scalar() or 0,
                "sale_records": records_count.scalar() or 0,
                "alerts": alerts_count.scalar() or 0,
                "ml_results": ml_results_count.scalar() or 0
            }
        }
    except Exception as e:
        logger.exception("Failed to fetch admin statistics")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query database statistics: {str(e)}"
        )

@router.post("/clear-cache")
@limiter.limit("5/minute")
async def clear_cache(
    request: Request,
    current_user: User = Depends(get_current_user),
    _ = Depends(verify_admin_pin)
):
    """Clear all Redis and local memory cache keys."""
    try:
        await cache.clear_all()
        return {"success": True, "message": "Cache database cleared successfully"}
    except Exception as e:
        logger.exception("Failed to flush cache")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/reseed")
@limiter.limit("5/minute")
async def trigger_global_reseed(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(verify_admin_pin)
):
    """Clean all tables and reseed default demo data."""
    try:
        # Import seeding function
        from scripts.seed_demo_account import seed_demo_data
        
        # Clear tables
        await db.execute(delete(SaleRecord))
        await db.execute(delete(Alert))
        await db.execute(delete(MLResult))
        await db.execute(delete(Store))
        await db.execute(delete(User))
        await db.commit()
        
        # Run seed
        await seed_demo_data(force=True)
        await cache.clear_all()
        
        return {"success": True, "message": "Database successfully reseeded globally"}
    except Exception as e:
        logger.exception("Global reseed failed")
        raise HTTPException(status_code=500, detail=f"Reseed failed: {str(e)}")

@router.post("/bypass-limits")
@limiter.limit("5/minute")
async def toggle_limits_bypass(
    request: Request,
    payload: BypassRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(verify_admin_pin)
):
    """Toggle a limit-bypass flag in the database user schema (pro plan toggle)."""
    import uuid
    try:
        uid = uuid.UUID(payload.user_id)
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Change plan to "enterprise" to bypass demo limits
        user.plan = "enterprise" if payload.bypass else "free"
        await db.commit()
        
        # Invalidate cache
        await cache.invalidate_chart_bundle(user.id)
        
        status_lbl = "bypassed (enterprise)" if payload.bypass else "limited (free)"
        return {"success": True, "message": f"User limits updated to: {status_lbl}"}
    except Exception as e:
        logger.exception("Limits bypass update failed")
        raise HTTPException(status_code=500, detail=str(e))
