"""Validation rules for transformed customer records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


class TransformationValidationError(ValueError):
    """Raised when a transformed customer record is invalid."""


def validate_customer_record(data: Dict[str, Any]) -> List[str]:
    """
    Validate the minimum downstream requirements for a customer record.

    Returns:
        A list of validation error messages. An empty list means valid.
    """
    errors: List[str] = []

    customer_id = data.get("id")

    if not isinstance(customer_id, str) or not customer_id.strip():
        errors.append("id must be a non-empty string")

    email = data.get("email")

    if email is not None and not isinstance(email, str):
        errors.append("email must be a string or None")

    currency = data.get("currency")

    if currency is not None:
        if not isinstance(currency, str):
            errors.append("currency must be a string or None")
        elif len(currency) != 3:
            errors.append("currency must be a 3-character ISO code")

    created = data.get("created")

    if created is not None and not isinstance(created, str):
        errors.append("created must be an ISO-8601 string or None")

    return errors


def ensure_valid_customer_record(data: Dict[str, Any]) -> None:
    """Raise TransformationValidationError if the record is invalid."""
    errors = validate_customer_record(data)

    if errors:
        raise TransformationValidationError("; ".join(errors))