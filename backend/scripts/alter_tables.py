import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

async def alter_tables():
    db_url = settings.DATABASE_URL.split("?")[0]
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        print("Altering sale_records to add upload_id column if it doesn't exist...")
        # Check if column exists first or use PostgreSQL safe syntax
        await conn.execute(text(
            "ALTER TABLE sale_records ADD COLUMN IF NOT EXISTS upload_id UUID REFERENCES upload_history(id) ON DELETE SET NULL;"
        ))
    
    print("Database table alteration complete!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(alter_tables())
