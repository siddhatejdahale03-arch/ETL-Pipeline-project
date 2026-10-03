"""Map validated source customer objects into a canonical representation."""

from __future__ import annotations

from typing import Any, Dict

from models.customer import Customer


def customer_to_dict(customer: Customer) -> Dict[str, Any]:
    """
    Convert a validated Customer model into a dictionary suitable for
    downstream transformation.

    Pydantic is responsible for source-model validation; this function
    focuses only on representation.
    """
    return customer.model_dump(mode="python")