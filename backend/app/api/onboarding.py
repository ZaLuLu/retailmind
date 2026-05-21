from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.db import get_db
from ..models.db import User, Budget
from ..api.deps import get_current_user
from pydantic import BaseModel
from typing import Dict
from datetime import date

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

class OnboardingCompleteRequest(BaseModel):
    full_name: str
    store_name: str
    initial_balance: float
    currency: str
    budgets: Dict[str, float]

@router.post("/complete")
async def complete_onboarding(
    request: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Finalize user onboarding and create initial budget records.
    """
    # 1. Update user profile
    current_user.full_name = request.full_name
    current_user.store_name = request.store_name
    current_user.initial_balance = request.initial_balance
    current_user.currency = request.currency
    current_user.is_onboarded = True
    current_user.intelligence_meta = {"budgets": request.budgets}
    
    # 2. Create budget records for the current month
    today = date.today()
    first_of_month = today.replace(day=1)
    
    for category, limit in request.budgets.items():
        if limit > 0:
            new_budget = Budget(
                user_id=current_user.id,
                category=category,
                monthly_limit=limit,
                month=first_of_month
            )
            db.add(new_budget)
            
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save onboarding data"
        )
        
    return {"status": "success", "message": "Onboarding complete"}
