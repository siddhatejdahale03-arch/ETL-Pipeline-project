"""
Pydantic models = the "shape" we expect from each API.

If an API record is missing a required field or has a wrong type,
Pydantic raises a ValidationError and we skip that record.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# ---------------- Stripe ----------------
class StripeCustomer(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created: int  # Unix timestamp (seconds)
    delinquent: bool = False


class StripeCharge(BaseModel):
    id: str
    customer: Optional[str] = None
    amount: int  # in cents! 1999 = 19.99
    currency: str
    status: str
    description: Optional[str] = None
    created: int


# ---------------- Salesforce ----------------
class SalesforceAccount(BaseModel):
    Id: str
    Name: Optional[str] = None
    Industry: Optional[str] = None
    AnnualRevenue: Optional[float] = None
    CreatedDate: datetime
    LastModifiedDate: datetime


class SalesforceOpportunity(BaseModel):
    Id: str
    AccountId: Optional[str] = None
    Name: Optional[str] = None
    Amount: Optional[float] = None
    StageName: str
    CloseDate: date
