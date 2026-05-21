"""
RetailMind Demo Seeder
======================
Seeds the demo account with 220+ realistic retail sale records across 5 categories,
spanning 6 months. Includes:
  - Intentional margin-erosion products (low-cost generics)
  - Dead-stock scenarios (products with no recent sales)
  - Demand-spike products (summer/seasonal items)

Run: python seed_demo.py  (from the backend/ directory)
"""

import asyncio
import random
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from app.core.config import settings
from app.models.db import User, SaleRecord, Transaction
from app.security.auth import get_password_hash

# ── DB setup ─────────────────────────────────────────────────────────────────
db_url = settings.DATABASE_URL
connect_args = {}
if "sslmode=require" in db_url:
    connect_args["ssl"] = True
    db_url = db_url.replace("sslmode=require", "")

engine = create_async_engine(db_url, echo=False, connect_args=connect_args)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Product catalogue ─────────────────────────────────────────────────────────
PRODUCTS = {
    "Electronics": [
        {"name": "Sony WH-1000XM5 Headphones", "sku": "SONY-XM5", "unit_price": 19990, "cogs_pct": 0.55},
        {"name": "boAt Airdopes 141",            "sku": "BOAT-141",  "unit_price": 1299,  "cogs_pct": 0.52},
        {"name": "Realme Buds Air 5",            "sku": "RLME-BA5",  "unit_price": 2999,  "cogs_pct": 0.54},
        {"name": "Portronics Mport USB Hub",     "sku": "PORT-HUB",  "unit_price": 899,   "cogs_pct": 0.58},
        {"name": "Generic USB-C Cable 1m",       "sku": "USB-C-1M",  "unit_price": 199,   "cogs_pct": 0.87},  # margin erosion
        {"name": "Anker 65W GaN Charger",        "sku": "ANK-GAN65", "unit_price": 2499,  "cogs_pct": 0.56},
    ],
    "Apparel": [
        {"name": "Levi's 501 Slim Jeans",        "sku": "LEV-501",   "unit_price": 3499,  "cogs_pct": 0.50},
        {"name": "Allen Solly Oxford Shirt",     "sku": "AS-OXF",    "unit_price": 1799,  "cogs_pct": 0.48},
        {"name": "Puma Softride Sneakers",       "sku": "PUM-SOFT",  "unit_price": 4999,  "cogs_pct": 0.55},
        {"name": "Zara Linen Blend Tee",         "sku": "ZAR-LIN",   "unit_price": 1299,  "cogs_pct": 0.49},
        {"name": "Nike Dri-FIT Running Shorts",  "sku": "NIK-DRF",   "unit_price": 1999,  "cogs_pct": 0.53},
        {"name": "Roadster Logo Hoodie",         "sku": "RD-HOOD",   "unit_price": 999,   "cogs_pct": 0.60},  # margin erosion
    ],
    "Groceries": [
        {"name": "Tata Salt 1kg Pack",           "sku": "TAT-SALT",  "unit_price": 30,    "cogs_pct": 0.75},
        {"name": "Aashirvaad Atta 5kg",          "sku": "AATA-5KG",  "unit_price": 265,   "cogs_pct": 0.72},
        {"name": "Amul Gold Full-Cream Milk 1L", "sku": "AMUL-MILK", "unit_price": 66,    "cogs_pct": 0.80},  # margin erosion
        {"name": "Fortune Sunflower Oil 1L",     "sku": "FORT-OIL",  "unit_price": 155,   "cogs_pct": 0.74},
        {"name": "Haldiram's Bhujia 400g",       "sku": "HAL-BHU",   "unit_price": 115,   "cogs_pct": 0.66},
        {"name": "Nescafé Classic 200g",         "sku": "NES-200",   "unit_price": 415,   "cogs_pct": 0.68},
    ],
    "Home & Kitchen": [
        {"name": "Milton Insulated Lunch Box",   "sku": "MLT-LBX",   "unit_price": 599,   "cogs_pct": 0.55},
        {"name": "Prestige Induction Cooktop",   "sku": "PRE-INDC",  "unit_price": 1999,  "cogs_pct": 0.58},
        {"name": "Cello Opalware Dinner Set",    "sku": "CEL-DIN",   "unit_price": 999,   "cogs_pct": 0.56},
        {"name": "Bajaj Mixer Grinder 500W",     "sku": "BAJ-MG5",   "unit_price": 2799,  "cogs_pct": 0.57},
        {"name": "Tupperware Modular Bowl 1L",   "sku": "TUP-MOD",   "unit_price": 349,   "cogs_pct": 0.54},
        # Dead-stock candidate — we'll stop seeding this after month 2
        {"name": "Nokia 3310 Phone Stand",       "sku": "NOK-STD",   "unit_price": 249,   "cogs_pct": 0.79},
    ],
    "Beauty": [
        {"name": "Nivea Soft Moisturising Cream", "sku": "NIV-SOFT", "unit_price": 299,   "cogs_pct": 0.52},
        {"name": "L'Oréal Revitalift Serum",     "sku": "LOR-REV",   "unit_price": 999,   "cogs_pct": 0.55},
        {"name": "Mamaearth Vitamin C Face Wash", "sku": "MAM-VCW",  "unit_price": 249,   "cogs_pct": 0.51},
        {"name": "Biotique Bio Aloe Vera Gel",   "sku": "BIO-ALG",   "unit_price": 199,   "cogs_pct": 0.53},
        {"name": "Lakme 9-to-5 Lipstick",        "sku": "LAK-LIP",   "unit_price": 399,   "cogs_pct": 0.49},
        # Seasonal spike product (summertime sunscreen demand)
        {"name": "Neutrogena Ultra Sheer SPF 50+","sku": "NEU-SPF",  "unit_price": 549,   "cogs_pct": 0.54},
    ],
}

SEGMENTS = ["Walk-in", "Online", "B2B"]
SEGMENT_WEIGHTS = [50, 35, 15]


def _compute_margin(unit_price: float, cogs_pct: float, qty: float) -> tuple[float, float]:
    """Returns (total_cogs, gross_margin_pct)."""
    cogs_per_unit = unit_price * cogs_pct
    total_cogs = cogs_per_unit * qty
    total_revenue = unit_price * qty
    margin_pct = round(((total_revenue - total_cogs) / total_revenue) * 100, 2)
    return total_cogs, margin_pct


def generate_sale_records(user_id, today: date) -> list[SaleRecord]:
    records = []
    start_date = today - timedelta(days=180)

    for category, products in PRODUCTS.items():
        for product in products:
            name = product["name"]
            sku = product["sku"]
            unit_price = product["unit_price"]
            cogs_pct = product["cogs_pct"]

            # Determine how many sale events this product gets
            # High-volume vs niche products
            if category == "Groceries":
                base_events = random.randint(25, 40)
            elif category == "Electronics":
                base_events = random.randint(10, 18)
            elif category == "Beauty":
                base_events = random.randint(15, 25)
            else:
                base_events = random.randint(8, 15)

            # Special cases
            is_dead_stock = (sku == "NOK-STD")
            is_spike_product = (sku == "NEU-SPF")  # demand spike in last 7 days

            # Generate random sale dates in window
            dates_pool = [start_date + timedelta(days=d) for d in range(181)]

            if is_dead_stock:
                # Sales only in months 1-3 (stop 90+ days ago)
                cutoff = today - timedelta(days=91)
                dates_pool = [d for d in dates_pool if d <= cutoff]

            elif is_spike_product:
                # Spike product: normal sales early, then heavy sales in last 7 days
                early_pool = [d for d in dates_pool if d < today - timedelta(days=7)]
                spike_pool = [today - timedelta(days=i) for i in range(7)]
                # ~4 early events
                selected_dates = random.sample(early_pool, min(4, len(early_pool)))
                # ~8 spike events
                selected_dates += [random.choice(spike_pool) for _ in range(8)]
                selected_dates.sort()
            else:
                selected_dates = sorted(random.sample(dates_pool, min(base_events, len(dates_pool))))

            if not is_spike_product:
                selected_dates = sorted(random.sample(dates_pool, min(base_events, len(dates_pool))))

            for sale_date in selected_dates:
                # Quantity varies by category
                if category == "Groceries":
                    qty = random.randint(5, 30)
                elif category == "Electronics":
                    qty = random.randint(1, 5)
                elif category == "Beauty":
                    qty = random.randint(2, 10)
                else:
                    qty = random.randint(1, 8)

                # Apply small price variance (± 5%) to simulate real retail
                price = round(unit_price * random.uniform(0.97, 1.03), 2)
                total_revenue = round(price * qty, 2)
                total_cogs, margin_pct = _compute_margin(price, cogs_pct, qty)
                segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]

                records.append(
                    SaleRecord(
                        user_id=user_id,
                        product_name=name,
                        product_sku=sku,
                        product_category=category,
                        quantity_sold=qty,
                        unit_price=price,
                        total_revenue=total_revenue,
                        cogs=round(total_cogs, 2),
                        gross_margin=margin_pct,
                        sale_date=sale_date,
                        customer_segment=segment,
                        currency="INR",
                        source="demo_seed",
                    )
                )

    # Sort newest first
    records.sort(key=lambda r: r.sale_date, reverse=True)
    return records


async def seed():
    async with AsyncSessionLocal() as db:
        demo_email = "rahul@retailmind.com"
        demo_password = "password123"
        today = date.today()

        print(f"Checking for demo user: {demo_email}")
        result = await db.execute(select(User).where(User.email == demo_email))
        user = result.scalars().first()

        if not user:
            print("Creating demo user...")
            user = User(
                email=demo_email,
                password=get_password_hash(demo_password),
                full_name="Rahul Sharma",
                store_name="Sharma Retail & Co.",
                initial_balance=0.0,
                is_onboarded=True,
                currency="INR",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            print("Demo user found.")

        # Clear old retail records
        print("Clearing old sale records for demo user...")
        await db.execute(delete(SaleRecord).where(SaleRecord.user_id == user.id))
        await db.commit()

        print("Generating RetailMind demo dataset (~220+ sale records)...")
        records = generate_sale_records(user.id, today)

        print(f"Inserting {len(records)} sale records...")
        batch_size = 100
        for i in range(0, len(records), batch_size):
            db.add_all(records[i : i + batch_size])
            await db.commit()

        print(f"\n[OK] Done! {len(records)} records seeded.")
        print(f"   Demo login:  {demo_email} / {demo_password}")
        print(f"   Categories:  {', '.join(PRODUCTS.keys())}")
        print("   Dead stock:  Nokia 3310 Phone Stand (no sales for 90+ days)")
        print("   Spike:       Neutrogena SPF (8 sales in last 7 days)")
        print("   Margin erode: Generic USB-C Cable, Amul Milk, Nokia Stand\n")


if __name__ == "__main__":
    asyncio.run(seed())
