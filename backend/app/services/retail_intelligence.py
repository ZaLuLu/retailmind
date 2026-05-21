from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..models.db import SaleRecord
from ..services.gemini import gemini_service
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def _resolve_date_range(
    period: str,
    date_from: Optional[date],
    date_to: Optional[date],
) -> Tuple[date, date]:
    """
    Resolve the active date window from period shorthand or explicit dates.

    period values: 'mtd' | '7d' | '30d' | '90d' | 'custom'
    Falls back to MTD if period is unrecognised.
    """
    today = date.today()

    if period == "7d":
        return today - timedelta(days=6), today
    elif period == "30d":
        return today - timedelta(days=29), today
    elif period == "90d":
        return today - timedelta(days=89), today
    elif period == "custom" and date_from and date_to:
        return date_from, date_to
    else:
        # Default: month-to-date
        return today.replace(day=1), today


class RetailIntelligenceService:
    """
    Core analytics engine for RetailMind.
    All computations are against the SaleRecord table.

    Phase 2 additions:
    - Date range support (7d / 30d / 90d / custom / mtd)
    - Demand forecasting v1 (weighted rolling average per product)
    - Export data method (used by /retail/export-csv)
    """

    async def get_retail_summary(
        self,
        db: AsyncSession,
        user_id: Any,
        period: str = "mtd",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        store_id: Optional[Any] = None,
    ) -> Dict[str, Any]:

        start_date, end_date = _resolve_date_range(period, date_from, date_to)
        today = date.today()

        # Previous equivalent window for MoM/period comparison
        window_days = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=window_days)
        prev_end = start_date - timedelta(days=1)

        # ── 1. Current period totals ─────────────────────────────────────────
        totals_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= start_date,
            SaleRecord.sale_date <= end_date,
        ]
        if store_id is not None:
            totals_cond.append(SaleRecord.store_id == store_id)
        stmt_totals = select(
            func.coalesce(func.sum(SaleRecord.total_revenue), 0).label("revenue"),
            func.coalesce(func.sum(SaleRecord.cogs), 0).label("cogs"),
            func.count(SaleRecord.id).label("num_sales"),
        ).where(and_(*totals_cond))
        r = await db.execute(stmt_totals)
        row = r.one()
        total_revenue = float(row.revenue)
        total_cogs = float(row.cogs)
        gross_profit = total_revenue - total_cogs
        overall_margin_pct = round(
            (gross_profit / total_revenue * 100) if total_revenue > 0 else 0.0, 2
        )

        # ── 2. Previous period revenue (for period-over-period %) ────────────
        prev_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= prev_start,
            SaleRecord.sale_date <= prev_end,
        ]
        if store_id is not None:
            prev_cond.append(SaleRecord.store_id == store_id)
        stmt_prev = select(
            func.coalesce(func.sum(SaleRecord.total_revenue), 0).label("revenue")
        ).where(and_(*prev_cond))
        r_prev = await db.execute(stmt_prev)
        prev_revenue = float(r_prev.scalar_one())
        mom_change_pct = round(
            ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0.0, 2
        )

        # ── 3. Top 5 products by revenue (within period) ─────────────────────
        top_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= start_date,
            SaleRecord.sale_date <= end_date,
        ]
        if store_id is not None:
            top_cond.append(SaleRecord.store_id == store_id)
        stmt_top = (
            select(
                SaleRecord.product_name,
                SaleRecord.product_category,
                func.sum(SaleRecord.total_revenue).label("revenue"),
                func.sum(SaleRecord.quantity_sold).label("quantity"),
                func.avg(SaleRecord.gross_margin).label("avg_margin"),
            )
            .where(and_(*top_cond))
            .group_by(SaleRecord.product_name, SaleRecord.product_category)
            .order_by(func.sum(SaleRecord.total_revenue).desc())
            .limit(5)
        )
        r_top = await db.execute(stmt_top)
        top_products = [
            {
                "product_name": row.product_name,
                "category": row.product_category,
                "revenue": round(float(row.revenue), 2),
                "quantity": round(float(row.quantity), 1),
                "margin_pct": round(float(row.avg_margin) if row.avg_margin else 0.0, 2),
            }
            for row in r_top.all()
        ]

        # ── 4. Category breakdown (within period) ────────────────────────────
        cats_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= start_date,
            SaleRecord.sale_date <= end_date,
        ]
        if store_id is not None:
            cats_cond.append(SaleRecord.store_id == store_id)
        stmt_cats = (
            select(
                SaleRecord.product_category,
                func.sum(SaleRecord.total_revenue).label("revenue"),
                func.coalesce(func.sum(SaleRecord.cogs), 0).label("cogs"),
                func.avg(SaleRecord.gross_margin).label("avg_margin"),
            )
            .where(and_(*cats_cond))
            .group_by(SaleRecord.product_category)
            .order_by(func.sum(SaleRecord.total_revenue).desc())
        )
        r_cats = await db.execute(stmt_cats)
        category_breakdown = [
            {
                "category": row.product_category,
                "revenue": round(float(row.revenue), 2),
                "cogs": round(float(row.cogs), 2),
                "margin_pct": round(float(row.avg_margin) if row.avg_margin else 0.0, 2),
            }
            for row in r_cats.all()
        ]

        # ── 5. Demand spike detection (always uses last 7d vs prior 30d) ─────
        # Spike detection is always relative to today, not the selected period
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=37)

        recent_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= seven_days_ago,
            SaleRecord.sale_date <= today,
        ]
        prior_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= thirty_days_ago,
            SaleRecord.sale_date < seven_days_ago,
        ]
        if store_id is not None:
            recent_cond.append(SaleRecord.store_id == store_id)
            prior_cond.append(SaleRecord.store_id == store_id)

        stmt_recent = (
            select(
                SaleRecord.product_name,
                func.sum(SaleRecord.quantity_sold).label("qty_recent"),
            )
            .where(and_(*recent_cond))
            .group_by(SaleRecord.product_name)
        )
        stmt_prior = (
            select(
                SaleRecord.product_name,
                func.sum(SaleRecord.quantity_sold).label("qty_prior"),
            )
            .where(and_(*prior_cond))
            .group_by(SaleRecord.product_name)
        )

        r_recent = await db.execute(stmt_recent)
        r_prior = await db.execute(stmt_prior)

        recent_map = {row.product_name: float(row.qty_recent) for row in r_recent.all()}
        prior_map = {row.product_name: float(row.qty_prior) for row in r_prior.all()}

        demand_signals: List[Dict] = []
        for product, recent_qty in recent_map.items():
            prior_qty = prior_map.get(product, 0)
            prior_weekly_avg = prior_qty / 4.3 if prior_qty > 0 else 0
            if prior_weekly_avg > 0 and recent_qty >= prior_weekly_avg * 1.5:
                multiplier = round(recent_qty / prior_weekly_avg, 1)
                demand_signals.append({
                    "product_name": product,
                    "type": "spike",
                    "message": f"Sales up {multiplier}x vs 30-day weekly avg",
                    "recent_qty": recent_qty,
                    "prior_weekly_avg": round(prior_weekly_avg, 1),
                })
        demand_signals = sorted(demand_signals, key=lambda x: x["recent_qty"], reverse=True)[:5]

        # ── 6. Dead stock alerts ──────────────────────────────────────────────
        thirty_days_ago_simple = today - timedelta(days=30)
        ninety_days_ago = today - timedelta(days=90)

        had_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= ninety_days_ago,
            SaleRecord.sale_date < thirty_days_ago_simple,
        ]
        recent_sales_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= thirty_days_ago_simple,
        ]
        if store_id is not None:
            had_cond.append(SaleRecord.store_id == store_id)
            recent_sales_cond.append(SaleRecord.store_id == store_id)

        stmt_had_sales = (
            select(SaleRecord.product_name, func.max(SaleRecord.sale_date).label("last_sale"))
            .where(and_(*had_cond))
            .group_by(SaleRecord.product_name)
        )
        r_had = await db.execute(stmt_had_sales)
        products_with_prior_sales = {row.product_name: row.last_sale for row in r_had.all()}

        stmt_recent_sales = (
            select(SaleRecord.product_name)
            .where(and_(*recent_sales_cond))
            .group_by(SaleRecord.product_name)
        )
        r_rec = await db.execute(stmt_recent_sales)
        active_products = {row.product_name for row in r_rec.all()}

        dead_stock_alerts = [
            {
                "product_name": name,
                "last_sale_days_ago": (today - last_sale).days,
                "message": f"No sales in {(today - last_sale).days} days",
            }
            for name, last_sale in products_with_prior_sales.items()
            if name not in active_products
        ]
        dead_stock_alerts = sorted(
            dead_stock_alerts, key=lambda x: x["last_sale_days_ago"], reverse=True
        )[:5]

        # ── 7. Margin erosion alerts ──────────────────────────────────────────
        margin_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.gross_margin.isnot(None),
        ]
        if store_id is not None:
            margin_cond.append(SaleRecord.store_id == store_id)
        stmt_margin = (
            select(
                SaleRecord.product_name,
                func.avg(SaleRecord.gross_margin).label("avg_margin"),
                func.sum(SaleRecord.total_revenue).label("revenue"),
            )
            .where(and_(*margin_cond))
            .group_by(SaleRecord.product_name)
            .having(func.avg(SaleRecord.gross_margin) < 20)
            .having(func.count(SaleRecord.id) >= 2)
            .order_by(func.avg(SaleRecord.gross_margin).asc())
            .limit(5)
        )
        r_margin = await db.execute(stmt_margin)
        margin_erosion_alerts = [
            {
                "product_name": row.product_name,
                "margin_pct": round(float(row.avg_margin), 2),
                "revenue": round(float(row.revenue), 2),
                "message": f"Margin at {round(float(row.avg_margin), 1)}% — below 20% threshold",
            }
            for row in r_margin.all()
        ]

        # ── 8. AI insight via Gemini ──────────────────────────────────────────
        ai_insight = "Retail intelligence is processing your sales data..."
        try:
            period_label = {
                "7d": "last 7 days",
                "30d": "last 30 days",
                "90d": "last 90 days",
                "custom": f"{start_date} to {end_date}",
            }.get(period, "month-to-date")

            context = (
                f"Period: {period_label} | "
                f"Revenue: ₹{total_revenue:,.0f} | "
                f"Gross margin: {overall_margin_pct}% | "
                f"Period-over-period change: {'+' if mom_change_pct >= 0 else ''}{mom_change_pct}% | "
                f"Top category: {category_breakdown[0]['category'] if category_breakdown else 'N/A'} | "
                f"Dead stock items: {len(dead_stock_alerts)} | "
                f"Margin alerts: {len(margin_erosion_alerts)}"
            )
            ai_insight = await gemini_service.ask_advisor(
                "You are a retail business intelligence analyst. "
                "Write ONE sharp, actionable sentence (max 20 words) summarising the most important insight from this data. "
                "Sound like a Financial Times headline — factual, direct, no fluff.",
                context,
            )
        except Exception as e:
            logger.warning(f"Gemini AI insight failed: {e}")

        return {
            "total_revenue": total_revenue,
            "total_cogs": total_cogs,
            "gross_profit": gross_profit,
            "overall_margin_pct": overall_margin_pct,
            "mom_revenue_change_pct": mom_change_pct,
            "num_sales": int(row.num_sales),
            "top_products": top_products,
            "category_breakdown": category_breakdown,
            "demand_signals": demand_signals,
            "dead_stock_alerts": dead_stock_alerts,
            "margin_erosion_alerts": margin_erosion_alerts,
            "ai_insight": ai_insight,
            # Period metadata — used by frontend to label charts
            "period": period,
            "date_from": str(start_date),
            "date_to": str(end_date),
        }

    # ── Demand Forecasting v1 ─────────────────────────────────────────────────

    async def get_demand_forecast(
        self, db: AsyncSession, user_id: Any, store_id: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Weighted 7-day rolling average forecast per product.

        Algorithm:
          - Fetch last 28 days of daily qty per product
          - Apply weights [1,2,3,4,5,6,7] to the most recent 7 days
          - Forecast = weighted average of those 7 days
          - Trend = compare forecast to prior 7-day simple average
          - Confidence = based on number of data points available

        Returns top 10 products by forecast qty.
        """
        today = date.today()
        lookback_start = today - timedelta(days=27)  # 28 days total

        forecast_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= lookback_start,
            SaleRecord.sale_date <= today,
        ]
        if store_id is not None:
            forecast_cond.append(SaleRecord.store_id == store_id)

        stmt = (
            select(
                SaleRecord.product_name,
                SaleRecord.product_category,
                SaleRecord.sale_date,
                func.sum(SaleRecord.quantity_sold).label("daily_qty"),
            )
            .where(and_(*forecast_cond))
            .group_by(
                SaleRecord.product_name,
                SaleRecord.product_category,
                SaleRecord.sale_date,
            )
            .order_by(SaleRecord.product_name, SaleRecord.sale_date)
        )
        result = await db.execute(stmt)
        rows = result.all()

        # Group by product
        product_data: Dict[str, Dict] = {}
        for row in rows:
            name = row.product_name
            if name not in product_data:
                product_data[name] = {
                    "category": row.product_category,
                    "daily": {},  # date → qty
                }
            product_data[name]["daily"][row.sale_date] = float(row.daily_qty)

        forecasts = []
        weights = [1, 2, 3, 4, 5, 6, 7]  # day -7 to day -1 (most recent = highest weight)

        for product_name, data in product_data.items():
            daily = data["daily"]

            # Build ordered list of last 7 days
            recent_7 = []
            for i in range(6, -1, -1):  # day -7 to day -1
                d = today - timedelta(days=i + 1)
                recent_7.append(daily.get(d, 0.0))

            # Build prior 7 days (days -14 to -8) for trend comparison
            prior_7 = []
            for i in range(13, 6, -1):
                d = today - timedelta(days=i + 1)
                prior_7.append(daily.get(d, 0.0))

            total_weight = sum(weights)
            weighted_sum = sum(w * q for w, q in zip(weights, recent_7))
            forecast_daily = weighted_sum / total_weight if total_weight > 0 else 0.0
            forecast_7d = round(forecast_daily * 7, 1)

            prior_avg_daily = sum(prior_7) / 7 if any(prior_7) else 0.0
            prior_7d = prior_avg_daily * 7

            # Trend direction
            if prior_7d == 0:
                trend = "new"
            elif forecast_7d > prior_7d * 1.1:
                trend = "up"
            elif forecast_7d < prior_7d * 0.9:
                trend = "down"
            else:
                trend = "flat"

            # Confidence based on data density
            data_points = sum(1 for v in recent_7 if v > 0)
            if data_points >= 5:
                confidence = "high"
            elif data_points >= 3:
                confidence = "medium"
            else:
                confidence = "low"

            if forecast_7d > 0:
                forecasts.append({
                    "product_name": product_name,
                    "category": data["category"],
                    "forecast_qty_7d": forecast_7d,
                    "recent_7d_qty": round(sum(recent_7), 1),
                    "prior_7d_qty": round(prior_7d, 1),
                    "trend": trend,
                    "confidence": confidence,
                })

        # Sort by forecast qty descending, return top 10
        forecasts.sort(key=lambda x: x["forecast_qty_7d"], reverse=True)
        return forecasts[:10]

    # ── Export data ───────────────────────────────────────────────────────────

    async def get_export_data(
        self,
        db: AsyncSession,
        user_id: Any,
        search: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        store_id: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns filtered sale records for CSV export.
        Applies the same filters as the SalesLedger view.
        """
        conditions = [SaleRecord.user_id == user_id]
        if store_id is not None:
            conditions.append(SaleRecord.store_id == store_id)

        if search:
            from sqlalchemy import or_, cast, String
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
            .limit(10000)  # safety cap
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "product_name": r.product_name,
                "product_sku": r.product_sku or "",
                "product_category": r.product_category,
                "quantity_sold": r.quantity_sold,
                "unit_price": float(r.unit_price),
                "total_revenue": float(r.total_revenue),
                "cogs": float(r.cogs) if r.cogs is not None else "",
                "gross_margin": float(r.gross_margin) if r.gross_margin is not None else "",
                "sale_date": str(r.sale_date),
                "customer_segment": r.customer_segment or "",
                "currency": r.currency,
                "source": r.source,
            }
            for r in records
        ]


retail_intelligence_service = RetailIntelligenceService()
