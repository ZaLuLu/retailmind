"""
Demo Mode API — reset+upload and SSE progress endpoints.

These routes are only functional when DEMO_MODE=true.
They allow a visitor to clear the demo dataset and upload their own
CSV/XLSX file, triggering a full ML recomputation with real-time
progress streamed via Server-Sent Events.

Routes:
    POST /api/v1/demo/reset-and-upload  — clear + upload + enqueue ML
    GET  /api/v1/demo/progress/{job_id} — SSE stream of pipeline progress
    POST /api/v1/demo/restore           — restore original seeded data
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import date, datetime, timedelta
from typing import AsyncGenerator

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import get_current_user
from ..core.config import settings
from ..core.db import get_db
from ..models.db import Alert, MLResult, SaleRecord, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo Mode"])

# ── In-memory job progress store ──────────────────────────────────────────────
# Simple dict keyed by job_id. In production with multiple workers, use Redis.
# For demo mode (single-worker), this is sufficient.
_job_progress: dict[str, list[dict]] = {}


def _require_demo_mode() -> None:
    """Guard: raise 403 if not in demo mode."""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in Demo Mode.",
        )


async def _emit_progress(
    job_id: str,
    step: str,
    percent: int,
    message: str,
) -> None:
    """Append a progress event to the job's event queue."""
    if job_id not in _job_progress:
        _job_progress[job_id] = []
    event = {
        "step": step,
        "percent": percent,
        "message": message,
        "ts": datetime.utcnow().isoformat(),
    }
    _job_progress[job_id].append(event)
    logger.info("Job %s — %s %d%%: %s", job_id, step, percent, message)


# ── ML pipeline ───────────────────────────────────────────────────────────────

async def _run_full_ml_pipeline(user_id: str, job_id: str) -> None:
    """
    Ordered ML recomputation pipeline. Each step writes to ml_results/alerts
    and emits progress events consumed by the SSE endpoint.

    Steps & target % checkpoints (per upgrade plan §12.4):
        import   20%
        forecast 40%
        clusters 60%
        alerts   75%
        segments 90%
        done    100%
    """
    from ..services.retail_intelligence import retail_intelligence_service
    from ..core.db import async_session_factory

    uid = uuid.UUID(user_id)

    try:
        await _emit_progress(job_id, "import", 20, "Records imported and validated")

        # 1. Demand Forecasting (40%)
        try:
            async with async_session_factory() as db:
                forecast_payload = await retail_intelligence_service.get_demand_forecast(db, uid)
                # Save to ml_results
                stmt = select(MLResult).where(MLResult.user_id == uid, MLResult.result_type == "forecast")
                res = await db.execute(stmt)
                ml_res = res.scalars().first()
                if ml_res:
                    ml_res.payload = forecast_payload
                else:
                    db.add(MLResult(user_id=uid, result_type="forecast", payload=forecast_payload))
                await db.commit()
        except Exception as exc:
            logger.exception("Forecasting step failed")
            await _emit_progress(job_id, "forecast_failed", 35, f"Forecasting warn: {exc}")
        await _emit_progress(job_id, "forecast", 40, "Demand forecasting complete")

        # 2. Portfolio Clustering (60%)
        try:
            async with async_session_factory() as db:
                portfolio_payload = await retail_intelligence_service.get_portfolio_clusters(db, uid, period="30d")
                # Save to ml_results
                stmt = select(MLResult).where(MLResult.user_id == uid, MLResult.result_type == "portfolio")
                res = await db.execute(stmt)
                ml_res = res.scalars().first()
                if ml_res:
                    ml_res.payload = portfolio_payload
                else:
                    db.add(MLResult(user_id=uid, result_type="portfolio", payload=portfolio_payload))
                await db.commit()
        except Exception as exc:
            logger.exception("Clustering step failed")
            await _emit_progress(job_id, "clusters_failed", 55, f"Clustering warn: {exc}")
        await _emit_progress(job_id, "clusters", 60, "Portfolio matrix built")

        # 3. Alert Detection (75%)
        # 4. Customer Segment Analysis (90%)
        try:
            async with async_session_factory() as db:
                summary = await retail_intelligence_service.get_retail_summary(db, uid, period="30d")
                
                # Create smart alerts in the alerts table
                for d in summary.get("dead_stock_alerts", []):
                    alert = Alert(
                        user_id=uid,
                        alert_type="dead_stock",
                        product_name=d["product_name"],
                        severity="warning",
                        payload={"message": d["message"], "last_sale_days_ago": d["last_sale_days_ago"]}
                    )
                    db.add(alert)
                
                for m in summary.get("margin_erosion_alerts", []):
                    alert = Alert(
                        user_id=uid,
                        alert_type="margin_erosion",
                        product_name=m["product_name"],
                        severity="critical",
                        payload={"message": m["message"], "margin_pct": m["margin_pct"], "revenue": m["revenue"]}
                    )
                    db.add(alert)
                
                for s in summary.get("demand_signals", []):
                    alert = Alert(
                        user_id=uid,
                        alert_type="demand_spike",
                        product_name=s["product_name"],
                        severity="info",
                        payload={"message": s["message"], "z_score": s["z_score"], "deviation_pct": s["deviation_pct"]}
                    )
                    db.add(alert)

                # Save segments to ml_results
                segments_payload = summary.get("customer_segments", [])
                stmt = select(MLResult).where(MLResult.user_id == uid, MLResult.result_type == "segments")
                res = await db.execute(stmt)
                ml_res = res.scalars().first()
                if ml_res:
                    ml_res.payload = segments_payload
                else:
                    db.add(MLResult(user_id=uid, result_type="segments", payload=segments_payload))
                
                await db.commit()
        except Exception as exc:
            logger.exception("Alerts/Segments step failed")
            await _emit_progress(job_id, "alerts_failed", 80, f"Alerts/Segments warn: {exc}")

        await _emit_progress(job_id, "alerts", 75, "Smart alerts generated")
        await _emit_progress(job_id, "segments", 90, "Customer segments ready")
        await _emit_progress(job_id, "done", 100, "Analysis complete ✓")

    except Exception as exc:
        logger.error("ML pipeline crashed for job %s: %s", job_id, exc)
        await _emit_progress(job_id, "error", 0, f"Analysis failed: {exc!s}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/reset-and-upload")
async def demo_reset_and_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """
    Phase 1 of the demo data reset flow:
    1. Hard-delete all sale_records for the demo user
    2. Parse the uploaded CSV/XLSX
    3. Insert new records
    4. Enqueue full ML recomputation (background)
    5. Return job_id so frontend can poll /progress/{job_id}
    """
    _require_demo_mode()

    content_type = file.content_type or ""
    filename = file.filename or ""

    if not any(filename.endswith(ext) for ext in (".csv", ".xlsx", ".xls")):
        raise HTTPException(400, "Only .csv, .xlsx, or .xls files are accepted.")

    raw = await file.read()

    # 1. Parse
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(__import__("io").BytesIO(raw), encoding="utf-8-sig")
        else:
            df = pd.read_excel(__import__("io").BytesIO(raw))
    except Exception as exc:
        raise HTTPException(422, f"Could not parse file: {exc}") from exc

    if len(df) == 0:
        raise HTTPException(422, "Uploaded file has no data rows.")

    if len(df) > settings.MAX_UPLOAD_ROWS:
        raise HTTPException(
            413,
            f"File exceeds maximum of {settings.MAX_UPLOAD_ROWS:,} rows.",
        )

    # 2. Normalise column names (case-insensitive alias resolution)
    ALIASES: dict[str, str] = {
        # product
        "product": "product_name", "item": "product_name", "item_name": "product_name",
        "name": "product_name",
        # quantity
        "qty": "quantity_sold", "quantity": "quantity_sold", "units": "quantity_sold",
        "units_sold": "quantity_sold", "qty_sold": "quantity_sold",
        # price
        "price": "unit_price", "selling_price": "unit_price", "sale_price": "unit_price",
        "mrp": "unit_price",
        # date
        "date": "sale_date", "transaction_date": "sale_date", "order_date": "sale_date",
        # sku
        "sku": "product_sku", "item_code": "product_sku", "barcode": "product_sku",
        "product_id": "product_sku",
        # category
        "category": "product_category", "type": "product_category",
        # cogs
        "cost": "cogs", "cost_price": "cogs", "purchase_price": "cogs", "unit_cost": "cogs",
        # segment
        "segment": "customer_segment",
    }
    df.columns = [ALIASES.get(c.strip().lower(), c.strip().lower()) for c in df.columns]

    # Validate required columns
    required = {"product_name", "quantity_sold", "unit_price", "sale_date"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            422,
            f"Missing required columns: {', '.join(missing)}. "
            "Use the template from the Data Import page.",
        )

    # 3. Delete existing records
    await db.execute(delete(SaleRecord).where(SaleRecord.user_id == user.id))
    # Also clear old alerts and ML results
    await db.execute(delete(Alert).where(Alert.user_id == user.id))
    await db.execute(delete(MLResult).where(MLResult.user_id == user.id))
    await db.commit()

    # Look up the first store of the user to bind it to all imported sales records
    store_stmt = select(Store).where(Store.user_id == user.id).order_by(Store.created_at.asc())
    store_res = await db.execute(store_stmt)
    store = store_res.scalars().first()
    store_id = store.id if store else None

    # 4. Insert new records
    records: list[SaleRecord] = []
    skipped = 0
    import math

    for _, row in df.iterrows():
        try:
            qty = float(row["quantity_sold"])
            price = float(row["unit_price"])

            if math.isnan(qty) or math.isnan(price) or math.isinf(qty) or math.isinf(price):
                logger.debug("Skipping row due to invalid number (NaN or Infinity)")
                skipped += 1
                continue

            total = qty * price
            raw_cogs = row.get("cogs", None)
            
            cogs = None
            if pd.notna(raw_cogs) and raw_cogs:
                cogs_val = float(raw_cogs)
                if math.isnan(cogs_val) or math.isinf(cogs_val):
                    logger.debug("Skipping row due to invalid COGS (NaN or Infinity)")
                    skipped += 1
                    continue
                cogs = cogs_val * qty

            margin = (
                round(((total - cogs) / total) * 100, 2)
                if total > 0 and cogs is not None
                else None
            )

            sale_date_raw = str(row["sale_date"])[:10]
            sale_date = datetime.strptime(sale_date_raw, "%Y-%m-%d").date()

            records.append(
                SaleRecord(
                    user_id=user.id,
                    store_id=store_id,
                    product_name=str(row["product_name"]).strip(),
                    product_sku=str(row.get("product_sku", "")).strip() or None,
                    product_category=str(row.get("product_category", "Other")).strip(),
                    quantity_sold=qty,
                    unit_price=price,
                    total_revenue=total,
                    cogs=cogs,
                    gross_margin=margin,
                    sale_date=sale_date,
                    customer_segment=str(row.get("customer_segment", "")).strip() or None,
                    currency="USD",
                    source="demo_upload",
                )
            )
        except Exception as exc:
            logger.debug("Skipping row due to parse error: %s", exc)
            skipped += 1

    if not records:
        raise HTTPException(422, "No valid rows could be parsed from the file.")

    batch_size = 500
    for i in range(0, len(records), batch_size):
        db.add_all(records[i : i + batch_size])
        await db.commit()

    # 5. Enqueue ML pipeline
    job_id = str(uuid.uuid4())
    _job_progress[job_id] = []
    background_tasks.add_task(_run_full_ml_pipeline, str(user.id), job_id)

    return {
        "job_id": job_id,
        "record_count": len(records),
        "skipped_rows": skipped,
        "status": "processing",
    }


@router.get("/progress/{job_id}")
async def demo_progress(job_id: str) -> StreamingResponse:
    """
    SSE stream returning real-time ML pipeline progress for a given job_id.
    Frontend connects here after POST /reset-and-upload and listens until
    percent == 100 or step == 'error'.
    """
    _require_demo_mode()

    async def event_stream() -> AsyncGenerator[str, None]:
        seen = 0
        timeout_seconds = 120
        start = asyncio.get_event_loop().time()

        while True:
            events = _job_progress.get(job_id, [])
            new_events = events[seen:]

            for event in new_events:
                yield f"data: {json.dumps(event)}\n\n"
                seen += 1

                if event.get("step") in ("done", "error"):
                    # Clean up after a delay so late consumers still get it
                    await asyncio.sleep(5)
                    _job_progress.pop(job_id, None)
                    return

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > timeout_seconds:
                yield f"data: {json.dumps({'step': 'timeout', 'percent': 0, 'message': 'Pipeline timed out'})}\n\n"
                return

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@router.post("/restore")
async def demo_restore(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """
    Restore original demo seed data by re-running the seed script for this user.
    Shows up as '← Restore demo data' CTA after user has uploaded their own file.
    """
    _require_demo_mode()

    # Import and re-run seed for this user only
    try:
        from scripts.seed_demo_account import seed_for_user
        job_id = str(uuid.uuid4())
        _job_progress[job_id] = []
        background_tasks.add_task(seed_for_user, str(user.id), job_id, _job_progress)
        return {"job_id": job_id, "status": "restoring"}
    except ImportError as e:
        logger.warning(f"Seed import failed: {e}")
        # Seed function not yet available — run seed script externally
        raise HTTPException(
            503,
            "Restore not available. Run: python backend/scripts/seed_demo_account.py --force",
        )
