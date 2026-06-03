# backend/app/api/analytics.py
import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.db import get_db
from ..core.redis import cache
from ..core.config import settings
from ..models.db import User, SaleRecord, Alert, MLResult
from ..api.deps import get_current_user
from ..services.retail_intelligence import retail_intelligence_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


async def get_or_compute_ml_result(
    user_id: Any,
    result_type: str,
    db: AsyncSession,
    compute_func,
) -> Any:
    """Helper to retrieve cached ML result from PostgreSQL or compute and save it on-demand."""
    stmt = select(MLResult).where(MLResult.user_id == user_id, MLResult.result_type == result_type)
    res = await db.execute(stmt)
    ml_res = res.scalars().first()
    if ml_res:
        return ml_res.payload
    
    # Compute on demand
    payload = await compute_func()
    
    # Save to db
    ml_res = MLResult(
        user_id=user_id,
        result_type=result_type,
        payload=payload
    )
    db.add(ml_res)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        # Fallback to load if another concurrent request committed it
        res = await db.execute(stmt)
        ml_res = res.scalars().first()
        if ml_res:
            return ml_res.payload
        # If all else fails, just return payload without saving
        return payload
    return payload


@router.get("/chart-bundle")
async def get_chart_bundle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    store_id: Optional[str] = Query(default=None),
):
    """
    Returns a unified dashboard JSON bundle containing KPIs, 90-day daily revenue history,
    top products, demand forecasts, portfolio clusters, customer segments, and unread alerts.
    
    The payload is cached in Redis (infinite in demo mode, 5 min TTL in production).
    All filter operations on the frontend run against this memory bundle, saving database cost.
    """
    user_id = current_user.id
    
    parsed_store_id = None
    if store_id:
        try:
            import uuid
            parsed_store_id = uuid.UUID(store_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid store_id format",
            )
            
    # 1. Check Redis cache first
    cache_key = f"chart_bundle:{user_id}:{store_id or 'all'}"
    try:
        cached = await cache.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Failed to read chart bundle cache: {e}")

    try:
        # 2. Get standard retail summary for 30d KPIs and lists
        summary = await retail_intelligence_service.get_retail_summary(
            db, user_id, period="30d", store_id=parsed_store_id
        )
        
        # 3. Get or compute forecasting and portfolio quadrant
        if parsed_store_id:
            # Bypass persistent MLResult cache since it has no store_id column;
            # rely on the store-specific Redis cache key instead.
            forecast = await retail_intelligence_service.get_demand_forecast(db, user_id, store_id=parsed_store_id)
            portfolio = await retail_intelligence_service.get_portfolio_clusters(db, user_id, period="30d", store_id=parsed_store_id)
        else:
            async def compute_forecast():
                return await retail_intelligence_service.get_demand_forecast(db, user_id)
            forecast = await get_or_compute_ml_result(user_id, "forecast", db, compute_forecast)

            async def compute_portfolio():
                return await retail_intelligence_service.get_portfolio_clusters(db, user_id, period="30d")
            portfolio = await get_or_compute_ml_result(user_id, "portfolio", db, compute_portfolio)

        # 5. Customer segments from 30d summary
        segments = summary.get("customer_segments", [])

        # 6. Persisted alerts
        alerts_query = select(Alert).where(Alert.user_id == user_id)
        if parsed_store_id:
            alerts_query = alerts_query.where(Alert.store_id == parsed_store_id)
        alerts_stmt = alerts_query.order_by(Alert.created_at.desc())
        alerts_res = await db.execute(alerts_stmt)
        alerts = [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "product_sku": a.product_sku,
                "product_name": a.product_name,
                "severity": a.severity,
                "payload": a.payload,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts_res.scalars().all()
        ]

        # 7. Dense 90-day daily revenue series
        today = date.today()
        lookback_start_90d = today - timedelta(days=89)
        rev_query = select(
            SaleRecord.sale_date,
            func.sum(SaleRecord.total_revenue).label("daily_rev")
        ).where(
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= lookback_start_90d,
            SaleRecord.sale_date <= today
        )
        if parsed_store_id:
            rev_query = rev_query.where(SaleRecord.store_id == parsed_store_id)
        stmt_rev_daily = rev_query.group_by(SaleRecord.sale_date)
        r_rev_daily = await db.execute(stmt_rev_daily)
        daily_rev_map = {row.sale_date: float(row.daily_rev or 0.0) for row in r_rev_daily.all()}
        
        revenue_by_day = []
        for i in range(90):
            d = lookback_start_90d + timedelta(days=i)
            revenue_by_day.append({
                "date": str(d),
                "revenue": daily_rev_map.get(d, 0.0)
            })

        # Assemble full bundle
        bundle = {
            "kpis": {
                "total_revenue": summary.get("total_revenue", 0.0),
                "total_cogs": summary.get("total_cogs", 0.0),
                "gross_profit": summary.get("gross_profit", 0.0),
                "overall_margin_pct": summary.get("overall_margin_pct", 0.0),
                "mom_revenue_change_pct": summary.get("mom_revenue_change_pct", 0.0),
                "num_sales": summary.get("num_sales", 0),
                "ai_insight": summary.get("ai_insight", ""),
            },
            "revenue_by_day": revenue_by_day,
            "top_products": summary.get("top_products", []),
            "forecast": forecast,
            "portfolio": portfolio,
            "segments": segments,
            "alerts": alerts,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Cache in Redis: infinite TTL in demo mode, 5 min TTL in production
        ttl = None if settings.DEMO_MODE else 300
        try:
            await cache.set(cache_key, json.dumps(bundle), ex=ttl)
        except Exception as e:
            logger.warning(f"Failed to write chart bundle to Redis cache: {e}")

        return bundle

    except Exception as e:
        logger.exception("Failed to build chart bundle")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build chart bundle: {str(e)}"
        )
