"""
loaders/local_loader.py — Local filesystem raw data store.

Mirrors the S3Loader interface exactly but writes to local disk instead.
Perfect for development, testing, and free-tier usage with zero cloud setup.

Data is written to a Hive-style partitioned directory tree:
    {base_path}/{source}/{entity}/year=YYYY/month=MM/day=DD/{run_id}/data.json
    {base_path}/{source}/{entity}/year=YYYY/month=MM/day=DD/{run_id}/_manifest.json

This structure is identical to the S3 layout, making it trivial to switch
to S3 later — just swap LocalFileLoader for S3Loader in main.py.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class LocalFileLoader:
    """
    Saves raw JSON data to a local partitioned directory structure.

    Identical interface to S3Loader — swap one for the other with no
    changes to business logic.

    Usage:
        loader = LocalFileLoader()
        data_path, manifest = loader.upload(
            source="stripe",
            records=[c.model_dump() for c in customers],
        )
    """

    def __init__(self, base_path: Optional[str] = None) -> None:
        """
        Args:
            base_path: Root directory for all raw data.
                       Defaults to config.LOCAL_STORAGE_PATH (./data/raw).
        """
        self.base_path = os.path.abspath(base_path or config.LOCAL_STORAGE_PATH)
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(
            "LocalFileLoader initialised",
            extra={"base_path": self.base_path},
        )

    # ------------------------------------------------------------------
    # Path generation (mirrors S3Loader.get_s3_key)
    # ------------------------------------------------------------------

    def get_local_path(
        self,
        source: str,
        entity: str,
        run_id: str,
        dt: Optional[datetime] = None,
        filename: str = "data.json",
    ) -> str:
        """
        Build a Hive-partitioned local file path.

        Pattern:
            {base_path}/{source}/{entity}/year=YYYY/month=MM/day=DD/{run_id}/{filename}

        Args:
            source:   Data source name, e.g. "stripe".
            entity:   Entity type, e.g. "customers".
            run_id:   Unique run identifier.
            dt:       Partition date (defaults to UTC now).
            filename: File name inside the run folder.

        Returns:
            Absolute local file path string.

        Example:
            "/path/to/data/raw/stripe/customers/year=2026/month=09/day=18/abc123/data.json"
        """
        if dt is None:
            dt = datetime.now(tz=timezone.utc)

        return os.path.join(
            self.base_path,
            source,
            entity,
            f"year={dt.year}",
            f"month={dt.month:02d}",
            f"day={dt.day:02d}",
            run_id,
            filename,
        )

    # ------------------------------------------------------------------
    # Public interface (same signature as S3Loader.upload)
    # ------------------------------------------------------------------

    def upload(
        self,
        source: str,
        records: List[Dict[str, Any]],
        entity: str = "customers",
        run_id: Optional[str] = None,
        extracted_at: Optional[datetime] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Write raw JSON records to local disk with a matching manifest file.

        Args:
            source:       Data source name, e.g. "stripe".
            records:      List of plain dicts to serialise as JSON.
            entity:       Entity type for path, e.g. "customers".
            run_id:       Unique pipeline run ID (auto-generated if None).
            extracted_at: Timestamp for partitioning (defaults to UTC now).

        Returns:
            Tuple of:
                data_path — Absolute path to the written data.json file.
                manifest  — The manifest dict that was written.
        """
        run_id = run_id or str(uuid.uuid4())
        extracted_at = extracted_at or datetime.now(tz=timezone.utc)

        # --- 1. Build paths ---
        data_path = self.get_local_path(source, entity, run_id, dt=extracted_at, filename="data.json")
        manifest_path = self.get_local_path(source, entity, run_id, dt=extracted_at, filename="_manifest.json")

        # --- 2. Create directory ---
        os.makedirs(os.path.dirname(data_path), exist_ok=True)

        # --- 3. Build payload ---
        payload = {
            "run_id": run_id,
            "source": source,
            "entity": entity,
            "extracted_at": extracted_at.isoformat(),
            "record_count": len(records),
            "records": records,
        }

        # --- 4. Write data.json ---
        logger.info(
            "Writing raw data to local file",
            extra={
                "path": data_path,
                "record_count": len(records),
                "run_id": run_id,
            },
        )
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        # --- 5. Write _manifest.json ---
        manifest: Dict[str, Any] = {
            "run_id": run_id,
            "source": source,
            "entity": entity,
            "extracted_at": extracted_at.isoformat(),
            "record_count": len(records),
            "storage": "local",
            "data_path": data_path,
            "status": "success",
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(
            "Local file write complete",
            extra={
                "data_path": data_path,
                "manifest_path": manifest_path,
                "run_id": run_id,
            },
        )

        return data_path, manifest
