from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from ..api.deps import get_current_user
from ..models.db import User
from ..services.gemini import gemini_service
from pydantic import BaseModel, field_validator
from typing import Optional
import json
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advisor", tags=["Advisor"])

class AdvisorRequest(BaseModel):
    question: str
    context: Optional[str] = None

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        try:
            import json
            data = json.loads(v)
            if not isinstance(data, dict):
                raise ValueError("Context must be a valid JSON object")
            
            allowed_keys = {
                "total_revenue", "total_cogs", "gross_profit", "overall_margin_pct",
                "mom_revenue_change_pct", "num_sales", "ai_insight", "period",
                "date_from", "date_to"
            }
            
            safe_data = {}
            for k in allowed_keys:
                if k in data:
                    val = data[k]
                    if isinstance(val, (int, float, str, bool)) or val is None:
                        safe_data[k] = val
            
            list_keys = {
                "top_products": ["product_name", "category", "revenue", "quantity", "margin_pct"],
                "category_breakdown": ["category", "revenue", "cogs", "margin_pct"],
                "demand_signals": ["product_name", "type", "z_score", "deviation_pct", "message", "recent_qty", "prior_weekly_avg"],
                "dead_stock_alerts": ["product_name", "last_sale_days_ago", "message"],
                "margin_erosion_alerts": ["product_name", "margin_pct", "revenue", "message"],
                "customer_segments": ["segment", "revenue", "cogs", "margin_pct", "aov", "share", "mom_growth_pct", "num_orders"]
            }
            
            for list_key, allowed_fields in list_keys.items():
                if list_key in data and isinstance(data[list_key], list):
                    safe_list = []
                    for item in data[list_key][:10]:
                        if isinstance(item, dict):
                            safe_item = {}
                            for f in allowed_fields:
                                if f in item:
                                    f_val = item[f]
                                    if isinstance(f_val, (int, float, str, bool)) or f_val is None:
                                        safe_item[f] = f_val
                            safe_list.append(safe_item)
                    safe_data[list_key] = safe_list

            return json.dumps(safe_data)
        except Exception as exc:
            raise ValueError(f"Malformed or unsafe context: {exc}")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        max_len = 1000
        if len(v) > max_len:
            raise ValueError(f"Question exceeds maximum length of {max_len} characters")
        # Basic prompt injection mitigation: strip known injection patterns
        import re
        # Remove attempts to override system prompt via role-play instructions
        injection_patterns = [
            r"ignore\s+(previous|above|all)\s+instructions",
            r"system\s+prompt",
            r"forget\s+(everything|all)",
            r"you\s+are\s+now",
            r"pretend\s+(you\s+are|to\s+be)",
            r"act\s+as\s+(if\s+you\s+are|a)",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Question contains disallowed content")
        return v

class AdvisorResponse(BaseModel):
    answer: str

@router.post("/ask", response_model=AdvisorResponse)
async def ask_advisor(
    request: AdvisorRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ask the AI advisor a retail business question (synchronous).
    Question is validated and sanitized before forwarding to Gemini.
    """
    answer = await gemini_service.ask_advisor(request.question, request.context)
    return AdvisorResponse(answer=answer)

@router.post("/stream")
async def stream_advisor(
    request: AdvisorRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Stream the AI advisor's answer (SSE).
    Question is validated and sanitized before forwarding to Gemini.
    """
    async def event_generator():
        try:
            async for chunk in gemini_service.stream_advisor(request.question, request.context):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception:
            logger.exception("Error in advisor stream")
            yield f"data: {json.dumps({'error': 'Stream failed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
