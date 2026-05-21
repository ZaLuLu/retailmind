from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.db import get_db
from ..models.db import User, SaleRecord, Store
from ..api.deps import get_current_user
from ..services.retail_intelligence import retail_intelligence_service
from datetime import date
from typing import Optional
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
):
    """
    K-Means clustering portfolio analysis, grouping products into 4 performance quadrants:
    Stars, Cash Cows, Hidden Gems, Dead Weight.
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
            db, current_user.id, period=period, date_from=date_from, date_to=date_to, store_id=parsed_store_id
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


def _normalise_header(raw: str) -> str:
    cleaned = raw.strip().lower().replace(" ", "_").replace("-", "_")
    return HEADER_ALIASES.get(cleaned, cleaned)


def _parse_date(raw: str) -> date:
    from datetime import datetime
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
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

    # Build list of dicts matching CSV reader format
    result_rows = []
    for row in rows[1:]:
        row_dict = {}
        for i, raw_h in enumerate(raw_headers):
            if raw_h:
                row_dict[raw_h] = str(row[i]).strip() if row[i] is not None else ""
        result_rows.append(row_dict)

    return result_rows, normalised_headers


def _build_sale_record(norm_row: dict, user_id, user_currency: str, store_id: Optional[Any] = None) -> SaleRecord:
    qty = float(norm_row["quantity"])
    unit_price = float(norm_row["unit_price"])
    total_revenue = qty * unit_price
    cogs_raw = norm_row.get("cogs", "").strip()
    cogs = float(cogs_raw) if cogs_raw else None
    margin = None
    if cogs is not None and total_revenue > 0:
        margin = round(((total_revenue - (cogs * qty)) / total_revenue) * 100, 2)

    return SaleRecord(
        user_id=user_id,
        store_id=store_id,
        product_name=norm_row["product_name"].strip(),
        product_sku=norm_row.get("sku", "").strip() or None,
        product_category=norm_row.get("category", "Other").strip() or "Other",
        quantity_sold=qty,
        unit_price=unit_price,
        total_revenue=total_revenue,
        cogs=(cogs * qty) if cogs is not None else None,
        gross_margin=margin,
        sale_date=_parse_date(norm_row["date"]),
        customer_segment=norm_row.get("customer_segment", "").strip() or None,
        currency=norm_row.get("currency", "").strip() or user_currency,
        source="csv_upload",
    )


@router.post("/upload-csv")
async def upload_sales_csv(
    file: UploadFile = File(...),
    store_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV or Excel (.xlsx) file of sales records.
    Auto-detects column headers using alias mapping (15+ aliases).

    Supported formats: .csv, .txt, .xlsx
    Required columns: product_name, quantity, unit_price, date
    Optional: sku, category, cogs, customer_segment, currency
    """
    filename = file.filename or ""
    is_xlsx = filename.lower().endswith(".xlsx")
    is_csv = filename.lower().endswith((".csv", ".txt"))

    if not is_xlsx and not is_csv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported formats: .csv, .txt, .xlsx",
        )

    content = await file.read()

    # File size check (10 MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 10 MB limit.",
        )

    try:
        if is_xlsx:
            raw_rows, normalised_headers = _parse_xlsx_rows(content)
            source = "excel_upload"
        else:
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
            raw_rows, normalised_headers = _parse_csv_rows(text)
            source = "csv_upload"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    user_currency = current_user.currency or "INR"
    records = []
    errors = []

    parsed_store_id = None
    if store_id:
        try:
            import uuid
            parsed_store_id = uuid.UUID(store_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid store_id format")

    for line_num, row in enumerate(raw_rows, start=2):
        norm_row = {_normalise_header(k): v for k, v in row.items()}
        try:
            record = _build_sale_record(norm_row, current_user.id, user_currency, store_id=parsed_store_id)
            record.source = source
            records.append(record)
        except Exception as e:
            errors.append(f"Row {line_num}: {e}")

    if not records and errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No valid rows parsed. First error: {errors[0]}",
        )

    # Batch insert
    batch_size = 100
    for i in range(0, len(records), batch_size):
        db.add_all(records[i: i + batch_size])
        await db.commit()

    return {
        "inserted": len(records),
        "errors": len(errors),
        "error_details": errors[:10],
        "message": f"Successfully imported {len(records)} sale records.",
        "format": "xlsx" if is_xlsx else "csv",
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
