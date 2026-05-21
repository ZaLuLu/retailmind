from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.db import get_db
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import date
from ..models.db import User, Budget
from ..api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    initial_balance: Optional[float] = None
    store_name: Optional[str] = None
    currency: Optional[str] = None
    budgets: Optional[Dict[str, float]] = None

class UserResponse(BaseModel):
    email: str
    full_name: Optional[str]
    store_name: Optional[str]
    initial_balance: float
    is_onboarded: bool
    currency: Optional[str] = "INR"
    intelligence_meta: Optional[dict] = None

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
    
    if request.budgets is not None:
        current_user.intelligence_meta = {"budgets": request.budgets}
        
        # Update or create Budget records for the current month
        today = date.today()
        first_of_month = today.replace(day=1)
        
        for category, limit in request.budgets.items():
            # Check if budget already exists for this category/month
            from sqlalchemy import select, and_
            stmt = select(Budget).where(
                and_(
                    Budget.user_id == current_user.id,
                    Budget.category == category,
                    Budget.month == first_of_month
                )
            )
            result = await db.execute(stmt)
            existing_budget = result.scalar_one_or_none()
            
            if existing_budget:
                existing_budget.monthly_limit = limit
            else:
                new_budget = Budget(
                    user_id=current_user.id,
                    category=category,
                    monthly_limit=limit,
                    month=first_of_month
                )
                db.add(new_budget)
        
    try:
        await db.commit()
        await db.refresh(current_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )
        
    return current_user
