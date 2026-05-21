from fastapi import APIRouter, Depends, HTTPException, status
from ..api.deps import get_current_user
from ..models.db import User
from ..services.gemini import gemini_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/advisor", tags=["Advisor"])

class AdvisorRequest(BaseModel):
    question: str
    context: Optional[str] = None

class AdvisorResponse(BaseModel):
    answer: str

@router.post("/ask", response_model=AdvisorResponse)
async def ask_advisor(
    request: AdvisorRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ask the AI advisor a financial question.
    """
    if not request.question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )
        
    answer = await gemini_service.ask_advisor(request.question, request.context)
    return AdvisorResponse(answer=answer)
