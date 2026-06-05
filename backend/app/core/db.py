from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

import re

# asyncpg compatibility: strip sslmode param (not supported as a query kwarg)
# and pass ssl=True via connect_args instead
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

connect_args = {}
if "sslmode=require" in db_url:
    connect_args["ssl"] = True
    # Remove sslmode=require (handles ?, &, trailing ? cleanup)
    db_url = re.sub(r"[?&]sslmode=require", "", db_url)
    db_url = re.sub(r"\?&", "?", db_url)
    db_url = db_url.rstrip("?")

engine = create_async_engine(
    db_url,
    echo=True if settings.ENVIRONMENT == "development" else False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args=connect_args
)

async_session_factory = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session_factory() as session:
        yield session
