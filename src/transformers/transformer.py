"""End-to-end customer transformation pipeline."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from models.customer import Customer
from transformers.cleaner import clean_customer_data
from transformers.mapper import customer_to_dict
from transformers.normalizer import normalize_customer_data
from validators.validator import ensure_valid_customer_record


def transform_customer(customer: Customer) -> Dict[str, Any]:
    """
    Transform one validated Customer into a validated canonical record.

    Pipeline:

        Customer
          ↓
        mapping
          ↓
        cleaning
          ↓
        normalization
          ↓
        downstream validation
    """
    data = customer_to_dict(customer)
    data = clean_customer_data(data)
    data = normalize_customer_data(data)

    ensure_valid_customer_record(data)

    return data


def transform_customers(
    customers: Iterable[Customer],
) -> List[Dict[str, Any]]:
    """Transform a collection of validated Customer objects."""
    return [transform_customer(customer) for customer in customers]