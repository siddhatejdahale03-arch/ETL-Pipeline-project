"""Utilities for cleaning customer data before normalization."""

from __future__ import annotations

from typing import Any, Dict


def clean_string(value: Any) -> Any:
    """Trim whitespace and convert blank strings to None."""
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else None

    return value


def clean_customer_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean top-level customer fields without changing their structure.

    The function is intentionally conservative: it only cleans textual
    values and leaves numeric, boolean, nested, and metadata structures
    unchanged.
    """
    cleaned = dict(data)

    string_fields = (
        "name",
        "email",
        "phone",
        "description",
        "currency",
        "invoice_prefix",
        "tax_exempt",
        "default_source",
        "test_clock",
    )

    for field in string_fields:
        if field in cleaned:
            cleaned[field] = clean_string(cleaned[field])

    return cleaned