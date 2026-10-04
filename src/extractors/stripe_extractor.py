"""
Download customers and charges from Stripe.

Stripe uses CURSOR pagination:
    page 1: GET /customers?limit=100
    page 2: GET /customers?limit=100&starting_after=<id of last item on page 1>
    ... keep going while the answer says "has_more": true
"""
from datetime import datetime

from config.settings import get_settings
from src.extractors.base_extractor import get_json, load_sample
from src.utils.logger import get_logger

log = get_logger("stripe")


class StripeExtractor:
    def __init__(self):
        self.settings = get_settings()
        self.headers = {"Authorization": f"Bearer {self.settings.stripe_api_key}"}

    def fetch_all(self, endpoint: str, since: datetime | None = None) -> list[dict]:
        """Fetch every page of one Stripe endpoint, e.g. 'customers'."""
        url = f"{self.settings.stripe_base_url}/{endpoint}"
        params = {"limit": self.settings.stripe_page_limit}
        if since:  # incremental load: only records created after `since`
            params["created[gte]"] = int(since.timestamp())

        all_records = []
        page = 0
        while True:
            page += 1
            body = get_json(url, self.headers, params)
            records = body["data"]
            all_records.extend(records)
            log.info("page_downloaded", endpoint=endpoint, page=page, rows=len(records))

            if not body.get("has_more") or not records:
                break
            params["starting_after"] = records[-1]["id"]  # the cursor

        return all_records

    def extract(self, since: datetime | None = None) -> list[dict]:
        """Return customers + charges. Each record gets a '_type' tag."""
        if self.settings.demo_mode:
            log.info("demo_mode", detail="reading data/sample/stripe_*.json")
            customers = load_sample("stripe_customers.json")
            charges = load_sample("stripe_charges.json")
        else:
            customers = self.fetch_all("customers", since)
            charges = self.fetch_all("charges", since)

        for record in customers:
            record["_type"] = "customer"
        for record in charges:
            record["_type"] = "charge"

        log.info("extract_done", customers=len(customers), charges=len(charges))
        return customers + charges
