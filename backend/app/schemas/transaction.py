from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

class TransactionBase(BaseModel):
    vendor_name: Optional[str] = None
    amount: Decimal
    category: str = "Other"
    transaction_date: date
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    confidence: Optional[Decimal] = None
    document_path: Optional[str] = None
    created_by_ai: bool = False
    intelligence_meta: Optional[dict] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ExtractionResult(BaseModel):
    """Structured output from Gemini extraction"""
    vendor_name: Optional[str] = Field(description="Name of the merchant or vendor")
    amount: Decimal = Field(description="Total amount spent")
    category: str = Field(description="Financial category (e.g. Food, Transport, Utilities)")
    transaction_date: date = Field(description="Date of the transaction")
    confidence: float = Field(description="Confidence score between 0 and 1")
    notes: Optional[str] = Field(description="Any additional notes or summary of the item")
