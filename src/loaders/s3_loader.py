"""
loaders/s3_loader.py — Raw data lake loader for AWS S3.

Writes raw extracted data to S3 using a Hive-style partitioned path
that makes the data immediately queryable by Athena / Glue:

    s3://<bucket>/raw/<source>/year=YYYY/month=MM/day=DD/<run_id>/data.json

Also writes a _manifest.json alongside every upload containing run metadata:
    run_id, source, record_count, extracted_at, status, s3_key

Design principles:
  - Idempotent: the same run_id always writes to the same S3 key.
  - Atomic-ish: data.json is written before _manifest.json so a failed
    manifest doesn't leave orphaned data that looks "complete".
  - Zero local disk I/O: data is serialised and streamed directly to S3.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import BotoCoreError, ClientError

import config
from utils.logger import get_logger
from utils.retry import with_retry

logger = get_logger(__name__)


class S3Loader:
    """
    Uploads raw JSON data to a partitioned S3 raw data lake path.

    Usage:
        loader = S3Loader()
        s3_key, manifest = loader.upload(
            source="stripe",
            records=[customer.model_dump() for customer in customers],
        )
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> None:
        """
        Args:
            bucket: S3 bucket name. Defaults to config.AWS_BUCKET_NAME.
            region: AWS region.     Defaults to config.AWS_REGION.
            prefix: Top-level S3 prefix. Defaults to config.S3_RAW_PREFIX ("raw").
        """
        self.bucket = bucket or config.AWS_BUCKET_NAME
        self.region = region or config.AWS_REGION
        self.prefix = prefix or config.S3_RAW_PREFIX

        self._client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        )

        logger.info(
            "S3Loader initialised",
            extra={"bucket": self.bucket, "region": self.region, "prefix": self.prefix},
        )

    # ------------------------------------------------------------------
    # Key generation
    # ------------------------------------------------------------------

    def get_s3_key(
        self,
        source: str,
        entity: str,
        run_id: str,
        dt: datetime | None = None,
        filename: str = "data.json",
    ) -> str:
        """
        Build a Hive-partitioned S3 key for a given source/entity/run.

        Pattern:
            {prefix}/{source}/{entity}/year=YYYY/month=MM/day=DD/{run_id}/{filename}

        Args:
            source:  Data source name, e.g. "stripe".
            entity:  Entity type, e.g. "customers".
            run_id:  Unique run identifier (UUID string).
            dt:      Partition date. Defaults to current UTC time.
            filename: File name inside the run folder.

        Returns:
            S3 object key string (no leading slash).

        Example:
            "raw/stripe/customers/year=2026/month=09/day=18/abc123/data.json"
        """
        if dt is None:
            dt = datetime.now(tz=timezone.utc)

        return (
            f"{self.prefix}/{source}/{entity}"
            f"/year={dt.year}"
            f"/month={dt.month:02d}"
            f"/day={dt.day:02d}"
            f"/{run_id}/{filename}"
        )

    # ------------------------------------------------------------------
    # Upload helpers
    # ------------------------------------------------------------------

    @with_retry(max_attempts=3, wait_min=1.0, wait_max=30.0)
    def _put_object(self, key: str, body: str, content_type: str = "application/json") -> None:
        """
        Upload a string body to S3.

        Args:
            key:          S3 object key.
            body:         String content to upload.
            content_type: MIME type header.

        Raises:
            ClientError / BotoCoreError after retries exhausted.
        """
        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body.encode("utf-8"),
                ContentType=content_type,
            )
        except (ClientError, BotoCoreError) as exc:
            logger.error(
                "S3 put_object failed",
                extra={"bucket": self.bucket, "key": key, "error": str(exc)},
            )
            raise

    # ------------------------------------------------------------------
    # Public interface
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
        Upload raw JSON records to S3 and write a manifest file.

        Args:
            source:       Data source name, e.g. "stripe".
            records:      List of plain dicts to serialise as JSON.
            entity:       Entity type for S3 path, e.g. "customers".
            run_id:       Unique pipeline run ID (auto-generated if None).
            extracted_at: Timestamp for partitioning (defaults to UTC now).

        Returns:
            Tuple of:
                data_key  — S3 key of the uploaded data.json file.
                manifest  — The manifest dict that was written to S3.

        Raises:
            ClientError / BotoCoreError if S3 uploads fail after retries.
        """
        run_id = run_id or str(uuid.uuid4())
        extracted_at = extracted_at or datetime.now(tz=timezone.utc)

        # --- 1. Build keys ---
        data_key = self.get_s3_key(source, entity, run_id, dt=extracted_at, filename="data.json")
        manifest_key = self.get_s3_key(source, entity, run_id, dt=extracted_at, filename="_manifest.json")

        # --- 2. Serialise records ---
        payload = {
            "run_id": run_id,
            "source": source,
            "entity": entity,
            "extracted_at": extracted_at.isoformat(),
            "record_count": len(records),
            "records": records,
        }
        data_json = json.dumps(payload, default=str, indent=2)

        # --- 3. Upload data ---
        logger.info(
            "Uploading raw data to S3",
            extra={
                "bucket": self.bucket,
                "key": data_key,
                "record_count": len(records),
                "run_id": run_id,
            },
        )
        self._put_object(data_key, data_json)

        # --- 4. Write manifest ---
        manifest: Dict[str, Any] = {
            "run_id": run_id,
            "source": source,
            "entity": entity,
            "extracted_at": extracted_at.isoformat(),
            "record_count": len(records),
            "s3_bucket": self.bucket,
            "s3_key": data_key,
            "status": "success",
        }
        manifest_json = json.dumps(manifest, indent=2)
        self._put_object(manifest_key, manifest_json)

        logger.info(
            "S3 upload complete",
            extra={
                "bucket": self.bucket,
                "data_key": data_key,
                "manifest_key": manifest_key,
                "run_id": run_id,
            },
        )

        return data_key, manifest
