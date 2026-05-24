from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..models.db import SaleRecord
from ..services.gemini import gemini_service
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)


def custom_holt_winters_additive(series: List[float], seasonal_periods: int = 7, forecast_periods: int = 14) -> List[float]:
    """
    Pure Python/NumPy additive Holt-Winters triple exponential smoothing.
    Optimizes smoothing constants alpha, beta, gamma via a fast grid search to minimize SSE.
    """
    import numpy as np
    y = np.array(series, dtype=float)
    n = len(y)
    L = seasonal_periods
    
    if n < 2 * L:
        # Fallback to simple rolling average if not enough seasons
        avg = float(np.mean(y)) if n > 0 else 0.0
        return [avg] * forecast_periods
        
    # Initial level: mean of first L values
    l_init = float(np.mean(y[:L]))
    
    # Initial trend: average difference between corresponding seasons
    b_init = float(np.mean([y[L + i] - y[i] for i in range(L)])) / L
    
    # Initial seasonality: deviation from the level for first season
    s_init = list(y[:L] - l_init)
    
    # Fast grid search to minimize Sum of Squared Errors (SSE)
    best_sse = float("inf")
    best_params = (0.2, 0.1, 0.3)
    
    # Coarse search space
    grid_vals = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    for alpha in grid_vals:
        for beta in grid_vals:
            for gamma in grid_vals:
                l = l_init
                b = b_init
                s = s_init.copy()
                
                sse = 0.0
                for t in range(n):
                    y_t = y[t]
                    s_prev = s[t % L]
                    
                    y_hat = l + b + s_prev
                    sse += (y_t - y_hat) ** 2
                    
                    l_next = alpha * (y_t - s_prev) + (1 - alpha) * (l + b)
                    b_next = beta * (l_next - l) + (1 - beta) * b
                    s[t % L] = gamma * (y_t - l_next) + (1 - gamma) * s_prev
                    
                    l = l_next
                    b = b_next
                
                if sse < best_sse:
                    best_sse = sse
                    best_params = (alpha, beta, gamma)
                    
    # Fit model with optimized parameters
    alpha, beta, gamma = best_params
    l = l_init
    b = b_init
    s = s_init.copy()
    
    for t in range(n):
        y_t = y[t]
        s_prev = s[t % L]
        
        l_next = alpha * (y_t - s_prev) + (1 - alpha) * (l + b)
        b_next = beta * (l_next - l) + (1 - beta) * b
        s[t % L] = gamma * (y_t - l_next) + (1 - gamma) * s_prev
        
        l = l_next
        b = b_next
        
    # Generate forecast
    forecast_vals = []
    for m in range(1, forecast_periods + 1):
        s_idx = (n + m - 1) % L
        forecast_vals.append(l + m * b + s[s_idx])
        
    return [max(float(val), 0.0) for val in forecast_vals]


def custom_kmeans(X: np.ndarray, n_clusters: int = 4, max_iter: int = 300, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Pure Python/NumPy implementation of K-Means clustering.
    Returns:
        labels (np.ndarray): cluster assignment index per sample.
        centroids (np.ndarray): computed cluster centroids.
    """
    import numpy as np
    n_samples = X.shape[0]
    if n_samples < n_clusters:
        raise ValueError("Number of samples must be >= n_clusters")
        
    # Seed pseudo-random generator deterministically
    rng = np.random.default_rng(random_state)
    
    # Initialize centroids: select n_clusters distinct random samples
    initial_indices = rng.choice(n_samples, size=n_clusters, replace=False)
    centroids = X[initial_indices].copy()
    
    labels = np.zeros(n_samples, dtype=int)
    
    for _ in range(max_iter):
        # Euclidean distance from each sample to each centroid
        distances = np.linalg.norm(X[:, np.newaxis, :] - centroids[np.newaxis, :, :], axis=2)
        new_labels = np.argmin(distances, axis=1)
        
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        
        # Update centroids
        new_centroids = np.zeros_like(centroids)
        for k in range(n_clusters):
            members = X[labels == k]
            if len(members) > 0:
                new_centroids[k] = np.mean(members, axis=0)
            else:
                # Fallback in case of empty cluster: reinitialize with random data point
                new_centroids[k] = X[rng.choice(n_samples)]
        centroids = new_centroids
        
    return labels, centroids



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
        totals_row = r.one()
        total_revenue = float(totals_row.revenue)
        total_cogs = float(totals_row.cogs)
        num_sales_count = int(totals_row.num_sales)  # captured before any list-comp overwrites `row`
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

        # ── 5. Adaptive Z-Score Demand Spike Detection ───────────────────────
        # Evaluates each product's weekly volume over a 12-week rolling window
        # We retrieve daily transactions for the last 91 days (covering current week + 12 historical weeks)
        lookback_start = today - timedelta(days=90)
        daily_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= lookback_start,
            SaleRecord.sale_date <= today,
        ]
        if store_id is not None:
            daily_cond.append(SaleRecord.store_id == store_id)

        stmt_daily = (
            select(
                SaleRecord.product_name,
                SaleRecord.sale_date,
                func.sum(SaleRecord.quantity_sold).label("daily_qty"),
            )
            .where(and_(*daily_cond))
            .group_by(SaleRecord.product_name, SaleRecord.sale_date)
        )
        r_daily = await db.execute(stmt_daily)
        
        product_daily_sales = {}
        for row in r_daily.all():
            p_name = row.product_name
            if p_name not in product_daily_sales:
                product_daily_sales[p_name] = {}
            product_daily_sales[p_name][row.sale_date] = float(row.daily_qty)

        import math
        demand_signals = []
        
        for p_name, sales in product_daily_sales.items():
            # Build 13 weekly bins: Week 0 is current week (last 7 days), Weeks 1..12 are prior 12 weeks
            weeks = [0.0] * 13
            for sale_date, qty in sales.items():
                days_ago = (today - sale_date).days
                if 0 <= days_ago < 91:
                    week_idx = days_ago // 7
                    if week_idx < 13:
                        weeks[week_idx] += qty
            
            q_current = weeks[0]
            historical_weeks = weeks[1:]  # Weeks 1 to 12 (12 weeks total)
            
            # Active weeks means historical weeks with non-zero sales
            active_weeks = [w for w in historical_weeks if w > 0]
            num_active = len(active_weeks)
            
            if len(historical_weeks) > 0:
                mean_vol = sum(historical_weeks) / len(historical_weeks)
                variance = sum((w - mean_vol) ** 2 for w in historical_weeks) / len(historical_weeks)
                std_dev = math.sqrt(variance)
            else:
                mean_vol = 0.0
                std_dev = 0.0
                
            # If the product has at least 4 active weeks of data and std_dev > 0.1, compute Z-score
            if num_active >= 4 and std_dev > 0.1:
                z_score = (q_current - mean_vol) / std_dev
                if z_score > 2.0:
                    deviation_pct = round(((q_current - mean_vol) / mean_vol * 100), 1) if mean_vol > 0 else 0.0
                    demand_signals.append({
                        "product_name": p_name,
                        "type": "spike",
                        "z_score": round(z_score, 2),
                        "deviation_pct": deviation_pct,
                        "message": f"Demand surge: Z-score of {z_score:.2f} (+{deviation_pct}% deviation)",
                        "recent_qty": q_current,
                        "prior_weekly_avg": round(mean_vol, 1),
                    })
            else:
                # Defensive Fallback: 1.5x rolling average ratio
                prior_weekly_avg = sum(historical_weeks) / 12.0
                if prior_weekly_avg > 0 and q_current >= prior_weekly_avg * 1.5:
                    multiplier = round(q_current / prior_weekly_avg, 1)
                    deviation_pct = round(((q_current - prior_weekly_avg) / prior_weekly_avg * 100), 1)
                    demand_signals.append({
                        "product_name": p_name,
                        "type": "spike",
                        "z_score": 0.0,
                        "deviation_pct": deviation_pct,
                        "message": f"Sales up {multiplier}x vs rolling average (fallback)",
                        "recent_qty": q_current,
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

        # ── 8. Aggregate Store-Level 14-Day Holt-Winters Revenue Forecast ───────
        lookback_start_90d = today - timedelta(days=89)
        rev_cond_90d = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= lookback_start_90d,
            SaleRecord.sale_date <= today,
        ]
        if store_id is not None:
            rev_cond_90d.append(SaleRecord.store_id == store_id)

        stmt_rev_daily = (
            select(
                SaleRecord.sale_date,
                func.sum(SaleRecord.total_revenue).label("daily_rev")
            )
            .where(and_(*rev_cond_90d))
            .group_by(SaleRecord.sale_date)
        )
        r_rev_daily = await db.execute(stmt_rev_daily)
        daily_rev_map = {row.sale_date: float(row.daily_rev or 0.0) for row in r_rev_daily.all()}

        rev_history = []
        for i in range(90):
            d = lookback_start_90d + timedelta(days=i)
            rev_history.append(daily_rev_map.get(d, 0.0))

        active_rev_days = sum(1 for val in rev_history if val > 0)
        forecast_vals = []
        fitted_rev_hw = False

        if active_rev_days >= 15:
            try:
                forecast_vals = custom_holt_winters_additive(
                    rev_history,
                    seasonal_periods=7,
                    forecast_periods=14
                )
                fitted_rev_hw = True
            except Exception as e:
                logger.warning(f"Store revenue Holt-Winters forecasting failed, using fallback: {e}")

        if not fitted_rev_hw:
            # Fallback projection: rolling average of the last 14 days with weekday seasonality
            last_14_days = rev_history[-14:]
            avg_rev = sum(last_14_days) / len(last_14_days) if any(last_14_days) else 100.0
            weekday_factors = [1.0] * 7
            for day_idx in range(7):
                day_vals = [rev_history[idx] for idx in range(day_idx, 90, 7) if rev_history[idx] > 0]
                if day_vals:
                    overall_avg = sum(rev_history) / active_rev_days if active_rev_days > 0 else 1.0
                    weekday_factors[day_idx] = (sum(day_vals) / len(day_vals)) / overall_avg if overall_avg > 0 else 1.0

            for i in range(14):
                f_date = today + timedelta(days=i + 1)
                w_factor = weekday_factors[f_date.weekday()]
                forecast_vals.append(max(avg_rev * w_factor, 0.0))

        # Calculate historical standard deviation and mean for daily revenue
        active_rev_history = [val for val in rev_history if val > 0]
        hist_std = float(np.std(active_rev_history)) if active_rev_history else 0.0

        revenue_forecast_14d = []
        for i in range(14):
            f_date = today + timedelta(days=i + 1)
            f_val = forecast_vals[i]
            # 95% confidence bands
            forecast_lower = max(f_val - 1.96 * hist_std, 0.0)
            forecast_upper = f_val + 1.96 * hist_std

            revenue_forecast_14d.append({
                "date": str(f_date),
                "revenue": round(f_val, 2),
                "forecast_lower": round(forecast_lower, 2),
                "forecast_upper": round(forecast_upper, 2),
            })

        # ── 9. Customer Segment Analytics SQL ────────────────────────────────
        seg_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= start_date,
            SaleRecord.sale_date <= end_date,
        ]
        if store_id is not None:
            seg_cond.append(SaleRecord.store_id == store_id)

        stmt_seg = (
            select(
                SaleRecord.customer_segment,
                func.sum(SaleRecord.total_revenue).label("revenue"),
                func.sum(SaleRecord.cogs).label("cogs"),
                func.count(SaleRecord.id).label("num_orders"),
            )
            .where(and_(*seg_cond))
            .group_by(SaleRecord.customer_segment)
        )
        r_seg = await db.execute(stmt_seg)
        seg_rows = r_seg.all()

        prev_seg_cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= prev_start,
            SaleRecord.sale_date <= prev_end,
        ]
        if store_id is not None:
            prev_seg_cond.append(SaleRecord.store_id == store_id)

        stmt_prev_seg = (
            select(
                SaleRecord.customer_segment,
                func.sum(SaleRecord.total_revenue).label("revenue"),
            )
            .where(and_(*prev_seg_cond))
            .group_by(SaleRecord.customer_segment)
        )
        r_prev_seg = await db.execute(stmt_prev_seg)
        prev_seg_map = {row.customer_segment: float(row.revenue or 0.0) for row in r_prev_seg.all()}

        customer_segments = []
        total_seg_revenue = sum(float(row.revenue or 0.0) for row in seg_rows)

        for row in seg_rows:
            seg_name = row.customer_segment or "Walk-in"
            rev = float(row.revenue or 0.0)
            cogs = float(row.cogs or 0.0)
            num_orders = int(row.num_orders or 0)

            margin = rev - cogs
            margin_pct = round((margin / rev * 100) if rev > 0 else 0.0, 2)
            aov = round((rev / num_orders) if num_orders > 0 else 0.0, 2)
            share = round((rev / total_seg_revenue * 100) if total_seg_revenue > 0 else 0.0, 2)

            prev_rev = prev_seg_map.get(row.customer_segment, 0.0)
            mom_change = round(((rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0.0, 2)

            customer_segments.append({
                "segment": seg_name,
                "revenue": round(rev, 2),
                "cogs": round(cogs, 2),
                "margin_pct": margin_pct,
                "aov": aov,
                "share": share,
                "mom_growth_pct": mom_change,
                "num_orders": num_orders
            })

        existing_segs = {s["segment"] for s in customer_segments}
        for default_seg in ["Walk-in", "Online", "B2B"]:
            if default_seg not in existing_segs:
                customer_segments.append({
                    "segment": default_seg,
                    "revenue": 0.0,
                    "cogs": 0.0,
                    "margin_pct": 0.0,
                    "aov": 0.0,
                    "share": 0.0,
                    "mom_growth_pct": 0.0,
                    "num_orders": 0
                })

        # ── 10. AI insight via Gemini ─────────────────────────────────────────
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
            "num_sales": num_sales_count,
            "top_products": top_products,
            "category_breakdown": category_breakdown,
            "demand_signals": demand_signals,
            "dead_stock_alerts": dead_stock_alerts,
            "margin_erosion_alerts": margin_erosion_alerts,
            "ai_insight": ai_insight,
            "revenue_forecast_14d": revenue_forecast_14d,
            "customer_segments": customer_segments,
            # Period metadata — used by frontend to label charts
            "period": period,
            "date_from": str(start_date),
            "date_to": str(end_date),
        }

    # ── Holt-Winters & Triple Exponential Smoothing Demand Forecasting ────────

    async def get_demand_forecast(
        self, db: AsyncSession, user_id: Any, store_id: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Statsmodels Holt-Winters triple exponential smoothing demand forecast per product,
        forecasting 14 days into the future.
        
        Defensive Fallback:
          - If product has < 15 active days or sparse history, or fitting errors out,
            falls back to weighted 7-day rolling average forecast.
        """
        today = date.today()
        lookback_start = today - timedelta(days=89)  # 90 days total

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

            # Build dense 90-day daily series (oldest to newest)
            history_series = []
            for i in range(90):
                d = lookback_start + timedelta(days=i)
                history_series.append(daily.get(d, 0.0))

            # Count active days (days where sales > 0)
            active_days = sum(1 for qty in history_series if qty > 0)

            forecast_vals = []
            fitted_hw = False

            if active_days >= 15:
                try:
                    forecast_vals = custom_holt_winters_additive(
                        history_series,
                        seasonal_periods=7,
                        forecast_periods=14
                    )
                    fitted_hw = True
                except Exception as e:
                    logger.warning(f"Holt-Winters failed for product {product_name}: {e}")

            if not fitted_hw:
                # Weighted 7-day rolling average fallback (v1)
                recent_7 = [daily.get(today - timedelta(days=i + 1), 0.0) for i in range(6, -1, -1)]
                total_weight = sum(weights)
                weighted_sum = sum(w * q for w, q in zip(weights, recent_7))
                forecast_daily = weighted_sum / total_weight if total_weight > 0 else 0.0
                forecast_vals = [forecast_daily] * 14

            # Calculate 7-day and 14-day forecasts
            forecast_7d = round(sum(forecast_vals[:7]), 1)
            forecast_14d = round(sum(forecast_vals), 1)

            # Trend direction: compare recent_7d_qty to prior_7d_qty
            recent_7_sum = sum([daily.get(today - timedelta(days=i + 1), 0.0) for i in range(6, -1, -1)])
            prior_7_sum = sum([daily.get(today - timedelta(days=i + 8), 0.0) for i in range(6, -1, -1)])

            if prior_7_sum == 0:
                trend = "new"
            elif forecast_7d > prior_7_sum * 1.1:
                trend = "up"
            elif forecast_7d < prior_7_sum * 0.9:
                trend = "down"
            else:
                trend = "flat"

            confidence = "high" if active_days >= 30 else "medium" if active_days >= 15 else "low"

            # Calculate standard deviation of product historical daily quantities
            active_history = [val for val in history_series if val > 0]
            prod_std = float(np.std(active_history)) if active_history else 0.0

            if forecast_7d > 0 or forecast_14d > 0:
                forecasts.append({
                    "product_name": product_name,
                    "category": data["category"],
                    "forecast_qty_7d": forecast_7d,
                    "forecast_qty_14d": forecast_14d,
                    "forecast_lower_7d": max(round(forecast_7d - 1.96 * prod_std * np.sqrt(7), 1), 0.0),
                    "forecast_upper_7d": round(forecast_7d + 1.96 * prod_std * np.sqrt(7), 1),
                    "forecast_lower_14d": max(round(forecast_14d - 1.96 * prod_std * np.sqrt(14), 1), 0.0),
                    "forecast_upper_14d": round(forecast_14d + 1.96 * prod_std * np.sqrt(14), 1),
                    "recent_7d_qty": round(recent_7_sum, 1),
                    "prior_7d_qty": round(prior_7_sum, 1),
                    "trend": trend,
                    "confidence": confidence,
                    "forecast_method": "holt-winters" if fitted_hw else "rolling-average-fallback"
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

    async def get_portfolio_clusters(
        self,
        db: AsyncSession,
        user_id: Any,
        period: str = "mtd",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        store_id: Optional[Any] = None,
        k: int = 4,
    ) -> Dict[str, Any]:
        """
        Auto-segment the store's product portfolio using unsupervised K-Means clustering.
        """
        start_date, end_date = _resolve_date_range(period, date_from, date_to)
        today = date.today()

        cond = [
            SaleRecord.user_id == user_id,
            SaleRecord.sale_date >= start_date,
            SaleRecord.sale_date <= end_date,
        ]
        if store_id is not None:
            cond.append(SaleRecord.store_id == store_id)

        stmt = (
            select(
                SaleRecord.product_name,
                func.sum(SaleRecord.total_revenue).label("revenue"),
                func.sum(SaleRecord.cogs).label("cogs"),
                func.sum(SaleRecord.quantity_sold).label("qty"),
                func.max(SaleRecord.sale_date).label("last_sale"),
            )
            .where(and_(*cond))
            .group_by(SaleRecord.product_name)
        )
        res = await db.execute(stmt)
        rows = res.all()

        if not rows:
            return {"clusters": [], "centroids": {}}

        products = []
        features = []

        for row in rows:
            revenue = float(row.revenue or 0.0)
            cogs = float(row.cogs or 0.0)
            qty = float(row.qty or 0.0)
            last_sale = row.last_sale
            
            margin_pct = ((revenue - cogs) / revenue * 100) if revenue > 0 else 0.0
            recency_days = (today - last_sale).days if last_sale else 90.0

            products.append({
                "product_name": row.product_name,
                "metrics": {
                    "revenue": round(revenue, 2),
                    "margin_pct": round(margin_pct, 2),
                    "qty": round(qty, 1),
                    "recency": recency_days
                }
            })
            # Features: Revenue, Margin, Velocity, Recency
            features.append([revenue, margin_pct, qty, recency_days])

        X = np.array(features, dtype=float)

        # Defensive Fallback: If less than 4 products, heuristic assignment
        if len(products) < 4:
            # Simple averages
            avg_rev = np.mean(X[:, 0]) if len(products) > 0 else 0.0
            avg_margin = np.mean(X[:, 1]) if len(products) > 0 else 0.0
            
            clusters_out = []
            for i, p in enumerate(products):
                rev = p["metrics"]["revenue"]
                margin = p["metrics"]["margin_pct"]
                
                if rev >= avg_rev:
                    quadrant = "Stars" if margin >= avg_margin else "Cash Cows"
                else:
                    quadrant = "Hidden Gems" if margin >= avg_margin else "Dead Weight"
                
                # Mock scaled coordinates for rendering in quadrants
                x_coord = 0.5 if rev >= avg_rev else -0.5
                y_coord = 0.5 if margin >= avg_margin else -0.5
                
                clusters_out.append({
                    "product_name": p["product_name"],
                    "quadrant": quadrant,
                    "coordinates": {"x": x_coord, "y": y_coord},
                    "metrics": p["metrics"]
                })
            
            centroids = {
                "Stars": {"x": 0.5, "y": 0.5},
                "Hidden Gems": {"x": -0.5, "y": 0.5},
                "Cash Cows": {"x": 0.5, "y": -0.5},
                "Dead Weight": {"x": -0.5, "y": -0.5}
            }
            return {"clusters": clusters_out, "centroids": centroids}

        # Otherwise, fit K-Means
        import itertools

        # Custom StandardScaler
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        std = np.where(std == 0, 1.0, std)
        X_scaled = (X - mean) / std

        # Fit K-Means with dynamic clusters count
        actual_k = min(k, len(products))
        labels, centroids_scaled = custom_kmeans(X_scaled, n_clusters=actual_k, random_state=42)

        # Map cluster labels to quadrants or custom named clusters
        label_to_quadrant = {}
        if actual_k == 4:
            # Determine best assignment permutation between cluster labels and archetypes
            archetypes = {
                "Stars": np.array([1.0, 1.0, 1.0, -1.0]),
                "Hidden Gems": np.array([-0.5, 1.0, -0.5, 0.0]),
                "Cash Cows": np.array([1.0, -0.5, 1.0, -0.5]),
                "Dead Weight": np.array([-1.0, -1.0, -1.0, 1.0]),
            }
            quadrant_names = ["Stars", "Hidden Gems", "Cash Cows", "Dead Weight"]

            best_perm = None
            min_total_dist = float("inf")

            for perm in itertools.permutations(range(4)):
                total_dist = 0.0
                for quad_idx, cluster_lbl in enumerate(perm):
                    quad_name = quadrant_names[quad_idx]
                    arch_vec = archetypes[quad_name]
                    cent_vec = centroids_scaled[cluster_lbl]
                    total_dist += np.linalg.norm(cent_vec - arch_vec)
                
                if total_dist < min_total_dist:
                    min_total_dist = total_dist
                    best_perm = perm

            for quad_idx, cluster_lbl in enumerate(best_perm):
                label_to_quadrant[cluster_lbl] = quadrant_names[quad_idx]
        else:
            # Map based on centroid quadrant characteristics
            for cluster_lbl in range(actual_k):
                cx = float(centroids_scaled[cluster_lbl, 0])
                cy = float(centroids_scaled[cluster_lbl, 1])
                if cx >= 0:
                    quad = "Stars" if cy >= 0 else "Cash Cows"
                else:
                    quad = "Hidden Gems" if cy >= 0 else "Dead Weight"
                label_to_quadrant[cluster_lbl] = f"{quad} (Cluster {cluster_lbl + 1})"

        # Construct response
        clusters_out = []
        for i, p in enumerate(products):
            lbl = labels[i]
            quadrant = label_to_quadrant[lbl]
            
            # x is scaled revenue, y is scaled margin
            x_coord = float(X_scaled[i, 0])
            y_coord = float(X_scaled[i, 1])

            # Clamp coordinates to a reasonable range for rendering safety [-2.5, 2.5]
            x_coord = max(min(x_coord, 2.5), -2.5)
            y_coord = max(min(y_coord, 2.5), -2.5)

            clusters_out.append({
                "product_name": p["product_name"],
                "quadrant": quadrant,
                "coordinates": {"x": x_coord, "y": y_coord},
                "metrics": p["metrics"]
            })

        # Centroids coordinates for output
        centroids = {}
        for cluster_lbl, quad_name in label_to_quadrant.items():
            cx = float(centroids_scaled[cluster_lbl, 0])
            cy = float(centroids_scaled[cluster_lbl, 1])
            centroids[quad_name] = {
                "x": max(min(cx, 2.5), -2.5),
                "y": max(min(cy, 2.5), -2.5)
            }

        return {"clusters": clusters_out, "centroids": centroids}


retail_intelligence_service = RetailIntelligenceService()
