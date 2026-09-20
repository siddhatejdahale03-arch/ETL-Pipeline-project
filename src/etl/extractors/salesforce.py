"""Extract live Lead records from Salesforce into the raw data lake."""

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from requests import RequestException
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed, SalesforceError

# Permit `python src/etl/extractors/salesforce.py` from the repository root,
# while preserving normal package imports when run with `python -m`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from etl.utils.logger import get_logger


load_dotenv()

logger = get_logger(__name__)
RAW_FILE = Path("data/raw/salesforce_leads.json")
LEAD_QUERY = (
    "SELECT Id, FirstName, LastName, Company, Email, Status, CreatedDate, LastModifiedDate "
    "FROM Lead ORDER BY CreatedDate DESC LIMIT 50"
)


def _required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _salesforce_domain() -> str:
    """Return the domain format expected by simple-salesforce.

    Salesforce's UI commonly shows a full host such as
    ``company.my.salesforce.com``.  simple-salesforce appends
    ``.salesforce.com`` itself, so it expects ``company.my``.
    """
    domain = os.getenv("SALESFORCE_DOMAIN", "login").strip()
    domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    if domain.endswith(".salesforce.com"):
        return domain[: -len(".salesforce.com")]
    return domain


def get_salesforce_client() -> Salesforce:
    """Authenticate using values from .env without exposing secrets in logs."""
    options: dict[str, str] = {
        "username": _required_setting("SALESFORCE_USERNAME"),
        "password": _required_setting("SALESFORCE_PASSWORD"),
        "domain": _salesforce_domain(),
    }

    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
    if client_id and client_secret:
        # This uses the REST OAuth password grant, which works in orgs where
        # the legacy SOAP login endpoint is disabled. Salesforce expects the
        # security token to be appended to the password in this flow.
        options["password"] += os.getenv("SALESFORCE_SECURITY_TOKEN", "")
        options["consumer_key"] = client_id
        options["consumer_secret"] = client_secret
    else:
        options["security_token"] = os.getenv("SALESFORCE_SECURITY_TOKEN", "")

    return Salesforce(**options)


def fetch_salesforce_leads(limit: int = 50) -> list[dict[str, Any]]:
    """Fetch live Leads and replace the raw file only after a successful call."""
    if not 1 <= limit <= 2_000:
        raise ValueError("limit must be between 1 and 2000")

    query = LEAD_QUERY.replace("LIMIT 50", f"LIMIT {limit}")
    logger.info("Connecting to Salesforce (domain=%s)", _salesforce_domain())

    try:
        sf = get_salesforce_client()
        total_leads = sf.query("SELECT COUNT() FROM Lead")["totalSize"]
        result = sf.query_all(query)
    except ValueError:
        raise
    except SalesforceAuthenticationFailed as error:
        logger.error("Salesforce authentication failed. Check .env credentials and domain.")
        raise RuntimeError("Salesforce authentication failed") from error
    except SalesforceError as error:
        logger.error("Salesforce query failed: %s", error)
        raise RuntimeError("Salesforce query failed") from error
    except RequestException as error:
        logger.error("Could not reach Salesforce: %s", error)
        raise RuntimeError("Could not reach Salesforce") from error

    leads = result.get("records", [])
    for lead in leads:
        lead.pop("attributes", None)

    logger.info("Salesforce has %s Lead record(s); extracted %s record(s).", total_leads, len(leads))
    if total_leads > len(leads):
        logger.warning("The configured extraction limit is %s; more Lead records are available.", limit)

    RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RAW_FILE.open("w", encoding="utf-8") as file:
        json.dump(leads, file, indent=2, default=str)

    logger.info("Saved verified Salesforce response to %s", RAW_FILE)
    return leads


if __name__ == "__main__":
    fetch_salesforce_leads()
