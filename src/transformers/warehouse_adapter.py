from datetime import datetime, timezone
from typing import Any, Dict, Optional


def stripe_customer_to_warehouse_row(
    record: Dict[str, Any],
    ingested_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    created = record.get("created")

    if isinstance(created, (int, float)):
        created_at = datetime.fromtimestamp(created, tz=timezone.utc)
    elif isinstance(created, str) and created:
        created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = created_at.astimezone(timezone.utc)
    else:
        created_at = None

    return {
        "customer_id": record["id"],
        "source_system": "stripe",
        "email": record.get("email"),
        "full_name": record.get("name"),
        "industry": None,
        "annual_revenue_usd": None,
        "is_delinquent": bool(record.get("delinquent", False)),
        "created_at": created_at,
        "updated_at": None,
        "ingested_at": ingested_at or datetime.now(timezone.utc),
    }
