from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# asyncpg compatibility: strip query params (like sslmode) that it doesn't support as kwargs
db_url = settings.DATABASE_URL
connect_args = {}
if "sslmode=require" in db_url:
    connect_args["ssl"] = True
    # Strip the parameter to avoid SQLAlchemy passing it as a kwarg
    db_url = db_url.replace("sslmode=require", "").replace("??", "?").rstrip("?")

engine = create_async_engine(
    db_url,
    echo=True if settings.ENVIRONMENT == "development" else False,
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
