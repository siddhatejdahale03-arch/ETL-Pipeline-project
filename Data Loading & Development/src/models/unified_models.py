"""Unified schema — the single source of truth for the DW."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UnifiedCustomer(BaseModel):
    customer_id: str
    source_system: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue_usd: Optional[float] = None
    is_delinquent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    ingested_at: datetime


class UnifiedTransaction(BaseModel):
    transaction_id: str
    source_system: str
    customer_id: Optional[str] = None
    amount_usd: float
    status: str
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    ingested_at: datetime