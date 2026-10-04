"""Pydantic models for Salesforce API payloads."""
from typing import Optional
from pydantic import BaseModel


class SalesforceAccount(BaseModel):
    Id: str
    Name: Optional[str] = None
    Industry: Optional[str] = None
    AnnualRevenue: Optional[float] = None
    CreatedDate: Optional[str] = None
    LastModifiedDate: Optional[str] = None


class SalesforceOpportunity(BaseModel):
    Id: str
    AccountId: Optional[str] = None
    Name: Optional[str] = None
    Amount: Optional[float] = None
    StageName: Optional[str] = None
    CloseDate: Optional[str] = None