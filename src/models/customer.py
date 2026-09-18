"""
models/customer.py — Pydantic v2 data model for a Stripe Customer object.

Covers all commonly used fields from the Stripe Customer API response.
Extra fields from the API are silently ignored (extra="ignore") so the model
never breaks when Stripe adds new fields.

Reference: https://docs.stripe.com/api/customers/object
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerAddress(BaseModel):
    """Mailing / billing address."""

    model_config = ConfigDict(extra="ignore")

    city: Optional[str] = None
    country: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None


class CustomerShipping(BaseModel):
    """Shipping information on the customer."""

    model_config = ConfigDict(extra="ignore")

    address: Optional[CustomerAddress] = None
    name: Optional[str] = None
    phone: Optional[str] = None


class Customer(BaseModel):
    """
    Stripe Customer object.

    All fields are Optional (except `id`) because Stripe only returns
    fields that have been set — a freshly created customer may have
    very few populated fields.
    """

    model_config = ConfigDict(extra="ignore")

    # Core identity
    id: str
    object: str = "customer"

    # Contact info
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None

    # Address
    address: Optional[CustomerAddress] = None
    shipping: Optional[CustomerShipping] = None

    # Financial state
    balance: int = 0                        # Balance in cents (can be negative = credit)
    currency: Optional[str] = None          # ISO 4217 code, e.g. "usd"
    delinquent: Optional[bool] = None       # True if outstanding invoice is past due
    invoice_prefix: Optional[str] = None    # Unique prefix for invoices

    # Tax
    tax_exempt: Optional[str] = None        # "none" | "exempt" | "reverse"

    # Payment methods
    default_source: Optional[str] = None    # ID of the default payment source
    invoice_settings: Optional[Dict[str, Any]] = None

    # Metadata & timestamps
    metadata: Dict[str, str] = Field(default_factory=dict)
    created: int = 0                        # Unix timestamp
    livemode: bool = False                  # True in production, False in test mode

    # Stripe test-clock (used in test environments)
    test_clock: Optional[str] = None

    # Preferred locale
    preferred_locales: List[str] = Field(default_factory=list)

    @property
    def created_iso(self) -> str:
        """Return the `created` Unix timestamp as an ISO 8601 string."""
        from datetime import datetime, timezone
        return datetime.fromtimestamp(self.created, tz=timezone.utc).isoformat()
