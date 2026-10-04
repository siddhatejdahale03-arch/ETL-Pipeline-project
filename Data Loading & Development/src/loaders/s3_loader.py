"""Write raw JSON to S3 data lake."""
import json
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
log = get_logger("s3_loader")


class S3Loader:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        self.bucket = settings.s3_bucket

    def write_json(self, source: str, records: list[dict]) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y/%m/%d/%H%M%S")
        key = f"raw/{source}/{ts}.json"
        body = json.dumps(records, default=str).encode("utf-8")
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
            log.info("s3_write_ok", bucket=self.bucket, key=key, size=len(body))
        except (BotoCoreError, ClientError) as e:
            log.error("s3_write_failed", error=str(e))
            raise
        return f"s3://{self.bucket}/{key}"