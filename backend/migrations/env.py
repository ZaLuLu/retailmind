import asyncio
import sys
import re
from os.path import abspath, dirname
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Insert the parent path (backend root) to python path
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from app.core.config import settings
from app.core.db import Base
# Make sure all models are imported so their metadata is registered on Base
from app.models import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Dynamically set the database URL in the alembic config (strip sslmode parameter if present)
db_url = settings.DATABASE_URL

# Ensure we use the asyncpg driver (Railway/Postgres URLs often come as postgres:// or postgresql://)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url  # already correct

connect_args = {}
if "sslmode=require" in db_url:
    connect_args["ssl"] = True
    # Remove sslmode=require (handles ?, &, trailing ? cleanup)
    db_url = re.sub(r"[?&]sslmode=require", "", db_url)
    db_url = re.sub(r"\?&", "?", db_url)
    db_url = db_url.rstrip("?")

config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

