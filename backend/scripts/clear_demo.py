import asyncio
import os
import sys
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.db import User
from app.core.db import async_session_factory

async def clear_demo():
    async with async_session_factory() as db:
        # Delete user demo@retailmind.com to resolve unique constraint conflict
        await db.execute(delete(User).where(User.email == "demo@retailmind.com"))
        await db.commit()
        print("Cleared demo user from database.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(clear_demo())
