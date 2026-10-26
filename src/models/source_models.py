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
    """Represents a customer object from the Stripe API."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created: int   # Unix timestamp (seconds since epoch)
    delinquent: bool = False


class StripeCharge(BaseModel):
    """Represents a charge (payment attempt) from the Stripe API."""
    id: str
    customer: Optional[str] = None
    amount: int    # amount is in cents! e.g. 1999 = $19.99
    currency: str
    status: str
    description: Optional[str] = None
    created: int


# ---------------- Salesforce ----------------
class SalesforceAccount(BaseModel):
    """Represents an Account record from Salesforce CRM."""
    Id: str
    Name: Optional[str] = None
    Industry: Optional[str] = None
    AnnualRevenue: Optional[float] = None
    CreatedDate: datetime
    LastModifiedDate: datetime


class SalesforceOpportunity(BaseModel):
    """Represents an Opportunity (deal) record from Salesforce CRM."""
    Id: str
    AccountId: Optional[str] = None
    Name: Optional[str] = None
    Amount: Optional[float] = None
    StageName: str
    CloseDate: date
