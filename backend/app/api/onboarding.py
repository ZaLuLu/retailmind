from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.db import get_db
from ..models.db import User, Store
from ..api.deps import get_current_user
from pydantic import BaseModel, field_validator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

ALLOWED_CURRENCIES = {"INR", "USD", "EUR", "GBP", "AED", "SGD", "JPY"}


class OnboardingCompleteRequest(BaseModel):
    full_name: str
    store_name: str
    initial_balance: float
    currency: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty")
        if len(v) > 255:
            raise ValueError("Full name must be 255 characters or fewer")
        return v

    @field_validator("store_name")
    @classmethod
    def validate_store_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Store name cannot be empty")
        if len(v) > 255:
            raise ValueError("Store name must be 255 characters or fewer")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in ALLOWED_CURRENCIES:
            raise ValueError(f"Currency must be one of: {', '.join(sorted(ALLOWED_CURRENCIES))}")
        return v

    @field_validator("initial_balance")
    @classmethod
    def validate_balance(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Initial balance cannot be negative")
        return v


@router.post("/complete")
async def complete_onboarding(
    request: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Finalize user onboarding: save profile and create the default store.
    """
    # 1. Update user profile
    current_user.full_name = request.full_name
    current_user.store_name = request.store_name
    current_user.initial_balance = request.initial_balance
    current_user.currency = request.currency
    current_user.is_onboarded = True

    # 2. Create the default Store record for this user
    default_store = Store(
        user_id=current_user.id,
        name=request.store_name,
        location="Headquarters",
        currency=request.currency,
        is_active=True,
    )
    db.add(default_store)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to save onboarding data for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save onboarding data. Please try again."
        )

    return {"status": "success", "message": "Onboarding complete"}
