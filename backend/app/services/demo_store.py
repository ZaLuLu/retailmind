import uuid
import random
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Tuple, List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.redis import cache
from ..core.security import hash_password
from ..models.db import User, Store, SaleRecord, Alert, MLResult

logger = logging.getLogger(__name__)

# ── Product catalogue for rich seeding ─────────────────────────────────────────
PRODUCTS: List[Dict[str, Any]] = [
    {"sku": "E001", "name": "Wireless Bluetooth Headphones",   "category": "Electronics",   "price": 129.99, "cogs_pct": 0.56, "velocity": 3.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.3, "Online": 0.5, "B2B": 0.2}},
    {"sku": "E002", "name": "USB-C Fast Charger 65W",          "category": "Electronics",   "price": 39.99,  "cogs_pct": 0.40, "velocity": 5.0,  "trend": "growing",  "segment_mix": {"Walk-in": 0.4, "Online": 0.5, "B2B": 0.1}},
    {"sku": "E003", "name": "Premium Wireless Headphones",     "category": "Electronics",   "price": 199.99, "cogs_pct": 0.62, "velocity": 1.5,  "trend": "stable",   "segment_mix": {"Walk-in": 0.2, "Online": 0.4, "B2B": 0.4}},
    {"sku": "E004", "name": "Smart Watch Fitness Tracker",     "category": "Electronics",   "price": 89.99,  "cogs_pct": 0.50, "velocity": 2.5,  "trend": "growing",  "segment_mix": {"Walk-in": 0.3, "Online": 0.6, "B2B": 0.1}},
    {"sku": "E005", "name": "Portable Bluetooth Speaker",      "category": "Electronics",   "price": 59.99,  "cogs_pct": 0.52, "velocity": 2.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.5, "B2B": 0.1}},
    {"sku": "E006", "name": "USB-C Hub 7-in-1",               "category": "Electronics",   "price": 49.99,  "cogs_pct": 0.45, "velocity": 3.5,  "trend": "spike",    "segment_mix": {"Walk-in": 0.3, "Online": 0.5, "B2B": 0.2}},
    {"sku": "E007", "name": "Wireless Charging Pad 15W",      "category": "Electronics",   "price": 34.99,  "cogs_pct": 0.48, "velocity": 2.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.4, "B2B": 0.2}},
    {"sku": "E008", "name": "Mechanical Keyboard RGB",         "category": "Electronics",   "price": 149.99, "cogs_pct": 0.55, "velocity": 1.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.2, "Online": 0.5, "B2B": 0.3}},
    {"sku": "A001", "name": "Classic White T-Shirt",           "category": "Apparel",       "price": 24.99,  "cogs_pct": 0.45, "velocity": 8.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "A002", "name": "Slim Fit Denim Jeans",            "category": "Apparel",       "price": 59.99,  "cogs_pct": 0.50, "velocity": 4.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A003", "name": "Casual Hoodie Pullover",          "category": "Apparel",       "price": 44.99,  "cogs_pct": 0.48, "velocity": 5.0,  "trend": "growing",  "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A004", "name": "Running Shorts Athletic",         "category": "Apparel",       "price": 29.99,  "cogs_pct": 0.42, "velocity": 6.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A005", "name": "Formal Button-Down Shirt",        "category": "Apparel",       "price": 54.99,  "cogs_pct": 0.46, "velocity": 3.0,  "trend": "dead",     "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "A006", "name": "Winter Puffer Jacket",            "category": "Apparel",       "price": 99.99,  "cogs_pct": 0.55, "velocity": 2.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.4, "B2B": 0.2}},
    {"sku": "A007", "name": "Yoga Leggings High-Waist",        "category": "Apparel",       "price": 39.99,  "cogs_pct": 0.44, "velocity": 5.0,  "trend": "growing",  "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A008", "name": "Polo Shirt Classic Fit",          "category": "Apparel",       "price": 34.99,  "cogs_pct": 0.43, "velocity": 4.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "A009", "name": "Cargo Shorts Multi-Pocket",       "category": "Apparel",       "price": 44.99,  "cogs_pct": 0.46, "velocity": 3.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "A010", "name": "Summer Floral Dress",             "category": "Apparel",       "price": 49.99,  "cogs_pct": 0.47, "velocity": 3.5,  "trend": "growing",  "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "A011", "name": "Compression Socks Athletic",      "category": "Apparel",       "price": 14.99,  "cogs_pct": 0.35, "velocity": 7.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "A012", "name": "Swim Trunks Beach Board",         "category": "Apparel",       "price": 32.99,  "cogs_pct": 0.44, "velocity": 2.0,  "trend": "dead",     "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "F001", "name": "Premium Ground Coffee 500g",      "category": "Food & Beverage", "price": 18.99, "cogs_pct": 0.65, "velocity": 12.0, "trend": "stable",  "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},
    {"sku": "F002", "name": "Protein Bar Variety Pack 12ct",   "category": "Food & Beverage", "price": 29.99, "cogs_pct": 0.62, "velocity": 9.0,  "trend": "growing", "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "F003", "name": "Green Tea Premium 100 Bags",      "category": "Food & Beverage", "price": 14.99, "cogs_pct": 0.60, "velocity": 10.0, "trend": "stable",  "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},
    {"sku": "F004", "name": "Energy Drink 24-Pack",            "category": "Food & Beverage", "price": 49.99, "cogs_pct": 0.68, "velocity": 6.0,  "trend": "growing", "segment_mix": {"Walk-in": 0.4, "Online": 0.3, "B2B": 0.3}},
    {"sku": "F005", "name": "Almond Milk Organic 1L",          "category": "Food & Beverage", "price": 5.99,  "cogs_pct": 0.70, "velocity": 15.0, "trend": "stable",  "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},
    {"sku": "F006", "name": "Whey Protein Powder 2kg",        "category": "Food & Beverage", "price": 79.99, "cogs_pct": 0.66, "velocity": 4.0,  "trend": "stable",  "segment_mix": {"Walk-in": 0.3, "Online": 0.4, "B2B": 0.3}},
    {"sku": "H001", "name": "Ceramic Plant Pot Set 3pc",       "category": "Home & Garden", "price": 34.99,  "cogs_pct": 0.55, "velocity": 1.0,  "trend": "dead",     "segment_mix": {"Walk-in": 0.7, "Online": 0.2, "B2B": 0.1}},
    {"sku": "H002", "name": "Bamboo Garden Planter Set",       "category": "Home & Garden", "price": 54.99,  "cogs_pct": 0.58, "velocity": 0.8,  "trend": "stable",   "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "H003", "name": "LED Garden String Lights 10m",    "category": "Home & Garden", "price": 29.99,  "cogs_pct": 0.52, "velocity": 1.5,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.4, "B2B": 0.1}},
    {"sku": "H004", "name": "Stainless Steel Watering Can",    "category": "Home & Garden", "price": 44.99,  "cogs_pct": 0.56, "velocity": 0.5,  "trend": "stable",   "segment_mix": {"Walk-in": 0.6, "Online": 0.3, "B2B": 0.1}},
    {"sku": "H005", "name": "Raised Garden Bed Cedar Wood",    "category": "Home & Garden", "price": 89.99,  "cogs_pct": 0.60, "velocity": 0.3,  "trend": "stable",   "segment_mix": {"Walk-in": 0.4, "Online": 0.4, "B2B": 0.2}},
    {"sku": "S001", "name": "Ballpoint Pen Set 12pc Blue",     "category": "Stationery",    "price": 9.99,   "cogs_pct": 0.30, "velocity": 8.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.2, "B2B": 0.3}},
    {"sku": "S002", "name": "A5 Hardcover Notebook Dotted",    "category": "Stationery",    "price": 19.99,  "cogs_pct": 0.38, "velocity": 5.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.3, "B2B": 0.2}},
    {"sku": "S003", "name": "Highlighter Marker Set 8 Colors", "category": "Stationery",    "price": 12.99,  "cogs_pct": 0.32, "velocity": 6.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.2, "B2B": 0.3}},
    {"sku": "S004", "name": "Sticky Notes Assorted 10 Pads",   "category": "Stationery",    "price": 14.99,  "cogs_pct": 0.34, "velocity": 7.0,  "trend": "stable",   "segment_mix": {"Walk-in": 0.5, "Online": 0.2, "B2B": 0.3}},
]

MARGIN_EROSION_SKUS = {"E003", "F006"}
DEAD_STOCK_SKUS = {"A005", "A012", "H001"}
SPIKE_SKU = "E006"

def _generate_records(user_id: uuid.UUID, store_id: uuid.UUID) -> List[SaleRecord]:
    rng = random.Random(42)
    today = date.today()
    start_date = today - timedelta(days=90)
    records: List[SaleRecord] = []

    for product in PRODUCTS:
        sku = product["sku"]
        base_velocity = product["velocity"]

        for day_offset in range(90):
            current_date = start_date + timedelta(days=day_offset)

            if sku in DEAD_STOCK_SKUS and day_offset >= 60:
                continue

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

            weekday = current_date.weekday()
            if weekday >= 5:
                day_velocity *= 1.4
            elif weekday == 0:
                day_velocity *= 0.7

            days_in_month = 31
            if current_date.day >= days_in_month - 3:
                day_velocity *= 1.6

            if day_velocity <= 0:
                continue

            n_transactions = rng.choices(
                [0, 1, 2, 3, 4],
                weights=[max(0.05, 0.5 - day_velocity * 0.05), 0.35, 0.30, 0.20, 0.10],
            )[0]

            for _ in range(max(1, n_transactions)):
                qty = max(1, rng.randint(1, max(2, int(day_velocity * 1.5))))
                price = product["price"] * rng.uniform(0.97, 1.03)
                total = round(qty * price, 2)

                cogs_pct = product["cogs_pct"]
                if sku in MARGIN_EROSION_SKUS and day_offset >= 60:
                    cogs_pct = min(0.92, cogs_pct + 0.12)

                cogs = round(qty * price * cogs_pct, 2)
                margin_pct = round(((total - cogs) / total) * 100, 2) if total > 0 else None

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
                        unit_price=Decimal(str(round(price, 2))),
                        total_revenue=Decimal(str(total)),
                        cogs=Decimal(str(cogs)),
                        gross_margin=Decimal(str(margin_pct)) if margin_pct is not None else None,
                        sale_date=current_date,
                        customer_segment=segment,
                        currency="USD",
                        source="demo_seed",
                    )
                )
    return records

def _generate_alerts(user_id: uuid.UUID, store_id: uuid.UUID) -> List[Alert]:
    today = date.today()
    return [
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
                "recommended_action": "Supplier COGS increased. Consider adjusting pricing or changing suppliers.",
            },
            is_read=False,
        ),
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

class DemoSessionStore:
    """
    Manages isolated demo visitor sessions.
    Uses Redis to track session TTLs and clean up PostgreSQL temp users automatically.
    """

    @staticmethod
    async def create_session(db: AsyncSession) -> Tuple[str, User]:
        """
        Creates a unique ephemeral user & store in PostgreSQL,
        seeds the rich 90-day dataset, and registers the session in Redis.
        """
        demo_session_id = str(uuid.uuid4())
        
        # 1. Ephemeral user and store
        user_id = uuid.uuid4()
        store_id = uuid.uuid4()
        
        email = f"demo_session_{demo_session_id}@retailmind.com"
        
        user = User(
            id=user_id,
            email=email,
            password=hash_password(f"demo_pass_{demo_session_id}"),
            full_name="Guest Demo User",
            store_name="RetailMind Demo Store",
            currency="USD",
            timezone="UTC",
            is_onboarded=True,
            plan="pro",
        )
        
        store = Store(
            id=store_id,
            user_id=user_id,
            name="RetailMind Demo Store",
            location="Demo Location",
            currency="USD",
            timezone="UTC",
            is_active=True,
        )
        
        db.add(user)
        db.add(store)
        await db.commit()
        
        # 2. Seed data
        records = _generate_records(user_id, store_id)
        batch_size = 500
        for i in range(0, len(records), batch_size):
            db.add_all(records[i : i + batch_size])
            await db.commit()
            
        alerts = _generate_alerts(user_id, store_id)
        db.add_all(alerts)
        await db.commit()
        
        # 3. Store session ID mapping in Redis with 2-hour TTL (7200 seconds)
        # Note: If Redis is down, it falls back to in-memory, which is handled inside CacheClient.
        await cache.set(f"demo_session:{demo_session_id}", str(user_id), ex=7200)
        
        logger.info(f"Created demo session {demo_session_id} for ephemeral user {user_id}")
        return demo_session_id, user

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession):
        """
        Finds all ephemeral users and deletes them if their session key has expired in Redis.
        Also acts as a fallback for database cleanup (users older than 12 hours are deleted anyway).
        """
        # Select all ephemeral users
        stmt = select(User).where(User.email.like("demo_session_%@retailmind.com"))
        res = await db.execute(stmt)
        ephemeral_users = res.scalars().all()
        
        deleted_count = 0
        now = datetime.now(timezone.utc)
        
        for user in ephemeral_users:
            # Extract demo_session_id from email
            try:
                # Format: demo_session_{demo_session_id}@retailmind.com
                email_part = user.email.split("@")[0]
                session_id = email_part.replace("demo_session_", "")
            except Exception:
                continue
                
            # Check if active in Redis
            is_active = await cache.get(f"demo_session:{session_id}")
            
            # Delete if not active in Redis, or fallback: if created > 12 hours ago
            should_delete = False
            if not is_active:
                should_delete = True
            elif user.created_at:
                # Make user.created_at timezone-aware if needed
                created_at = user.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if now - created_at > timedelta(hours=12):
                    should_delete = True
                    
            if should_delete:
                logger.info(f"Cleaning up expired demo session user: {user.id} ({user.email})")
                await db.delete(user)
                deleted_count += 1
                
        if deleted_count > 0:
            await db.commit()
            logger.info(f"Cleaned up {deleted_count} expired demo sessions.")
