"""
src/transformers/transformer.py — End-to-end customer transformation pipeline.

Updated to use the new multi-source cleaner + mapper instead of the old
clean_customer_data() / customer_to_dict() functions that were replaced
during the final integration merge.

This module is kept for backward compatibility and delegates to the new
cleaner + mapper pipeline.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from src.transformers.cleaner import clean_stripe_customers
from src.transformers.mapper import to_unified_customers
from src.models.customer import Customer


def transform_customer(customer: Customer) -> Dict[str, Any]:
    """
    Transform one validated Stripe Customer into a unified canonical record.

    Pipeline:
        Customer model
          ↓
        clean_stripe_customers()   (trim, lowercase, Unix -> UTC)
          ↓
        to_unified_customers()     (add source_system, ingested_at)
          ↓
        dict (first row of unified DataFrame)
    """
    # Convert pydantic model to the raw dict shape the cleaner expects
    raw = {
        "id": customer.id,
        "email": customer.email,
        "name": customer.name,
        "created": customer.created,
        "delinquent": customer.delinquent if customer.delinquent is not None else False,
    }
    cleaned_df = clean_stripe_customers([raw])
    unified_df = to_unified_customers(cleaned_df, None)
    return unified_df.to_dicts()[0]


def transform_customers(customers: Iterable[Customer]) -> List[Dict[str, Any]]:
    """Transform a collection of validated Stripe Customer objects."""
    return [transform_customer(c) for c in customers]