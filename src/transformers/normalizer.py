"""Normalization utilities for customer data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def normalize_email(value: Any) -> Any:
    """Normalize an email address for consistent downstream storage."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip().lower()
        return value if value else None

    return value


def normalize_currency(value: Any) -> Any:
    """Normalize a currency code to lowercase."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip().lower()
        return value if value else None

    return value


def normalize_created_timestamp(value: Any) -> Any:
    """
    Convert a Unix timestamp into an ISO-8601 UTC string.

    Invalid values are returned unchanged so that validation can report
    the problem rather than silently losing the original value.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            ).isoformat()
        except (OverflowError, OSError, ValueError):
            return value

    return value


def normalize_customer_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply supported customer normalization rules."""
    normalized = dict(data)

    if "email" in normalized:
        normalized["email"] = normalize_email(normalized["email"])

    if "currency" in normalized:
        normalized["currency"] = normalize_currency(normalized["currency"])

    if "created" in normalized:
        normalized["created"] = normalize_created_timestamp(
            normalized["created"]
        )

    return normalized