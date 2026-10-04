"""Pydantic models for Stripe API payloads."""
from typing import Optional
from pydantic import BaseModel


class StripeCustomer(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created: int
    currency: Optional[str] = "usd"
    delinquent: Optional[bool] = False


class StripeCharge(BaseModel):
    id: str
    customer: Optional[str] = None
    amount: int
    currency: str
    status: str
    created: int
    description: Optional[str] = None