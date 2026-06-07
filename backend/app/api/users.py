import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.db import get_db
from pydantic import BaseModel, field_validator
from typing import Optional
from ..models.db import User
from ..api.deps import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])

ALLOWED_CURRENCIES = {"INR", "USD", "EUR", "GBP", "AED", "SGD", "JPY"}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    initial_balance: Optional[float] = None
    store_name: Optional[str] = None
    currency: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) > 255:
                raise ValueError("Full name must be 255 characters or fewer")
        return v

    @field_validator("store_name")
    @classmethod
    def validate_store_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) > 255:
                raise ValueError("Store name must be 255 characters or fewer")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.upper().strip()
            if v not in ALLOWED_CURRENCIES:
                raise ValueError(f"Currency must be one of: {', '.join(sorted(ALLOWED_CURRENCIES))}")
        return v

    @field_validator("initial_balance")
    @classmethod
    def validate_balance(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Initial balance cannot be negative")
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    store_name: Optional[str]
    initial_balance: float
    is_onboarded: bool
    currency: Optional[str] = "INR"
    plan: str = "free"
    is_demo: bool = False

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.initial_balance is not None:
        current_user.initial_balance = request.initial_balance
    if request.store_name is not None:
        current_user.store_name = request.store_name
    if request.currency is not None:
        current_user.currency = request.currency

    try:
        await db.commit()
        await db.refresh(current_user)
        from ..core.redis import cache
        await cache.invalidate_chart_bundle(current_user.id)
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to update user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings. Please try again."
        )

    return current_user
