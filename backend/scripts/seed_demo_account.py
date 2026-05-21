import asyncio
import os
import sys
import pandas as pd
from datetime import datetime

# Adjust Python path to load backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import async_session_factory
from app.models.db import User, Store, SaleRecord
from app.security.auth import get_password_hash

async def seed_demo_data():
    demo_email = "demo@retailmind.com"
    demo_pass = "demo123"
    excel_path = r"D:\CODING\documind\Demo_data\demo_retail_data.xlsx"

    print(f"Reading data from {excel_path}...")
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} rows.")

    async with async_session_factory() as db:
        from sqlalchemy.future import select
        
        # 1. Create or get Demo User
        result = await db.execute(select(User).where(User.email == demo_email))
        user = result.scalars().first()
        if not user:
            print("Creating demo user...")
            user = User(
                email=demo_email,
                password=get_password_hash(demo_pass),
                full_name="Demo Admin",
                store_name="RetailMind Demo Store",
                currency="USD",
                is_onboarded=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            print("Demo user already exists.")

        # 2. Create or get Demo Store
        result = await db.execute(select(Store).where(Store.user_id == user.id))
        store = result.scalars().first()
        if not store:
            print("Creating demo store...")
            store = Store(
                user_id=user.id,
                name="RetailMind Demo Store",
                location="Virtual"
            )
            db.add(store)
            await db.commit()
            await db.refresh(store)
        else:
            print("Demo store already exists.")
            
        # 3. Clean up existing sale records for this user (reset)
        print("Clearing existing sales data for demo user...")
        from sqlalchemy import delete
        await db.execute(delete(SaleRecord).where(SaleRecord.user_id == user.id))
        await db.commit()

        # 4. Insert data
        print("Inserting sales data...")
        records = []
        for _, row in df.iterrows():
            qty = float(row['qty_sold'])
            unit_price = float(row['unit_price'])
            unit_cost = float(row.get('unit_cost', 0))
            total_revenue = qty * unit_price
            cogs = unit_cost * qty if unit_cost else 0
            margin = None
            if total_revenue > 0 and cogs > 0:
                margin = round(((total_revenue - cogs) / total_revenue) * 100, 2)
            
            # Parse date string
            sale_date = datetime.strptime(str(row['date'])[:10], "%Y-%m-%d").date()

            record = SaleRecord(
                user_id=user.id,
                store_id=store.id,
                product_name=str(row['product_name']),
                product_sku=str(row.get('product_id', '')),
                product_category=str(row.get('category', 'Other')),
                quantity_sold=qty,
                unit_price=unit_price,
                total_revenue=total_revenue,
                cogs=cogs,
                gross_margin=margin,
                sale_date=sale_date,
                customer_segment=str(row.get('customer_segment', '')),
                currency="USD",
                source="demo_seed"
            )
            records.append(record)

        # Batch insert
        batch_size = 500
        for i in range(0, len(records), batch_size):
            db.add_all(records[i:i+batch_size])
            await db.commit()
            print(f"Inserted {min(i+batch_size, len(records))} / {len(records)}")

        print("Successfully seeded demo account!")
        print(f"Login: {demo_email}")
        print(f"Password: {demo_pass}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_demo_data())
