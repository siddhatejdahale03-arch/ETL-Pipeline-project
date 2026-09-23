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
    """Unified transaction record loaded from Stripe/Salesforce.

    Attributes:
        id: Source system's unique identifier (primary key).
        source_system: Either "stripe" or "salesforce".
        customer_id: Foreign identifier for the customer, if known.
        amount: Transaction amount in the given currency.
        currency: ISO 4217 currency code, e.g. "USD".
        status: Source system's status string for the transaction.
        created_at: When the transaction was created upstream.
        updated_at: When the transaction was last updated upstream.
        is_synced: Whether this row reflects the latest upstream state.
    """
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    source_system = Column(String, nullable=False)
    customer_id = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(3), nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    is_synced = Column(Boolean, default=True)
