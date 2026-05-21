from sqlalchemy import Column, String, DECIMAL, Date, DateTime, Boolean, ForeignKey, Text, Index, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from ..core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    store_name = Column(String(255), nullable=True)
    initial_balance = Column(DECIMAL(15, 2), default=0.0)
    is_onboarded = Column(Boolean, default=False)
    currency = Column(String(3), default="INR")  # INR or USD
    intelligence_meta = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Budget(Base):
    """LEGACY — personal finance model, scheduled for removal."""
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    monthly_limit = Column(DECIMAL(10, 2), nullable=False)
    month = Column(Date, nullable=False)

    __table_args__ = (
        Index("idx_user_category_month", "user_id", "category", "month", unique=True),
    )

class Transaction(Base):
    """LEGACY — personal finance model, scheduled for removal."""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vendor_name = Column(String(255))
    amount = Column(DECIMAL(10, 2), nullable=False)
    category = Column(String(50), nullable=False, default="Other")
    transaction_date = Column(Date, nullable=False)
    confidence = Column(DECIMAL(5, 2))
    notes = Column(Text)
    document_path = Column(String(500))
    intelligence_meta = Column(JSONB, nullable=True)
    created_by_ai = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SaleRecord(Base):
    """
    RetailMind core model — represents a single sales transaction.
    Populated via CSV/Excel upload or manual entry.
    """
    __tablename__ = "sale_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)

    # Product Info
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=True)
    product_category = Column(String(100), nullable=False, default="Other")

    # Sales Figures
    quantity_sold = Column(Float, nullable=False, default=1.0)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    total_revenue = Column(DECIMAL(12, 2), nullable=False)
    cogs = Column(DECIMAL(12, 2), nullable=True)          # Cost of Goods Sold
    gross_margin = Column(DECIMAL(5, 2), nullable=True)   # % e.g. 42.5

    # Context
    sale_date = Column(Date, nullable=False, index=True)
    customer_segment = Column(String(50), nullable=True)  # Walk-in, Online, B2B
    currency = Column(String(3), default="INR")

    # ML Intelligence (auto-populated by ml_engine)
    ml_meta = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(50), default="csv_upload")  # csv_upload | excel_upload | manual

    __table_args__ = (
        Index("idx_sale_user_date", "user_id", "sale_date"),
        Index("idx_sale_user_category", "user_id", "product_category"),
        Index("idx_sale_sku", "user_id", "product_sku"),
    )

class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
