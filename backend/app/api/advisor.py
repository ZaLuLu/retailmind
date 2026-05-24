from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from ..api.deps import get_current_user
from ..models.db import User
from ..services.gemini import gemini_service
from pydantic import BaseModel
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

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
    Ask the AI advisor a financial question (synchronous).
    """
    if not request.question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )
        
    answer = await gemini_service.ask_advisor(request.question, request.context)
    return AdvisorResponse(answer=answer)

@router.post("/stream")
async def stream_advisor(
    request: AdvisorRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Stream the AI advisor's answer to a financial question (SSE).
    """
    if not request.question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )
        
    async def event_generator():
        try:
            async for chunk in gemini_service.stream_advisor(request.question, request.context):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            logger.exception("Error in advisor stream")
            yield f"data: {json.dumps({'error': 'Transcription failed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
