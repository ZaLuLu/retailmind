import asyncio
from sqlalchemy import text
from app.core.db import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT email, is_onboarded, store_name, currency FROM users WHERE email='rahul@retailmind.com'")
        )
        row = result.fetchone()
        if row:
            print(f"User: {row.email} | onboarded={row.is_onboarded} | store={row.store_name} | currency={row.currency}")
        else:
            print("User NOT found in DB")

        r2 = await conn.execute(
            text("SELECT COUNT(*) FROM sale_records sr JOIN users u ON sr.user_id=u.id WHERE u.email='rahul@retailmind.com'")
        )
        count = r2.scalar()
        print(f"Sale records: {count}")

asyncio.run(check())
