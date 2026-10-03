"""
config.py — Centralised configuration & secrets loader.

Loads all required environment variables from a .env file and
validates that every required key is present at startup.
Raises a descriptive ValueError immediately if anything is missing,
so the pipeline never runs in a half-configured state.
"""

from __future__ import annotations

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file (no-op if already in environment, safe to call multiple times)
load_dotenv()

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _require(key: str) -> str:
    """Return the value of an env var or raise with a helpful message."""
    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"[Config] Required environment variable '{key}' is missing or empty. "
            f"Add it to your .env file. See .env.example for reference."
        )
    return value


def _optional(key: str, default: Optional[str] = None) -> Optional[str]:
    """Return the value of an env var or a default (no error)."""
    return os.getenv(key, default)


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------
STRIPE_API_KEY: str = _require("STRIPE_API_KEY")

# Stripe pagination: how many records to request per page (max 100)
STRIPE_PAGE_LIMIT: int = int(_optional("STRIPE_PAGE_LIMIT", "100"))

# ---------------------------------------------------------------------------
# Storage backend: "local" or "s3"
# ---------------------------------------------------------------------------
STORAGE_BACKEND: str = _optional("STORAGE_BACKEND", "local").lower()

# ---------------------------------------------------------------------------
# Local filesystem storage (used when STORAGE_BACKEND=local)
# ---------------------------------------------------------------------------
LOCAL_STORAGE_PATH: str = _optional("LOCAL_STORAGE_PATH", "./data/raw")

# ---------------------------------------------------------------------------
# AWS / S3 — Only required when STORAGE_BACKEND=s3
# ---------------------------------------------------------------------------
AWS_ACCESS_KEY_ID: Optional[str] = _optional("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY: Optional[str] = _optional("AWS_SECRET_ACCESS_KEY")
AWS_REGION: Optional[str] = _optional("AWS_REGION", "us-east-1")
AWS_BUCKET_NAME: Optional[str] = _optional("AWS_BUCKET_NAME")
S3_RAW_PREFIX: str = _optional("S3_RAW_PREFIX", "raw")

def _validate_s3_config() -> None:
    """Called only when STORAGE_BACKEND=s3. Raises if any AWS key is missing."""
    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_BUCKET_NAME"):
        if not os.getenv(key):
            raise ValueError(
                f"[Config] STORAGE_BACKEND is 's3' but '{key}' is missing. "
                f"Add it to .env or switch to STORAGE_BACKEND=local."
            )

# ---------------------------------------------------------------------------
# Salesforce (optional — planned for future weeks)
# ---------------------------------------------------------------------------
SALESFORCE_ACCESS_TOKEN: Optional[str] = _optional("SALESFORCE_ACCESS_TOKEN")
SALESFORCE_INSTANCE_URL: Optional[str] = _optional("SALESFORCE_INSTANCE_URL")

# ---------------------------------------------------------------------------
# Pipeline behaviour
# ---------------------------------------------------------------------------
MAX_RETRY_ATTEMPTS: int = int(_optional("MAX_RETRY_ATTEMPTS", "3"))
LOG_LEVEL: str = _optional("LOG_LEVEL", "INFO").upper()
