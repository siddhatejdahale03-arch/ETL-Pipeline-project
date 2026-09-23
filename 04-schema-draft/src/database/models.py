"""
Warehouse table definitions.
Owner: Rohan (Data Loading & Warehouse Development)

v1 draft — sketched straight from a first read of the Stripe/Salesforce
API docs. Field names/types will likely need correcting (see commit 6).
"""
from sqlalchemy import Column, String, Float, DateTime
from src.database.db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    source_system = Column(String)
    customer_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String)
    created_at = Column(DateTime)
