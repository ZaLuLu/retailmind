from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from fastapi.responses import StreamingResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.db import get_db
from ..models.db import User, SaleRecord, Store, Alert, UploadHistory, Audit
from ..api.deps import get_current_user
from ..services.retail_intelligence import retail_intelligence_service
from datetime import date
from typing import Optional, Any
from ..core.limiter import limiter
from ..core.redis import cache
from pydantic import BaseModel
import csv
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retail", tags=["Retail Intelligence"])


# ── Store Management (Phase 2: Multi-Store Support) ──────────────────────────

class StoreCreate(BaseModel):
    name: str
    location: Optional[str] = None

@router.get("/stores")
async def list_stores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all stores owned by the current user."""
    try:
        stmt = select(Store).where(Store.user_id == current_user.id).order_by(Store.name.asc())
        result = await db.execute(stmt)
        stores = result.scalars().all()
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "location": s.location,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in stores
        ]
    except Exception as e:
        logger.exception("Failed to list stores")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list stores",
        )

@router.post("/stores")
async def create_store(
    payload: StoreCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new store for the current user."""
    # For demo users, limit store count to 3 stores max per session
    if getattr(current_user, "is_demo", False) and getattr(current_user, "plan", "free") != "enterprise":
        stmt = select(Store).where(Store.user_id == current_user.id)
        res = await db.execute(stmt)
        existing_stores = res.scalars().all()
        if len(existing_stores) >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Demo sessions are limited to registering a maximum of 3 stores."
            )

    try:
        store = Store(
            user_id=current_user.id,
            name=payload.name,
            location=payload.location,
        )
        db.add(store)
        await db.commit()
        await db.refresh(store)
        return {
            "id": str(store.id),
            "name": store.name,
            "location": store.location,
            "created_at": store.created_at.isoformat() if store.created_at else None,
        }
    except Exception as e:
        logger.exception("Failed to create store")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create store",
        )


# ── Summary (Phase 2: date range support) ────────────────────────────────────

@router.get("/summary")
async def get_retail_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    period: str = Query(default="mtd", description="mtd | 7d | 30d | 90d | custom"),
    date_from: Optional[date] = Query(default=None, description="Start date for custom range (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(default=None, description="End date for custom range (YYYY-MM-DD)"),
    store_id: Optional[str] = Query(default=None, description="Optional store ID to filter by"),
):
    """
    Full retail intelligence summary: KPIs, top products, demand signals,
    dead-stock alerts, margin erosion alerts, and AI insight.

    Supports date range filtering via `period` param:
    - mtd: month-to-date (default)
    - 7d: last 7 days
    - 30d: last 30 days
    - 90d: last 90 days
    - custom: use date_from + date_to
    """
    if period == "custom" and (not date_from or not date_to):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required when period=custom",
        )
    if period == "custom" and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be before date_to",
        )

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

    try:
        return await retail_intelligence_service.get_retail_summary(
            db, current_user.id, period=period, date_from=date_from, date_to=date_to, store_id=parsed_store_id
        )
    except Exception as e:
        logger.exception("Failed to generate retail summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate retail summary",
        )


# ── Sales Ledger ──────────────────────────────────────────────────────────────

@router.get("/sales")
async def get_sales(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
):
    """
    Paginated list of individual sale records for the ledger view.
    Supports search, category filter, and date range filter.
    """
    from sqlalchemy import and_, or_
    import uuid

    conditions = [SaleRecord.user_id == current_user.id]

    if store_id:
        try:
            conditions.append(SaleRecord.store_id == uuid.UUID(store_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid store_id format",
            )
    if search:
        conditions.append(
            or_(
                SaleRecord.product_name.ilike(f"%{search}%"),
                SaleRecord.product_sku.ilike(f"%{search}%"),
            )
        )
    if category and category != "All":
        conditions.append(SaleRecord.product_category == category)
    if date_from:
        conditions.append(SaleRecord.sale_date >= date_from)
    if date_to:
        conditions.append(SaleRecord.sale_date <= date_to)

    stmt = (
        select(SaleRecord)
        .where(and_(*conditions))
        .order_by(SaleRecord.sale_date.desc(), SaleRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "product_name": r.product_name,
            "product_sku": r.product_sku,
            "product_category": r.product_category,
            "quantity_sold": r.quantity_sold,
            "unit_price": float(r.unit_price),
            "total_revenue": float(r.total_revenue),
            "cogs": float(r.cogs) if r.cogs is not None else None,
            "gross_margin": float(r.gross_margin) if r.gross_margin is not None else None,
            "sale_date": str(r.sale_date),
            "customer_segment": r.customer_segment,
            "currency": r.currency,
            "source": r.source,
        }
        for r in records
    ]


# ── Demand Forecast (Phase 2) ─────────────────────────────────────────────────

@router.get("/forecast")
async def get_demand_forecast(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    store_id: Optional[str] = Query(default=None),
):
    """
    Weighted rolling average demand forecast per product.
    Returns top 10 products by predicted next-7-day quantity.

    Algorithm: weighted avg of last 7 days (weights 1–7, most recent = 7)
    Trend: compares forecast to prior 7-day average
    Confidence: based on data density (high/medium/low)
    """
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
    try:
        return await retail_intelligence_service.get_demand_forecast(db, current_user.id, store_id=parsed_store_id)
    except Exception as e:
        logger.exception("Failed to generate demand forecast")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate demand forecast",
        )


# ── Portfolio Clustering (K-Means) ──────────────────────────────────────────

@router.get("/portfolio-clusters")
async def get_portfolio_clusters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    period: str = Query(default="mtd", description="mtd | 7d | 30d | 90d | custom"),
    date_from: Optional[date] = Query(default=None, description="Start date for custom range (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(default=None, description="End date for custom range (YYYY-MM-DD)"),
    store_id: Optional[str] = Query(default=None, description="Optional store ID to filter by"),
    k: int = Query(default=4, ge=3, le=6, description="Number of clusters"),
):
    """
    K-Means clustering portfolio analysis, grouping products into performance quadrants.
    """
    if period == "custom" and (not date_from or not date_to):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required when period=custom",
        )
    if period == "custom" and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be before date_to",
        )

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

    try:
        return await retail_intelligence_service.get_portfolio_clusters(
            db, current_user.id, period=period, date_from=date_from, date_to=date_to, store_id=parsed_store_id, k=k
        )
    except Exception as e:
        logger.exception("Failed to generate portfolio clusters")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate portfolio clusters",
        )


# ── Export CSV (Phase 2) ──────────────────────────────────────────────────────

@router.get("/export-csv")
async def export_sales_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
):
    """
    Export filtered sale records as a downloadable CSV.
    Applies the same filters as the SalesLedger view.
    """
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
    try:
        records = await retail_intelligence_service.get_export_data(
            db, current_user.id,
            search=search, category=category,
            date_from=date_from, date_to=date_to,
            store_id=parsed_store_id,
        )
    except Exception as e:
        logger.exception("Failed to export sales data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export sales data",
        )

    # Build CSV in memory
    output = io.StringIO()
    fieldnames = [
        "id", "product_name", "product_sku", "product_category",
        "quantity_sold", "unit_price", "total_revenue", "cogs",
        "gross_margin", "sale_date", "customer_segment", "currency", "source",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

    filename = f"retailmind_export_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── CSV Upload (with .xlsx support via openpyxl) ──────────────────────────────

REQUIRED_HEADERS = {"product_name", "quantity", "unit_price", "date"}
OPTIONAL_HEADERS = {"sku", "category", "cogs", "customer_segment", "currency"}

HEADER_ALIASES = {
    "product": "product_name", "item": "product_name",
    "item_name": "product_name", "name": "product_name",
    "qty": "quantity", "quantity_sold": "quantity",
    "units": "quantity", "units_sold": "quantity",
    "price": "unit_price", "selling_price": "unit_price",
    "sale_price": "unit_price", "mrp": "unit_price",
    "sale_date": "date", "transaction_date": "date", "order_date": "date",
    "cost": "cogs", "cost_price": "cogs", "purchase_price": "cogs",
    "product_category": "category", "type": "category",
    "product_sku": "sku", "item_code": "sku", "barcode": "sku",
}

# ISO 4217 currency allowlist (common codes; extend as needed)
_VALID_CURRENCIES: set[str] = {
    "AED", "AUD", "BDT", "BRL", "CAD", "CHF", "CNY", "CZK",
    "DKK", "EGP", "EUR", "GBP", "HKD", "HUF", "IDR", "ILS",
    "INR", "JPY", "KRW", "LKR", "MXN", "MYR", "NGN", "NOK",
    "NZD", "PHP", "PKR", "PLN", "QAR", "RON", "RUB", "SAR",
    "SEK", "SGD", "THB", "TRY", "TWD", "UAH", "USD", "VND",
    "ZAR",
}


def _normalise_header(raw: str) -> str:
    cleaned = raw.strip().lower().replace(" ", "_").replace("-", "_")
    return HEADER_ALIASES.get(cleaned, cleaned)


def _normalise_currency(raw: str, fallback: str) -> str:
    """
    Normalise a currency string to an uppercase ISO code.
    Falls back to the user-level default if the value is absent or unrecognised.
    """
    code = raw.strip().upper() if raw and raw.strip() else ""
    if code in _VALID_CURRENCIES:
        return code
    if code:  # present but unknown — fall back silently
        logger.debug("Unknown currency code '%s'; falling back to '%s'", code, fallback)
    return fallback


def _parse_date(raw: str) -> date:
    from datetime import datetime
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d %b %Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: '{raw}'")


def _parse_csv_rows(text: str):
    """Parse CSV text into list of normalised row dicts."""
    reader = csv.DictReader(io.StringIO(text))
    raw_headers = reader.fieldnames or []
    normalised_headers = {_normalise_header(h): h for h in raw_headers}

    missing = REQUIRED_HEADERS - set(normalised_headers.keys())
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}. "
            f"Detected: {', '.join(normalised_headers.keys())}"
        )
    return list(reader), normalised_headers


def _parse_xlsx_rows(content: bytes):
    """Parse .xlsx bytes into list of normalised row dicts using openpyxl."""
    try:
        import openpyxl
    except ImportError:
        raise ValueError("openpyxl is required for .xlsx upload. Install it: pip install openpyxl")

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Excel file is empty")

    raw_headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    normalised_headers = {_normalise_header(h): h for h in raw_headers if h}

    missing = REQUIRED_HEADERS - set(normalised_headers.keys())
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}. "
            f"Detected: {', '.join(normalised_headers.keys())}"
        )

    result_rows = []
    for row in rows[1:]:
        row_dict = {}
        for i, raw_h in enumerate(raw_headers):
            if raw_h:
                row_dict[raw_h] = str(row[i]).strip() if row[i] is not None else ""
        result_rows.append(row_dict)

    return result_rows, normalised_headers


def _build_sale_record(
    norm_row: dict,
    user_id,
    user_currency: str,
    store_id: Optional[Any] = None,
    source: str = "csv_upload",
) -> SaleRecord:
    """
    Validate and construct a SaleRecord ORM object from a normalised row dict.

    Raises ValueError with a human-readable message on any validation failure.
    String fields are sanitized against XSS and capped at model column lengths.
    Numeric fields are validated to be finite, non-negative, and non-zero
    (quantity and unit_price must be > 0).
    """
    import math
    from ..core.validation import sanitize_string

    # ── product_name ──────────────────────────────────────────────────────────
    product_name_raw = norm_row.get("product_name")
    if not product_name_raw or not str(product_name_raw).strip():
        raise ValueError("[null] product_name is required and cannot be empty")
    product_name = sanitize_string(product_name_raw)[:255]

    # ── quantity ──────────────────────────────────────────────────────────────
    qty_raw = norm_row.get("quantity")
    if qty_raw is None or str(qty_raw).strip() == "":
        raise ValueError("[null] quantity is required")
    try:
        qty = float(qty_raw)
    except (TypeError, ValueError):
        raise ValueError(f"[type] quantity '{qty_raw}' is not a valid number")
    if math.isnan(qty) or math.isinf(qty):
        raise ValueError(f"[type] quantity '{qty_raw}' is NaN or Infinity")
    if qty <= 0:
        raise ValueError(f"[validation] quantity must be greater than 0, got {qty}")

    # ── unit_price ────────────────────────────────────────────────────────────
    price_raw = norm_row.get("unit_price")
    if price_raw is None or str(price_raw).strip() == "":
        raise ValueError("[null] unit_price is required")
    try:
        unit_price = float(price_raw)
    except (TypeError, ValueError):
        raise ValueError(f"[type] unit_price '{price_raw}' is not a valid number")
    if math.isnan(unit_price) or math.isinf(unit_price):
        raise ValueError(f"[type] unit_price '{price_raw}' is NaN or Infinity")
    if unit_price <= 0:
        raise ValueError(f"[validation] unit_price must be greater than 0, got {unit_price}")

    total_revenue = round(qty * unit_price, 4)

    # ── cogs (optional) ───────────────────────────────────────────────────────
    cogs_raw = str(norm_row.get("cogs", "")).strip()
    cogs: Optional[float] = None
    if cogs_raw:
        try:
            cogs = float(cogs_raw)
        except (TypeError, ValueError):
            raise ValueError(f"[type] cogs '{cogs_raw}' is not a valid number")
        if math.isnan(cogs) or math.isinf(cogs):
            raise ValueError(f"[type] cogs '{cogs_raw}' is NaN or Infinity")
        if cogs < 0:
            raise ValueError(f"[validation] cogs cannot be negative, got {cogs}")

    margin: Optional[float] = None
    if cogs is not None and total_revenue > 0:
        margin = round(((total_revenue - (cogs * qty)) / total_revenue) * 100, 2)

    # ── sale_date ─────────────────────────────────────────────────────────────
    date_raw = str(norm_row.get("date", "")).strip()
    if not date_raw:
        raise ValueError("[null] date is required")
    sale_date = _parse_date(date_raw)   # raises ValueError with [format] hint

    # ── currency (normalised, fallback to user default) ───────────────────────
    currency_raw = str(norm_row.get("currency", "")).strip()
    currency = _normalise_currency(currency_raw, user_currency)

    # ── optional string fields ────────────────────────────────────────────────
    product_sku = sanitize_string(norm_row.get("sku", ""))[:100] or None
    product_category = sanitize_string(norm_row.get("category", "Other"))[:100] or "Other"
    customer_segment = sanitize_string(norm_row.get("customer_segment", ""))[:50] or None

    return SaleRecord(
        user_id=user_id,
        store_id=store_id,
        product_name=product_name,
        product_sku=product_sku,
        product_category=product_category,
        quantity_sold=qty,
        unit_price=unit_price,
        total_revenue=total_revenue,
        cogs=(cogs * qty) if cogs is not None else None,
        gross_margin=margin,
        sale_date=sale_date,
        customer_segment=customer_segment,
        currency=currency,
        source=source,
    )


@router.post("/upload-csv")
@limiter.limit("20/hour")
async def upload_sales_csv(
    request: Request,
    file: UploadFile = File(...),
    store_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV or Excel (.xlsx) file of sales records.

    Performs a full Phase 2 ingestion pipeline:
    - File magic bytes validation (no binary disguised as CSV)
    - Strict schema / column-header check with 15+ alias mappings
    - Row-level sanitization: null checks, type coercion, positive-value enforcement,
      ISO currency normalisation, date format detection (7 formats), string sanitization
    - Exact-duplicate detection within the uploaded batch
    - Structured per-row error log stored in UploadHistory

    Supported formats : .csv  .txt  .xlsx
    Required columns  : product_name, quantity, unit_price, date
    Optional columns  : sku, category, cogs, customer_segment, currency
    """
    from ..core.validation import validate_file_magic
    import uuid

    filename = file.filename or "unknown_upload"
    is_xlsx = filename.lower().endswith(".xlsx")
    is_csv = filename.lower().endswith((".csv", ".txt"))

    if not is_xlsx and not is_csv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload a .csv, .txt, or .xlsx file.",
        )

    content = await file.read()

    # ── Security: validate file magic bytes ───────────────────────────────────
    validate_file_magic(content, filename)

    # ── Size guard (10 MB) ────────────────────────────────────────────────────
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds the 10 MB size limit.",
        )

    # ── Optional store ownership check ────────────────────────────────────────
    parsed_store_id = None
    if store_id:
        try:
            parsed_store_id = uuid.UUID(store_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid store_id format.",
            )
        store_stmt = select(Store).where(Store.id == parsed_store_id, Store.user_id == current_user.id)
        store_res = await db.execute(store_stmt)
        if not store_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Store not found or access denied.",
            )

    # ── Pre-create UploadHistory record (status=failed until we succeed) ──────
    upload_record = UploadHistory(
        user_id=current_user.id,
        store_id=parsed_store_id,
        filename=filename,
        status="failed",
        rows_total=0,
        records_processed=0,
        duplicates_skipped=0,
        errors_logged=[],
    )
    db.add(upload_record)
    await db.commit()
    await db.refresh(upload_record)

    # ── Parse raw rows from file ──────────────────────────────────────────────
    try:
        if is_xlsx:
            raw_rows, _ = _parse_xlsx_rows(content)
            source = "excel_upload"
        else:
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
            raw_rows, _ = _parse_csv_rows(text)
            source = "csv_upload"
    except ValueError as parse_err:
        upload_record.errors_logged = [{"row": 0, "category": "schema", "message": str(parse_err)}]
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(parse_err),
        )

    # ── Demo row-count guard ──────────────────────────────────────────────────
    is_demo = getattr(current_user, "is_demo", False)
    max_upload_rows = (
        500
        if is_demo and getattr(current_user, "plan", "free") != "enterprise"
        else 50_000
    )
    if len(raw_rows) > max_upload_rows:
        msg = (
            f"Upload limited to {max_upload_rows} rows in demo mode. "
            f"Your file contains {len(raw_rows)} rows."
        )
        upload_record.errors_logged = [{"row": 0, "category": "limit", "message": msg}]
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # ── Row-level sanitization + validation ───────────────────────────────────
    user_currency = current_user.currency or "INR"
    records: list[SaleRecord] = []
    error_log: list[dict] = []     # structured: {row, category, message}
    seen_sigs: set = set()
    duplicates_skipped = 0

    for line_num, row in enumerate(raw_rows, start=2):
        norm_row = {_normalise_header(k): v for k, v in row.items()}

        # ── Exact-duplicate detection (within this batch) ─────────────────────
        sig = (
            str(norm_row.get("product_name", "")).strip().lower(),
            str(norm_row.get("sku", "")).strip().lower(),
            str(norm_row.get("quantity", "")).strip(),
            str(norm_row.get("unit_price", "")).strip(),
            str(norm_row.get("date", "")).strip(),
        )
        if sig in seen_sigs:
            duplicates_skipped += 1
            error_log.append({
                "row": line_num,
                "category": "duplicate",
                "message": "Exact duplicate row — skipped.",
            })
            continue
        seen_sigs.add(sig)

        # ── Validate + build ORM record ───────────────────────────────────────
        try:
            record = _build_sale_record(
                norm_row,
                current_user.id,
                user_currency,
                store_id=parsed_store_id,
                source=source,
            )
            record.upload_id = upload_record.id
            records.append(record)
        except ValueError as row_err:
            msg = str(row_err)
            # Extract category prefix inserted by _build_sale_record (e.g. "[null]", "[type]")
            category = "validation"
            for tag in ("null", "type", "format", "validation"):
                if msg.startswith(f"[{tag}]"):
                    category = tag
                    break
            error_log.append({"row": line_num, "category": category, "message": msg})

    # ── Persist ingestion summary ─────────────────────────────────────────────
    upload_record.rows_total = len(raw_rows)
    upload_record.records_processed = len(records)
    upload_record.duplicates_skipped = duplicates_skipped
    upload_record.errors_logged = error_log

    if not records:
        upload_record.status = "failed"
        await db.commit()
        first_err = error_log[0]["message"] if error_log else "Empty dataset — no rows found."
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No valid rows could be imported. First issue: {first_err}",
        )

    # ── Determine final status ────────────────────────────────────────────────
    validation_errors = [e for e in error_log if e["category"] != "duplicate"]
    upload_record.status = "partial" if validation_errors else "success"

    # ── Batch insert in chunks of 100 ─────────────────────────────────────────
    batch_size = 100
    for i in range(0, len(records), batch_size):
        db.add_all(records[i : i + batch_size])
    await db.commit()

    await cache.invalidate_chart_bundle(current_user.id)
    logger.info(
        "Upload completed: user=%s file='%s' inserted=%d duplicates=%d errors=%d status=%s",
        current_user.id, filename, len(records), duplicates_skipped, len(validation_errors),
        upload_record.status,
    )

    return {
        "upload_id": str(upload_record.id),
        "status": upload_record.status,
        "format": "xlsx" if is_xlsx else "csv",
        "rows_total": len(raw_rows),
        "inserted": len(records),
        "duplicates_skipped": duplicates_skipped,
        "errors": len(validation_errors),
        "error_summary": error_log[:25],    # first 25 for inline display
        "message": (
            f"Imported {len(records)} of {len(raw_rows)} rows. "
            f"{duplicates_skipped} duplicates skipped. "
            f"{len(validation_errors)} rows had validation errors."
        ),
    }


@router.get("/upload-history")
async def get_upload_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    store_id: Optional[str] = Query(default=None, description="Filter by store UUID"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    List past CSV / Excel upload batches for the authenticated user.

    Each record includes a concise ingestion summary (rows total, inserted,
    duplicates skipped, validation error count). Use the companion
    `/upload-history/{upload_id}/log` endpoint to fetch the full per-row log.
    """
    import uuid as _uuid

    try:
        stmt = select(UploadHistory).where(UploadHistory.user_id == current_user.id)

        if store_id:
            try:
                stmt = stmt.where(UploadHistory.store_id == _uuid.UUID(store_id))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid store_id format.",
                )

        stmt = stmt.order_by(UploadHistory.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        uploads = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": str(up.id),
                    "filename": up.filename,
                    "status": up.status,                    # success | partial | failed
                    "rows_total": up.rows_total or 0,
                    "records_processed": up.records_processed,
                    "duplicates_skipped": up.duplicates_skipped or 0,
                    "error_count": len(
                        [e for e in (up.errors_logged or []) if isinstance(e, dict) and e.get("category") != "duplicate"]
                    ),
                    "created_at": up.created_at.isoformat() if up.created_at else None,
                }
                for up in uploads
            ],
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch upload history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch upload history.",
        )


@router.get("/upload-history/{upload_id}/log")
async def get_upload_log(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the full per-row error and diagnostic log for a specific upload batch.

    Returns the complete `errors_logged` JSON array, which includes every
    skipped/errored row with its row number, error category, and human-readable
    message. Categories: null | type | format | validation | duplicate | schema | limit.
    """
    import uuid as _uuid

    try:
        parsed_id = _uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload_id format.",
        )

    stmt = select(UploadHistory).where(
        UploadHistory.id == parsed_id,
        UploadHistory.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    upload = result.scalars().first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload record not found.",
        )

    error_log = upload.errors_logged or []
    validation_errors = [e for e in error_log if isinstance(e, dict) and e.get("category") != "duplicate"]
    duplicates = [e for e in error_log if isinstance(e, dict) and e.get("category") == "duplicate"]

    return {
        "success": True,
        "data": {
            "upload_id": str(upload.id),
            "filename": upload.filename,
            "status": upload.status,
            "rows_total": upload.rows_total or 0,
            "records_processed": upload.records_processed,
            "duplicates_skipped": upload.duplicates_skipped or 0,
            "validation_error_count": len(validation_errors),
            "created_at": upload.created_at.isoformat() if upload.created_at else None,
            "log": error_log,          # full structured log
        },
    }


@router.post("/audit/run")
@limiter.limit("5/hour")
async def run_audit(
    request: Request,
    store_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Phase 3 — Trigger a full retail audit.

    Computes:
    - MTD financial summary (revenue, margin, MoM change)
    - Z-Score demand spike detection
    - Dead stock identification
    - Margin erosion alerts
    - 14-day Holt-Winters revenue forecast
    - Top-3 per-product demand forecasts

    Feeds all results to Groq Cloud API (1200-token audit prompt) to generate a
    structured executive Markdown report with 4 sections:
    Executive Summary | Anomaly Breakdown | Demand Outlook | Action Plan.

    The full `anomaly_snapshot` dict is persisted on the Audit row for export.
    Rate-limited to 5 audits per hour per user.
    """
    parsed_store_id = None
    if store_id:
        try:
            import uuid
            parsed_store_id = uuid.UUID(store_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid store_id format")

        store_stmt = select(Store).where(Store.id == parsed_store_id, Store.user_id == current_user.id)
        store_res = await db.execute(store_stmt)
        if not store_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Store not found or access denied"
            )

    try:
        audit = await retail_intelligence_service.run_store_audit(
            db, current_user.id, store_id=parsed_store_id
        )
        return {
            "success": True,
            "data": {
                "id": str(audit.id),
                "audit_date": str(audit.audit_date),
                "total_products_checked": audit.total_products_checked,
                "anomalies_detected": audit.anomalies_detected,
                "ai_audit_summary": audit.ai_audit_summary,
                "anomaly_snapshot": audit.anomaly_snapshot,
                "created_at": audit.created_at.isoformat() if audit.created_at else None,
            }
        }
    except Exception as e:
        logger.exception("Failed to execute store audit")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute store audit: {e}",
        )


@router.get("/audits")
async def list_audits(
    store_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List past audits for the authenticated user. Returns concise metadata (no full snapshot)."""
    try:
        stmt = select(Audit).where(Audit.user_id == current_user.id)
        if store_id:
            try:
                import uuid
                stmt = stmt.where(Audit.store_id == uuid.UUID(store_id))
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid store_id format")
        
        stmt = stmt.order_by(Audit.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        audits = result.scalars().all()
        return {
            "success": True,
            "data": [
                {
                    "id": str(a.id),
                    "audit_date": str(a.audit_date),
                    "total_products_checked": a.total_products_checked,
                    "anomalies_detected": a.anomalies_detected,
                    "has_snapshot": a.anomaly_snapshot is not None,
                    "summary_preview": (a.ai_audit_summary or "")[:200] + "..."
                        if a.ai_audit_summary and len(a.ai_audit_summary) > 200
                        else a.ai_audit_summary,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in audits
            ]
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch past audits")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch past audits",
        )


@router.get("/audits/{audit_id}")
async def get_audit_detail(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full detail of a specific audit including the anomaly snapshot and AI report."""
    try:
        import uuid
        parsed_id = uuid.UUID(audit_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audit_id format")

    stmt = select(Audit).where(Audit.id == parsed_id, Audit.user_id == current_user.id)
    result = await db.execute(stmt)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")

    return {
        "success": True,
        "data": {
            "id": str(audit.id),
            "audit_date": str(audit.audit_date),
            "total_products_checked": audit.total_products_checked,
            "anomalies_detected": audit.anomalies_detected,
            "ai_audit_summary": audit.ai_audit_summary,
            "anomaly_snapshot": audit.anomaly_snapshot,      # Full structured data
            "created_at": audit.created_at.isoformat() if audit.created_at else None,
        }
    }


@router.get("/audits/{audit_id}/export")
async def export_audit_html(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export audit report as a print-optimised HTML document.

    Returns a self-contained HTML page styled with internal CSS for clean
    browser printing (File → Print → Save as PDF). Includes:
    - Header block with audit metadata
    - KPI scorecard (Revenue, Margin, MoM Change, Anomalies)
    - Colour-coded anomaly tables (demand spikes, dead stock, margin erosion)
    - Top 5 products by revenue
    - Groq AI narrative report (Markdown rendered as HTML)
    - Print-to-PDF footer
    """
    try:
        import uuid
        parsed_id = uuid.UUID(audit_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audit_id format")

    stmt = select(Audit).where(Audit.id == parsed_id, Audit.user_id == current_user.id)
    result = await db.execute(stmt)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")

    snap = audit.anomaly_snapshot or {}
    total_revenue = snap.get("total_revenue", 0.0)
    gross_profit = snap.get("gross_profit", 0.0)
    margin_pct = snap.get("overall_margin_pct", 0.0)
    mom_pct = snap.get("mom_revenue_change_pct", 0.0)
    products_checked = audit.total_products_checked
    anomalies = audit.anomalies_detected
    demand_spikes = snap.get("demand_signals", [])
    dead_stock = snap.get("dead_stock_alerts", [])
    margin_erosion = snap.get("margin_erosion_alerts", [])
    top_products = snap.get("top_products", [])
    forecast_summary = snap.get("revenue_forecast_14d_summary", {})
    report_md = audit.ai_audit_summary or "No AI report generated."
    generated_at = audit.created_at.strftime("%Y-%m-%d %H:%M") if audit.created_at else ""

    # ── Simple Markdown → HTML conversion (no extra dependencies) ────────
    def md_to_html(text: str) -> str:
        import re
        # Headers
        text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Bullet points
        lines = text.split("\n")
        html_lines = []
        in_ul = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                if not in_ul:
                    html_lines.append("<ul>")
                    in_ul = True
                html_lines.append(f"<li>{stripped[2:]}</li>")
            else:
                if in_ul:
                    html_lines.append("</ul>")
                    in_ul = False
                html_lines.append(line)
        if in_ul:
            html_lines.append("</ul>")
        text = "\n".join(html_lines)
        # Numbered lists
        text = re.sub(r"^(\d+)\. (.+)$", r"<li>\2</li>", text, flags=re.MULTILINE)
        # Paragraphs (double newlines)
        text = re.sub(r"\n\n", "</p><p>", text)
        return f"<p>{text}</p>"

    report_html = md_to_html(report_md)

    def spike_row(s: dict) -> str:
        z = s.get("z_score", 0.0)
        badge = "badge-critical" if z > 3.0 else "badge-warning"
        return (
            f"<tr>"
            f"<td><strong>{s.get('product_name', '')}</strong></td>"
            f"<td class='{badge}'>{z:.2f}</td>"
            f"<td>+{s.get('deviation_pct', 0):.0f}%</td>"
            f"<td>{s.get('recent_qty', 0):.0f} units</td>"
            f"</tr>"
        )

    def dead_row(d: dict) -> str:
        days = d.get("last_sale_days_ago", 0)
        badge = "badge-critical" if days > 45 else "badge-warning"
        return (
            f"<tr>"
            f"<td><strong>{d.get('product_name', '')}</strong></td>"
            f"<td class='{badge}'>{days} days</td>"
            f"<td>{d.get('message', '')}</td>"
            f"</tr>"
        )

    def margin_row(m: dict) -> str:
        pct = m.get("margin_pct", 0.0)
        badge = "badge-critical" if pct < 5.0 else "badge-warning"
        return (
            f"<tr>"
            f"<td><strong>{m.get('product_name', '')}</strong></td>"
            f"<td class='{badge}'>{pct:.1f}%</td>"
            f"<td>₹{m.get('revenue', 0):,.0f}</td>"
            f"</tr>"
        )

    def product_row(p: dict) -> str:
        return (
            f"<tr>"
            f"<td><strong>{p.get('product_name', '')}</strong></td>"
            f"<td>{p.get('category', '')}</td>"
            f"<td>₹{p.get('revenue', 0):,.0f}</td>"
            f"<td>{p.get('quantity', 0):.0f}</td>"
            f"<td>{p.get('margin_pct', 0):.1f}%</td>"
            f"</tr>"
        )

    mom_color = "#16a34a" if mom_pct >= 0 else "#dc2626"
    mom_sign = "+" if mom_pct >= 0 else ""

    spike_rows_html = "".join(spike_row(s) for s in demand_spikes) or "<tr><td colspan='4' class='empty'>No demand spikes detected.</td></tr>"
    dead_rows_html = "".join(dead_row(d) for d in dead_stock) or "<tr><td colspan='3' class='empty'>No dead stock detected.</td></tr>"
    margin_rows_html = "".join(margin_row(m) for m in margin_erosion) or "<tr><td colspan='3' class='empty'>No margin erosion detected.</td></tr>"
    product_rows_html = "".join(product_row(p) for p in top_products) or "<tr><td colspan='5' class='empty'>No product data available.</td></tr>"

    forecast_block = ""
    if forecast_summary:
        forecast_block = f"""
        <div class="kpi-grid" style="margin-top:0;">
            <div class="kpi-card">
                <div class="kpi-label">Projected 14-Day Revenue</div>
                <div class="kpi-value">₹{forecast_summary.get('projected_total_14d', 0):,.0f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Peak Forecast Day</div>
                <div class="kpi-value" style="font-size:1.4rem">{forecast_summary.get('peak_day', 'N/A')}</div>
                <div class="kpi-sub">₹{forecast_summary.get('peak_revenue', 0):,.0f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Trough Forecast Day</div>
                <div class="kpi-value" style="font-size:1.4rem">{forecast_summary.get('trough_day', 'N/A')}</div>
                <div class="kpi-sub">₹{forecast_summary.get('trough_revenue', 0):,.0f}</div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RetailMind Audit Report — {audit.audit_date}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; font-size: 13px; color: #1e293b; background: #f8fafc; }}
  .page {{ max-width: 860px; margin: 0 auto; background: #fff; padding: 48px 52px; }}
  /* Header */
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #0f172a; padding-bottom: 20px; margin-bottom: 32px; }}
  .brand {{ font-size: 22px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; }}
  .brand span {{ color: #6366f1; }}
  .meta {{ text-align: right; color: #64748b; font-size: 11px; line-height: 1.8; }}
  .meta strong {{ color: #0f172a; font-size: 12px; }}
  /* Section */
  .section {{ margin-bottom: 36px; }}
  .section-title {{ font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #6366f1; margin-bottom: 14px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }}
  /* KPI Cards */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 36px; }}
  .kpi-card {{ background: #f1f5f9; border-radius: 8px; padding: 16px 14px; border-left: 3px solid #6366f1; }}
  .kpi-label {{ font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }}
  .kpi-value {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; line-height: 1; }}
  .kpi-sub {{ font-size: 11px; color: #94a3b8; margin-top: 4px; }}
  /* Tables */
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  thead th {{ background: #f8fafc; color: #64748b; font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; padding: 8px 10px; text-align: left; border-bottom: 2px solid #e2e8f0; }}
  tbody td {{ padding: 9px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }}
  tbody tr:hover {{ background: #f8fafc; }}
  td.empty {{ color: #94a3b8; font-style: italic; padding: 14px 10px; }}
  /* Badges */
  .badge-critical {{ background: #fef2f2; color: #dc2626; font-weight: 700; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }}
  .badge-warning {{ background: #fffbeb; color: #d97706; font-weight: 700; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }}
  /* AI Report */
  .ai-report {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px 28px; line-height: 1.7; }}
  .ai-report h3 {{ font-size: 13px; font-weight: 700; color: #6366f1; margin-top: 20px; margin-bottom: 8px; }}
  .ai-report h3:first-child {{ margin-top: 0; }}
  .ai-report p {{ margin-bottom: 10px; }}
  .ai-report ul {{ padding-left: 20px; margin-bottom: 10px; }}
  .ai-report li {{ margin-bottom: 4px; }}
  .ai-report strong {{ color: #0f172a; }}
  /* Footer */
  .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; color: #94a3b8; font-size: 10px; }}
  /* Print */
  @media print {{
    body {{ background: #fff; }}
    .page {{ padding: 0; max-width: 100%; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="page">
  <!-- Header -->
  <div class="header">
    <div>
      <div class="brand">Retail<span>Mind</span></div>
      <div style="color:#64748b;font-size:11px;margin-top:4px;">Operational Intelligence Platform</div>
    </div>
    <div class="meta">
      <strong>AUDIT REPORT</strong><br>
      Audit Date: {audit.audit_date}<br>
      Audit ID: {str(audit.id)[:8].upper()}...<br>
      Generated: {generated_at} UTC
    </div>
  </div>

  <!-- KPI Scorecard -->
  <div class="section">
    <div class="section-title">Financial Scorecard — Month to Date</div>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-value">₹{total_revenue:,.0f}</div>
        <div class="kpi-sub" style="color:{mom_color};font-weight:700;">{mom_sign}{mom_pct:.1f}% vs prior period</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Gross Profit</div>
        <div class="kpi-value">₹{gross_profit:,.0f}</div>
        <div class="kpi-sub">Margin: {margin_pct:.1f}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Products Audited</div>
        <div class="kpi-value">{products_checked}</div>
        <div class="kpi-sub">Unique SKUs tracked</div>
      </div>
      <div class="kpi-card" style="border-left-color:{'#dc2626' if anomalies > 0 else '#16a34a'};">
        <div class="kpi-label">Risk Alerts</div>
        <div class="kpi-value" style="color:{'#dc2626' if anomalies > 0 else '#16a34a'}">{anomalies}</div>
        <div class="kpi-sub">Operational risks</div>
      </div>
    </div>
  </div>

  <!-- Demand Forecast -->
  {('<div class="section"><div class="section-title">14-Day Revenue Forecast</div>' + forecast_block + '</div>') if forecast_block else ''}

  <!-- AI Report -->
  <div class="section">
    <div class="section-title">AI Executive Audit Report</div>
    <div class="ai-report">{report_html}</div>
  </div>

  <!-- Top Products -->
  <div class="section">
    <div class="section-title">Top 5 Products by Revenue</div>
    <table>
      <thead><tr><th>Product</th><th>Category</th><th>Revenue</th><th>Units Sold</th><th>Margin %</th></tr></thead>
      <tbody>{product_rows_html}</tbody>
    </table>
  </div>

  <!-- Anomaly Tables -->
  <div class="section">
    <div class="section-title">Demand Spike Alerts ({len(demand_spikes)} detected)</div>
    <table>
      <thead><tr><th>Product</th><th>Z-Score</th><th>Deviation</th><th>Recent Volume</th></tr></thead>
      <tbody>{spike_rows_html}</tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-title">Dead Stock Alerts ({len(dead_stock)} detected)</div>
    <table>
      <thead><tr><th>Product</th><th>Days Inactive</th><th>Note</th></tr></thead>
      <tbody>{dead_rows_html}</tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-title">Margin Erosion Alerts ({len(margin_erosion)} detected)</div>
    <table>
      <thead><tr><th>Product</th><th>Avg Margin</th><th>Total Revenue</th></tr></thead>
      <tbody>{margin_rows_html}</tbody>
    </table>
  </div>

  <!-- Footer -->
  <div class="footer">
    <span>RetailMind Audit Platform &copy; 2025 — Confidential</span>
    <span class="no-print">Use browser Print (Ctrl+P) → Save as PDF to export</span>
  </div>
</div>
</body>
</html>"""

    filename = f"retailmind_audit_{audit.audit_date}_{str(audit.id)[:8]}.html"
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/audits/{audit_id}/export/markdown")
async def export_audit_markdown(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the raw Groq Markdown audit report as a .md file."""
    try:
        import uuid
        parsed_id = uuid.UUID(audit_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audit_id format")

    stmt = select(Audit).where(Audit.id == parsed_id, Audit.user_id == current_user.id)
    result = await db.execute(stmt)
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")

    snap = audit.anomaly_snapshot or {}
    header = (
        f"# RetailMind Audit Report\n\n"
        f"**Audit Date:** {audit.audit_date}  \n"
        f"**Audit ID:** {audit.id}  \n"
        f"**Products Audited:** {audit.total_products_checked}  \n"
        f"**Anomalies Detected:** {audit.anomalies_detected}  \n"
        f"**Total Revenue (MTD):** ₹{snap.get('total_revenue', 0.0):,.2f}  \n"
        f"**Gross Margin:** {snap.get('overall_margin_pct', 0.0):.1f}%  \n"
        f"**Generated:** {audit.created_at.strftime('%Y-%m-%d %H:%M') if audit.created_at else 'N/A'} UTC  \n"
        f"\n---\n\n"
    )
    md_content = header + (audit.ai_audit_summary or "_No AI report generated._")
    filename = f"retailmind_audit_{audit.audit_date}_{str(audit.id)[:8]}.md"
    return PlainTextResponse(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )



class SaleRecordCreate(BaseModel):
    product_name: str
    product_sku: Optional[str] = None
    product_category: str = "Other"
    quantity_sold: float = 1.0
    unit_price: float
    sale_date: date
    customer_segment: Optional[str] = "Walk-in"
    currency: str = "INR"


class BulkSalesCreate(BaseModel):
    sales: list[SaleRecordCreate]


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_sales(
    payload: BulkSalesCreate,
    store_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk-insert sale records entered manually (e.g. from the UI form).

    Applies the same Phase 2 numeric validation as the CSV upload pipeline:
    quantity and unit_price must be finite and > 0; currency is validated
    against the ISO 4217 allowlist. An UploadHistory record is created with
    source='manual_bulk' for full audit traceability.

    Maximum records per request: 500 (50 for demo sessions).
    """
    from ..core.config import settings as _settings
    from ..core.validation import sanitize_string
    import math, uuid

    is_demo = getattr(current_user, "is_demo", False)
    max_records = (
        50
        if is_demo and getattr(current_user, "plan", "free") != "enterprise"
        else getattr(_settings, "BULK_SALES_MAX_RECORDS", 500)
    )
    if len(payload.sales) > max_records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Bulk insert limited to {max_records} records per request. Got {len(payload.sales)}.",
        )

    parsed_store_id = None
    if store_id:
        try:
            parsed_store_id = uuid.UUID(store_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid store_id format.",
            )
        store_stmt = select(Store).where(Store.id == parsed_store_id, Store.user_id == current_user.id)
        store_res = await db.execute(store_stmt)
        if not store_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Store not found or access denied.",
            )

    user_currency = current_user.currency or "INR"
    records: list[SaleRecord] = []
    errors: list[dict] = []

    for idx, s in enumerate(payload.sales, start=1):
        qty = s.quantity_sold
        unit_p = s.unit_price

        # ── Numeric guards ──────────────────────────────────────────────────
        if math.isnan(qty) or math.isinf(qty):
            errors.append({"index": idx, "category": "type", "message": f"quantity_sold is NaN or Infinity"})
            continue
        if qty <= 0:
            errors.append({"index": idx, "category": "validation", "message": f"quantity_sold must be > 0, got {qty}"})
            continue
        if math.isnan(unit_p) or math.isinf(unit_p):
            errors.append({"index": idx, "category": "type", "message": f"unit_price is NaN or Infinity"})
            continue
        if unit_p <= 0:
            errors.append({"index": idx, "category": "validation", "message": f"unit_price must be > 0, got {unit_p}"})
            continue

        total_rev = round(qty * unit_p, 4)
        currency = _normalise_currency(s.currency or "", user_currency)

        record = SaleRecord(
            user_id=current_user.id,
            store_id=parsed_store_id,
            product_name=sanitize_string(s.product_name)[:255],
            product_sku=sanitize_string(s.product_sku or "")[:100] or None,
            product_category=sanitize_string(s.product_category or "Other")[:100] or "Other",
            quantity_sold=qty,
            unit_price=unit_p,
            total_revenue=total_rev,
            cogs=None,
            gross_margin=None,
            sale_date=s.sale_date,
            customer_segment=sanitize_string(s.customer_segment or "Walk-in")[:50] or "Walk-in",
            currency=currency,
            source="manual_bulk",
        )
        records.append(record)

    # ── Create UploadHistory for traceability ──────────────────────────────
    upload_record = UploadHistory(
        user_id=current_user.id,
        store_id=parsed_store_id,
        filename="manual_bulk_entry",
        status="success" if records and not errors else ("partial" if records else "failed"),
        rows_total=len(payload.sales),
        records_processed=len(records),
        duplicates_skipped=0,
        errors_logged=errors or None,
    )
    db.add(upload_record)

    if records:
        for record in records:
            record.upload_id = upload_record.id  # back-link will be set after flush
        db.add_all(records)

    await db.commit()
    await db.refresh(upload_record)

    # Patch upload_id now that we have the PK
    if records:
        for record in records:
            record.upload_id = upload_record.id
        await db.commit()

    await cache.invalidate_chart_bundle(current_user.id)

    return {
        "success": True,
        "upload_id": str(upload_record.id),
        "inserted": len(records),
        "errors": len(errors),
        "error_summary": errors,
    }


# ── CSV Template Download ─────────────────────────────────────────────────────

@router.get("/template-csv")
async def get_template_csv():
    """Download a sample CSV template matching the expected upload format."""
    template = (
        "product_name,quantity,unit_price,cogs,category,sku,customer_segment,currency\n"
        "Sony WH-1000XM5,2,19990,11000,Electronics,SONY-XM5,Online,INR\n"
        "Levi's Jeans,5,3499,1800,Apparel,LEV-501,Walk-in,INR\n"
        "Dove Body Lotion,10,299,140,Beauty,DOVE-BL-200,Walk-in,INR\n"
    )
    return PlainTextResponse(
        content=template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=retailmind_template.csv"},
    )


# ── Alert Management (Phase 4) ───────────────────────────────────────────────

@router.get("/alerts")
async def list_alerts(
    current_user: User = Depends(get_current_user),
    store_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """List all persisted alerts for the user, optionally filtered by store."""
    stmt = select(Alert).where(Alert.user_id == current_user.id)
    if store_id:
        try:
            import uuid
            stmt = stmt.where(Alert.store_id == uuid.UUID(store_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid store_id format"
            )
    stmt = stmt.order_by(Alert.created_at.desc())
    res = await db.execute(stmt)
    alerts = res.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "product_sku": a.product_sku,
                "product_name": a.product_name,
                "severity": a.severity,
                "payload": a.payload,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in alerts
        ]
    }

@router.get("/alerts/unread-count")
async def get_unread_alerts_count(
    current_user: User = Depends(get_current_user),
    store_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread alerts."""
    stmt = select(func.count(Alert.id)).where(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    )
    if store_id:
        try:
            import uuid
            stmt = stmt.where(Alert.store_id == uuid.UUID(store_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid store_id format"
            )
    res = await db.execute(stmt)
    count = res.scalar() or 0
    return {"success": True, "data": {"unread_count": count}}

@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark an alert as read."""
    try:
        import uuid
        parsed_id = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert_id format"
        )
    stmt = select(Alert).where(Alert.id == parsed_id, Alert.user_id == current_user.id)
    res = await db.execute(stmt)
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    alert.is_read = True
    await db.commit()
    return {"success": True, "data": {"alert_id": str(alert.id), "is_read": True}}

@router.post("/alerts/read-all")
async def mark_all_alerts_read(
    current_user: User = Depends(get_current_user),
    store_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Mark all alerts for the user (and optionally store) as read."""
    from sqlalchemy import update
    stmt = update(Alert).where(Alert.user_id == current_user.id, Alert.is_read == False).values(is_read=True)
    if store_id:
        try:
            import uuid
            stmt = stmt.where(Alert.store_id == uuid.UUID(store_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid store_id format"
            )
    await db.execute(stmt)
    await db.commit()
    return {"success": True, "message": "All alerts marked as read"}
__all__ = [
    "StoreCreate",
    "list_stores",
    "create_store",
    "get_retail_summary",
    "get_sales",
    "get_demand_forecast",
    "get_portfolio_clusters",
    "export_sales_csv",
    "upload_sales_csv",
    "get_upload_history",
    "get_upload_log",
    "run_audit",
    "list_audits",
    "get_audit_detail",
    "export_audit_text",
    "SaleRecordCreate",
    "BulkSalesCreate",
    "bulk_create_sales",
    "get_template_csv",
    "list_alerts",
    "get_unread_alerts_count",
    "mark_alert_read",
    "_normalise_header",
    "_normalise_currency",
    "_parse_date",
    "_parse_csv_rows",
    "_parse_xlsx_rows",
    "_build_sale_record",
]
