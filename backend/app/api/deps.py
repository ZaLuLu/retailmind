from __future__ import annotations

import uuid
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..core.config import settings
from ..core.db import get_db
from ..core.security import decode_token
from ..models.db import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    # In demo mode, the token is optional — FastAPI won't reject missing auth headers
    auto_error=not settings.DEMO_MODE,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that returns the currently authenticated user.

    In demo mode (DEMO_MODE=true):
        If a valid JWT token is provided, validates it and returns the user.
        Otherwise, falls back to returning the seeded demo user directly.

    In production mode:
        Validates the JWT, extracts user_id, and fetches from DB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Attempt standard JWT validation if token is present ─────────────────
    if token:
        payload = decode_token(token)
        if payload is not None:
            user_id_str: str | None = payload.get("sub")
            if user_id_str is not None:
                try:
                    user_id = uuid.UUID(user_id_str)
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalars().first()
                    if user is not None:
                        return user
                except ValueError:
                    pass

    # ── Demo Mode fallback ──────────────────────────────────────────────────
    if settings.DEMO_MODE:
        try:
            demo_uuid = uuid.UUID(settings.DEMO_USER_ID)
        except ValueError:
            logger.error("DEMO_USER_ID is not a valid UUID: %s", settings.DEMO_USER_ID)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Demo mode misconfigured: invalid DEMO_USER_ID",
            )

        result = await db.execute(select(User).where(User.id == demo_uuid))
        demo_user = result.scalars().first()

        if demo_user is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Demo data not seeded. "
                    "Run: python backend/scripts/seed_demo_account.py"
                ),
            )
        return demo_user

    raise credentials_exception
