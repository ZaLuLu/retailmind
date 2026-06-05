from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    DECIMAL,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from ..core.db import Base


# ─────────────────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    """Core user / store-owner account."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    store_name = Column(String(255), nullable=True)
    initial_balance = Column(DECIMAL(15, 2), default=0.0)
    is_onboarded = Column(Boolean, default=False)
    currency = Column(String(3), default="INR")          # e.g. INR, USD, EUR
    intelligence_meta = Column(JSONB, nullable=True)

    # New columns (Phase 0 / upgrade plan §3.2)
    timezone = Column(String(50), default="UTC")         # per-user timezone
    plan = Column(String(20), default="free")            # free | pro | enterprise
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class RefreshToken(Base):
    """JWT refresh token store with rotation support."""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
# Stores
# ─────────────────────────────────────────────────────────────────────────────

class Store(Base):
    """A retail store location associated with a user account."""

    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)

    # New columns (upgrade plan §3.2)
    currency = Column(String(3), default="INR")          # per-store currency override
    timezone = Column(String(50), nullable=True)         # for multi-timezone chains
    is_active = Column(Boolean, default=True)            # soft-delete

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
# Sale Records  (core RetailMind model)
# ─────────────────────────────────────────────────────────────────────────────

class SaleRecord(Base):
    """
    Represents a single sales transaction.
    Populated via CSV/Excel upload, manual entry, or document scan.
    """

    __tablename__ = "sale_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Product info ──────────────────────────────────────────────────────────
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=True)
    product_category = Column(String(100), nullable=False, default="Other")

    # ── Sales figures ─────────────────────────────────────────────────────────
    quantity_sold = Column(Float, nullable=False, default=1.0)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    total_revenue = Column(DECIMAL(12, 2), nullable=False)
    cogs = Column(DECIMAL(12, 2), nullable=True)          # Cost of Goods Sold
    gross_margin = Column(DECIMAL(5, 2), nullable=True)   # % e.g. 42.50

    # ── Context ───────────────────────────────────────────────────────────────
    sale_date = Column(Date, nullable=False, index=True)
    customer_segment = Column(String(50), nullable=True)  # Walk-in | Online | B2B
    currency = Column(String(3), default="INR")

    # ── New fields (upgrade plan §3.2) ────────────────────────────────────────
    notes = Column(Text, nullable=True)                   # manual annotations
    tags = Column(JSONB, nullable=True)                   # flexible labeling (list)
    is_return = Column(Boolean, default=False)            # handles refunds

    # ── ML Intelligence (auto-populated by ml services) ───────────────────────
    ml_meta = Column(JSONB, nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────
    source = Column(String(50), default="csv_upload")     # csv_upload | excel_upload | manual | scan
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_sale_user_date", "user_id", "sale_date"),
        Index("idx_sale_user_category", "user_id", "product_category"),
        Index("idx_sale_sku", "user_id", "product_sku"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Smart Alerts  (new — upgrade plan §3.2)
# ─────────────────────────────────────────────────────────────────────────────

class Alert(Base):
    """
    Persisted smart alerts: dead stock, margin erosion, demand spikes.
    Survives page refresh. Supports read/unread and severity levels.
    """

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    store_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Alert classification
    alert_type = Column(String(50), nullable=False)       # dead_stock | margin_erosion | demand_spike
    product_sku = Column(String(100), nullable=True)
    product_name = Column(String(255), nullable=True)
    severity = Column(String(20), default="warning")      # info | warning | critical

    # Rich payload (thresholds, context, recommended action, etc.)
    payload = Column(JSONB, nullable=True)

    # State
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Partial index: fast unread count lookup per user
        Index("idx_alerts_user_unread", "user_id", "is_read"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI Conversations  (new — upgrade plan §3.2)
# ─────────────────────────────────────────────────────────────────────────────

class AIConversation(Base):
    """
    Persisted Retail Advisor chat history.
    context_snapshot holds KPI data at conversation start for Gemini context injection.
    """

    __tablename__ = "ai_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    messages = Column(JSONB, nullable=False, default=list)      # [{role, content, ts}]
    context_snapshot = Column(JSONB, nullable=True)             # KPI snapshot at conversation start

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# ML Results  (new — upgrade plan §14.2)
# ─────────────────────────────────────────────────────────────────────────────

class MLResult(Base):
    """
    Stores the latest ML computation result per user per type.
    chart-bundle endpoint reads from here; ML services write here.
    UNIQUE(user_id, result_type) enforces one current result per type.
    data_hash allows skipping recomputation when input data hasn't changed.
    """

    __tablename__ = "ml_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    result_type = Column(String(50), nullable=False)       # forecast | portfolio | segments | alerts
    payload = Column(JSONB, nullable=False)
    data_hash = Column(String(64), nullable=True)          # SHA-256 of input rows; skip if unchanged
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "result_type", name="uq_ml_result_user_type"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Legacy (scheduled for removal — upgrade plan §3.2)
# ─────────────────────────────────────────────────────────────────────────────

class Budget(Base):
    """LEGACY — personal finance model, scheduled for removal in a future migration."""

    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category = Column(String(50), nullable=False)
    monthly_limit = Column(DECIMAL(10, 2), nullable=False)
    month = Column(Date, nullable=False)
# 
    __table_args__ = (
        Index("idx_user_category_month", "user_id", "category", "month", unique=True),
    )
# 

class Transaction(Base):
    """LEGACY — personal finance model, scheduled for removal in a future migration."""
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
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
