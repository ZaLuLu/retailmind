"""
RetailMind Demo Seed Script
────────────────────────────
Generates a rich, 90-day synthetic dataset for the public demo deployment.

Usage:
    python backend/scripts/seed_demo_account.py          # idempotent (skips if already seeded)
    python backend/scripts/seed_demo_account.py --force  # always re-seeds

The dataset is carefully engineered so every ML feature produces compelling output:
  - Holt-Winters: visible trend + weekly seasonality across 90 days
  - K-Means: clean 4-quadrant separation (Stars / Cash Cows / Hidden Gems / Dead Weight)
  - Dead Stock alerts: 3 products with zero sales in last 30 days
  - Margin Erosion alerts: 2 products with margin drop > 8pp
  - Demand Spike alerts: 1 product with 200%+ WoW growth in most recent week
  - Customer segments: Walk-in 45% / Online 35% / B2B 20%
"""
from __future__ import annotations

import argparse
import asyncio
import os
import random
import sys
import uuid
from datetime import date, timedelta
from typing import Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.core.config import settings
from app.models.db import Alert, AIConversation, MLResult, SaleRecord, Store, User


# ── Fixed demo identity ────────────────────────────────────────────────────────
DEMO_USER_ID  = uuid.UUID(settings.DEMO_USER_ID)
DEMO_STORE_ID = uuid.UUID(settings.DEMO_STORE_ID)
DEMO_EMAIL    = "demo@retailmind.com"
DEMO_PASSWORD = "demo123"  # only used if DEMO_MODE=false fallback login needed


# ── Product catalogue ─────────────────────────────────────────────────────────
# Each product dict specifies realistic pricing and velocity behaviour.
# "velocity" = avg units sold per day (Poisson λ)
# "margin_pct" = target gross margin %
# "trend" = "stable" | "growing" | "declining" | "dead" | "spike"
PRODUCTS: list[dict[str, Any]] = [
    # Electronics — high margin, moderate volume
    {"sku": "E001", "name": "Wireless Bluetooth Headphones",   "category": "Electronics",   "price": 129.99, "cogs_pct": 0.56, "velocity": 3.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.3, "Online": 0.5, "B2B": 0.2}},
    {"sku": "E002", "name": "USB-C Fast Charger 65W",          "category": "Electronics",   "price": 39.99,  "cogs_pct": 0.40, "velocity": 5.0,  "trend": "growing",  "segment_mix": {"Walk-in": 0.4, "Online": 0.5, "B2B": 0.1}},
    {"sku": "E003", "name": "Premium Wireless Headphones",     "category": "Electronics",   "price": 199.99, "cogs_pct": 0.62, "velocity": 1.5,  "trend": "stable",   "segment_mix": {"Walk-in": 0.2, "Online": 0.4, "B2B": 0.4}},  # margin erosion
    {"sku": "E004", "name": "Smart Watch Fitness Tracker",     "category": "Electronics",   "price": 89.99,  "cogs_pct": 0.50, "velocity": 2.5,  "trend": "growing",  "segment_mix": {"Walk-in": 0.3, "Online": 0.6, "B2B": 0.1}},
    {"sku": "E005", "name": "Portable Bluetooth Speaker",      "category": "Electronics",   "price": 59.99,  "cogs_pct": 0.52, "velocity": 2.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.5, "B2B": 0.1}},
    {"sku": "E006", "name": "USB-C Hub 7-in-1",               "category": "Electronics",   "price": 49.99,  "cogs_pct": 0.45, "velocity": 3.5,  "trend": "spike",    "segment_mix": {"Walk-in": 0.3, "Online": 0.5, "B2B": 0.2}},  # demand spike
    {"sku": "E007", "name": "Wireless Charging Pad 15W",      "category": "Electronics",   "price": 34.99,  "cogs_pct": 0.48, "velocity": 2.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.4, "B2B": 0.2}},
    {"sku": "E008", "name": "Mechanical Keyboard RGB",         "category": "Electronics",   "price": 149.99, "cogs_pct": 0.55, "velocity": 1.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.2, "Online": 0.5, "B2B": 0.3}},

    # Apparel — high volume, lower margin, seasonal
    {"sku": "A001", "name": "Classic White T-Shirt",           "category": "Apparel",       "price": 24.99,  "cogs_pct": 0.45, "velocity": 8.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "A002", "name": "Slim Fit Denim Jeans",            "category": "Apparel",       "price": 59.99,  "cogs_pct": 0.50, "velocity": 4.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A003", "name": "Casual Hoodie Pullover",          "category": "Apparel",       "price": 44.99,  "cogs_pct": 0.48, "velocity": 5.0,  "trend": "growing",  "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A004", "name": "Running Shorts Athletic",         "category": "Apparel",       "price": 29.99,  "cogs_pct": 0.42, "velocity": 6.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A005", "name": "Formal Button-Down Shirt",        "category": "Apparel",       "price": 54.99,  "cogs_pct": 0.46, "velocity": 3.0,  "trend": "dead",     "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},  # dead stock
    {"sku": "A006", "name": "Winter Puffer Jacket",            "category": "Apparel",       "price": 99.99,  "cogs_pct": 0.55, "velocity": 2.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.4, "B2B": 0.2}},
    {"sku": "A007", "name": "Yoga Leggings High-Waist",        "category": "Apparel",       "price": 39.99,  "cogs_pct": 0.44, "velocity": 5.0,  "trend": "growing",  "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A008", "name": "Polo Shirt Classic Fit",          "category": "Apparel",       "price": 34.99,  "cogs_pct": 0.43, "velocity": 4.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "A009", "name": "Cargo Shorts Multi-Pocket",       "category": "Apparel",       "price": 44.99,  "cogs_pct": 0.46, "velocity": 3.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "A010", "name": "Summer Floral Dress",             "category": "Apparel",       "price": 49.99,  "cogs_pct": 0.47, "velocity": 3.5,  "trend": "growing",  "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "A011", "name": "Compression Socks Athletic",      "category": "Apparel",       "price": 14.99,  "cogs_pct": 0.35, "velocity": 7.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A012", "name": "Swim Trunks Beach Board",         "category": "Apparel",       "price": 32.99,  "cogs_pct": 0.44, "velocity": 2.0,  "trend": "dead",     "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},  # dead stock

    # Food & Beverage — very high frequency, thin margin
    {"sku": "F001", "name": "Premium Ground Coffee 500g",      "category": "Food & Beverage", "price": 18.99, "cogs_pct": 0.65, "velocity": 12.0, "trend": "stable",  "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},
    {"sku": "F002", "name": "Protein Bar Variety Pack 12ct",   "category": "Food & Beverage", "price": 29.99, "cogs_pct": 0.62, "velocity": 9.0,  "trend": "growing", "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "F003", "name": "Green Tea Premium 100 Bags",      "category": "Food & Beverage", "price": 14.99, "cogs_pct": 0.60, "velocity": 10.0, "trend": "stable",  "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},
    {"sku": "F004", "name": "Energy Drink 24-Pack",            "category": "Food & Beverage", "price": 49.99, "cogs_pct": 0.68, "velocity": 6.0,  "trend": "growing", "segment_mix": {"Walk-in": 0.4, "Online": 0.3, "B2B": 0.3}},
    {"sku": "F005", "name": "Almond Milk Organic 1L",          "category": "Food & Beverage", "price": 5.99,  "cogs_pct": 0.70, "velocity": 15.0, "trend": "stable",  "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},
    {"sku": "F006", "name": "Whey Protein Powder 2kg",        "category": "Food & Beverage", "price": 79.99, "cogs_pct": 0.66, "velocity": 4.0,  "trend": "stable",  "segment_mix": {"Walk-in": 0.3, "Online": 0.4, "B2B": 0.3}},

    # Home & Garden — low velocity (Dead Weight products)
    {"sku": "H001", "name": "Ceramic Plant Pot Set 3pc",       "category": "Home & Garden", "price": 34.99,  "cogs_pct": 0.55, "velocity": 1.0,  "trend": "dead",     "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},  # dead stock
    {"sku": "H002", "name": "Bamboo Garden Planter Set",       "category": "Home & Garden", "price": 54.99,  "cogs_pct": 0.58, "velocity": 0.8,  "trend": "stable",   "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "H003", "name": "LED Garden String Lights 10m",    "category": "Home & Garden", "price": 29.99,  "cogs_pct": 0.52, "velocity": 1.5,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "H004", "name": "Stainless Steel Watering Can",    "category": "Home & Garden", "price": 44.99,  "cogs_pct": 0.56, "velocity": 0.5,  "trend": "stable",   "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "H005", "name": "Raised Garden Bed Cedar Wood",    "category": "Home & Garden", "price": 89.99,  "cogs_pct": 0.60, "velocity": 0.3,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.4, "B2B": 0.2}},

    # Stationery — steady cash cow behaviour
    {"sku": "S001", "name": "Ballpoint Pen Set 12pc Blue",     "category": "Stationery",    "price": 9.99,   "cogs_pct": 0.30, "velocity": 8.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.2, "B2B": 0.3}},
    {"sku": "S002", "name": "A5 Hardcover Notebook Dotted",    "category": "Stationery",    "price": 19.99,  "cogs_pct": 0.38, "velocity": 5.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "S003", "name": "Highlighter Marker Set 8 Colors", "category": "Stationery",    "price": 12.99,  "cogs_pct": 0.32, "velocity": 6.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.2, "B2B": 0.3}},
    {"sku": "S004", "name": "Sticky Notes Assorted 10 Pads",   "category": "Stationery",    "price": 14.99,  "cogs_pct": 0.34, "velocity": 7.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.2, "B2B": 0.3}},
]

# Products with margin erosion — COGS increases midway through the period
MARGIN_EROSION_SKUS = {"E003", "F006"}  # cogs_pct increases by +0.12 in last 30 days

# Products that go dead after day 60
DEAD_STOCK_SKUS = {"A005", "A012", "H001"}

# Product with demand spike in last 7 days
SPIKE_SKU = "E006"


def _get_password_hash(password: str) -> str:
    """Hash a password using the app's core security module."""
    from app.core.security import hash_password
    return hash_password(password)


def _generate_records(user_id: uuid.UUID, store_id: uuid.UUID) -> list[SaleRecord]:
    """
    Generate 90 days of synthetic sale records.

    Key behaviours:
    - Trend lines applied per product (growing / declining / stable)
    - Weekly seasonality: weekends 1.4x, Mondays 0.7x
    - Month-end spike: last 3 days of each month 1.6x
    - Dead stock: DEAD_STOCK_SKUS get zero sales after day 60
    - Margin erosion: MARGIN_EROSION_SKUS get +12pp COGS in last 30 days
    - Demand spike: SPIKE_SKU gets 4x velocity in last 7 days
    """
    rng = random.Random(42)  # deterministic seed for reproducibility
    today = date.today()
    start_date = today - timedelta(days=90)

    records: list[SaleRecord] = []

    for product in PRODUCTS:
        sku = product["sku"]
        base_velocity = product["velocity"]

        for day_offset in range(90):
            current_date = start_date + timedelta(days=day_offset)

            # Dead stock behaviour
            if sku in DEAD_STOCK_SKUS and day_offset >= 60:
                continue

            # Demand spike (only last 7 days)
            if sku == SPIKE_SKU and day_offset >= 83:
                day_velocity = base_velocity * 4.0
            elif product["trend"] == "growing":
                day_velocity = base_velocity * (1 + day_offset * 0.006)
            elif product["trend"] == "declining":
                day_velocity = base_velocity * (1 - day_offset * 0.004)
            elif product["trend"] == "dead":
                day_velocity = base_velocity if day_offset < 60 else 0
            else:
                day_velocity = base_velocity

            # Seasonality multipliers
            weekday = current_date.weekday()
            if weekday >= 5:  # Saturday / Sunday
                day_velocity *= 1.4
            elif weekday == 0:  # Monday
                day_velocity *= 0.7

            # Month-end spike
            days_in_month = 31  # simplified
            if current_date.day >= days_in_month - 3:
                day_velocity *= 1.6

            if day_velocity <= 0:
                continue

            # Poisson-distributed transaction count for the day
            n_transactions = rng.choices(
                [0, 1, 2, 3, 4],
                weights=[max(0.05, 0.5 - day_velocity * 0.05), 0.35, 0.30, 0.20, 0.10],
            )[0]

            for _ in range(max(1, n_transactions)):
                qty = max(1, rng.randint(1, max(2, int(day_velocity * 1.5))))

                price = product["price"] * rng.uniform(0.97, 1.03)  # slight price variation
                total = round(qty * price, 2)

                # Margin erosion: COGS increases in last 30 days
                cogs_pct = product["cogs_pct"]
                if sku in MARGIN_EROSION_SKUS and day_offset >= 60:
                    cogs_pct = min(0.92, cogs_pct + 0.12)

                cogs = round(qty * price * cogs_pct, 2)
                margin_pct = round(((total - cogs) / total) * 100, 2) if total > 0 else None

                # Segment selection based on product mix
                mix = product["segment_mix"]
                segment = rng.choices(
                    list(mix.keys()), weights=list(mix.values())
                )[0]

                records.append(
                    SaleRecord(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        store_id=store_id,
                        product_name=product["name"],
                        product_sku=sku,
                        product_category=product["category"],
                        quantity_sold=float(qty),
                        unit_price=round(price, 2),
                        total_revenue=total,
                        cogs=cogs,
                        gross_margin=margin_pct,
                        sale_date=current_date,
                        customer_segment=segment,
                        currency="USD",
                        source="demo_seed",
                    )
                )

    return records


def _generate_alerts(user_id: uuid.UUID, store_id: uuid.UUID) -> list[Alert]:
    """Pre-generate deterministic alerts matching the seeded data."""
    today = date.today()
    alerts = [
        # Dead Stock alerts
        Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            store_id=store_id,
            alert_type="dead_stock",
            product_sku="A005",
            product_name="Formal Button-Down Shirt",
            severity="warning",
            payload={
                "last_sale_date": str(today - timedelta(days=30)),
                "days_no_sales": 30,
                "estimated_holding_cost_monthly": 165.00,
                "recommended_action": "Consider a 20-30% clearance discount to move inventory.",
            },
            is_read=False,
        ),
        Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            store_id=store_id,
            alert_type="dead_stock",
            product_sku="A012",
            product_name="Swim Trunks Beach Board",
            severity="warning",
            payload={
                "last_sale_date": str(today - timedelta(days=30)),
                "days_no_sales": 30,
                "estimated_holding_cost_monthly": 99.00,
                "recommended_action": "Bundle with A004 (Running Shorts) for a summer sports pack.",
            },
            is_read=False,
        ),
        Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            store_id=store_id,
            alert_type="dead_stock",
            product_sku="H001",
            product_name="Ceramic Plant Pot Set 3pc",
            severity="warning",
            payload={
                "last_sale_date": str(today - timedelta(days=30)),
                "days_no_sales": 30,
                "estimated_holding_cost_monthly": 105.00,
                "recommended_action": "Mark for clearance. Holding cost exceeds projected revenue at current velocity.",
            },
            is_read=False,
        ),
        # Margin Erosion alerts
        Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            store_id=store_id,
            alert_type="margin_erosion",
            product_sku="E003",
            product_name="Premium Wireless Headphones",
            severity="critical",
            payload={
                "margin_before_pct": 38.0,
                "margin_after_pct": 26.0,
                "margin_drop_pp": 12.0,
                "cogs_increase_per_unit": 24.00,
                "price": 199.99,
                "period_days": 30,
                "recommended_action": "Raise price by $20 or renegotiate supplier COGS to restore margin above 35%.",
            },
            is_read=False,
        ),
        Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            store_id=store_id,
            alert_type="margin_erosion",
            product_sku="F006",
            product_name="Whey Protein Powder 2kg",
            severity="warning",
            payload={
                "margin_before_pct": 34.0,
                "margin_after_pct": 22.0,
                "margin_drop_pp": 12.0,
                "cogs_increase_per_unit": 9.60,
                "price": 79.99,
                "period_days": 30,
                "recommended_action": "Supplier COGS increased. Consider switching to B-grade supplier or adjusting pricing.",
            },
            is_read=False,
        ),
        # Demand Spike alert
        Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            store_id=store_id,
            alert_type="demand_spike",
            product_sku="E006",
            product_name="USB-C Hub 7-in-1",
            severity="info",
            payload={
                "velocity_before": 3.5,
                "velocity_after": 14.0,
                "wow_growth_pct": 300.0,
                "spike_start_date": str(today - timedelta(days=7)),
                "recommended_action": "Reorder immediately. At current velocity, stock will run out in ~5 days.",
            },
            is_read=False,
        ),
    ]
    return alerts


async def seed_for_user(
    user_id: str,
    job_id: str | None = None,
    job_progress: dict | None = None,
) -> None:
    """
    Seed (or re-seed) demo data for a specific user UUID.
    Can be called programmatically from the demo restore endpoint.
    """
    uid = uuid.UUID(user_id)
    sid = DEMO_STORE_ID

    async with async_session_factory() as db:
        # Clear existing data
        await db.execute(delete(SaleRecord).where(SaleRecord.user_id == uid))
        await db.execute(delete(Alert).where(Alert.user_id == uid))
        await db.execute(delete(MLResult).where(MLResult.user_id == uid))
        await db.commit()

        # Insert records in batches
        records = _generate_records(uid, sid)
        batch_size = 500
        for i in range(0, len(records), batch_size):
            db.add_all(records[i : i + batch_size])
            await db.commit()

        # Insert alerts
        alerts = _generate_alerts(uid, sid)
        db.add_all(alerts)
        await db.commit()

        print(f"✓ Seeded {len(records)} sale records and {len(alerts)} alerts for user {uid}")


async def seed_demo_data(force: bool = False) -> None:
    """Main seed function — creates demo user/store if needed, then seeds data."""
    async with async_session_factory() as db:
        # ── 1. Ensure demo user exists with fixed UUID ─────────────────────────
        result = await db.execute(select(User).where(User.id == DEMO_USER_ID))
        user = result.scalars().first()

        if not user:
            print("Creating demo user...")
            user = User(
                id=DEMO_USER_ID,
                email=DEMO_EMAIL,
                password=_get_password_hash(DEMO_PASSWORD),
                full_name="Demo Store",
                store_name="RetailMind Demo Store",
                currency="USD",
                timezone="America/New_York",
                is_onboarded=True,
                plan="pro",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"  ✓ Created demo user: {DEMO_EMAIL} (id={DEMO_USER_ID})")
        else:
            print(f"  Demo user already exists: {DEMO_EMAIL}")

        # ── 2. Ensure demo store exists with fixed UUID ────────────────────────
        result = await db.execute(select(Store).where(Store.id == DEMO_STORE_ID))
        store = result.scalars().first()

        if not store:
            print("Creating demo store...")
            store = Store(
                id=DEMO_STORE_ID,
                user_id=DEMO_USER_ID,
                name="RetailMind Demo Store",
                location="New York, USA",
                currency="USD",
                timezone="America/New_York",
                is_active=True,
            )
            db.add(store)
            await db.commit()
            print(f"  ✓ Created demo store (id={DEMO_STORE_ID})")
        else:
            print(f"  Demo store already exists.")

        # ── 3. Check if already seeded ─────────────────────────────────────────
        if not force:
            from sqlalchemy import func
            count_result = await db.execute(
                select(func.count()).select_from(SaleRecord).where(
                    SaleRecord.user_id == DEMO_USER_ID
                )
            )
            count = count_result.scalar()
            if count and count > 0:
                print(f"  Demo data already seeded ({count} records). Use --force to re-seed.")
                return

        # ── 4. Seed records and alerts ─────────────────────────────────────────
        print("Seeding 90-day synthetic dataset...")
        await seed_for_user(str(DEMO_USER_ID))

    print("\n✅ Demo account ready!")
    print(f"   Email:    {DEMO_EMAIL}")
    print(f"   Password: {DEMO_PASSWORD}")
    print(f"   User ID:  {DEMO_USER_ID}")
    print(f"   Store ID: {DEMO_STORE_ID}")
    print("   Set DEMO_MODE=true in .env to bypass authentication entirely.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed RetailMind demo account")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-seed even if demo data already exists",
    )
    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(seed_demo_data(force=args.force))
