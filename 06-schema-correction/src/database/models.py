"""
Warehouse table definitions.
Owner: Rohan (Data Loading & Warehouse Development)

Revision history:
  v1 (commit 4): first draft from Stripe/Salesforce docs
  v2 (commit 6): field names/types corrected after reading docs closely
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean
from src.database.db import Base


class Transaction(Base):
    """Unified transaction record loaded from Stripe/Salesforce."""
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)          # source system's unique ID
    source_system = Column(String, nullable=False)  # "stripe" or "salesforce"
    customer_id = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(3), nullable=True)     # ISO 4217, e.g. "USD"
    status = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    is_synced = Column(Boolean, default=True)
