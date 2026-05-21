import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.db import Base

async def reset_db():
    # asyncpg needs ssl=True or ssl='require' for Neon
    db_url = settings.DATABASE_URL.split("?")[0]
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_db())
