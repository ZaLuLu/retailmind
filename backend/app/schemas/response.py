"""
Standard API Response Schemas for RetailMind
Provides a unified structure for Success, Error, and Validation payloads.
"""
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any, List
from datetime import datetime, timezone

T = TypeVar('T')

def utc_now():
    return datetime.now(timezone.utc)

class SuccessResponse(BaseModel, Generic[T]):
    """Standard success API response"""
    success: bool = True
    data: T
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)

class ErrorResponse(BaseModel):
    """Standard error API response"""
    success: bool = False
    error: str
    details: Optional[Any] = None
    timestamp: datetime = Field(default_factory=utc_now)
    request_id: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated query response"""
    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    timestamp: datetime = Field(default_factory=utc_now)

class ValidationErrorDetail(BaseModel):
    """Validation error structure"""
    field: str
    message: str
    type: str

class ValidationErrorResponse(BaseModel):
    """Standard payload validation error response"""
    success: bool = False
    error: str = "Validation error"
    details: List[ValidationErrorDetail]
    timestamp: datetime = Field(default_factory=utc_now)
