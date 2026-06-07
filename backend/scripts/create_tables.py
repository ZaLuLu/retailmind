import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.db import Base

async def create_tables():
    # asyncpg needs ssl=True or ssl='require' for Neon
    db_url = settings.DATABASE_URL.split("?")[0]
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        print("Creating any missing tables (including audits and upload_history)...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database table checks and creation complete!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_tables())
