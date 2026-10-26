"""Unified schema — the single shape every source is converted into.

Both Stripe and Salesforce records are mapped to these two models so
the rest of the pipeline (loader, tests, BI tools) only has to deal
with one consistent structure.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UnifiedCustomer(BaseModel):
    """
    One customer record — regardless of whether it came from Stripe or Salesforce.

    Primary key in the warehouse: (customer_id, source_system)
    """
    customer_id: str
    source_system: str           # "stripe" or "salesforce"
    email: Optional[str] = None
    full_name: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue_usd: Optional[float] = None
    is_delinquent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    ingested_at: datetime         # when OUR pipeline loaded this record


class UnifiedTransaction(BaseModel):
    """
    One transaction — a Stripe charge OR a Salesforce Opportunity.

    Primary key in the warehouse: (transaction_id, source_system)
    """
    transaction_id: str
    source_system: str           # "stripe" or "salesforce"
    customer_id: Optional[str] = None
    amount_usd: float
    status: str
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    ingested_at: datetime
