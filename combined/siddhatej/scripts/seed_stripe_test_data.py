"""
scripts/seed_stripe_test_data.py
---------------------------------
Seeds your Stripe TEST account with realistic fake customers.

Run:
    cd ETL_Pipeline_Project
    source venv/bin/activate
    python scripts/seed_stripe_test_data.py

Then run the pipeline:
    python src/main.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import requests
from dotenv import load_dotenv

load_dotenv()

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
BASE_URL = "https://api.stripe.com/v1"
HEADERS = {"Authorization": f"Bearer {STRIPE_API_KEY}"}

# ---------------------------------------------------------------------------
# Fake but realistic test customer data
# ---------------------------------------------------------------------------
TEST_CUSTOMERS = [
    {
        "name": "Alice Johnson",
        "email": "alice.johnson@example.com",
        "phone": "+14155551234",
        "description": "Premium subscriber",
        "address": {
            "line1": "123 Market St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "country": "US",
        },
        "metadata": {"plan": "premium", "source": "organic"},
    },
    {
        "name": "Bob Smith",
        "email": "bob.smith@example.com",
        "phone": "+14155555678",
        "description": "Basic plan customer",
        "address": {
            "line1": "456 Broadway",
            "city": "New York",
            "state": "NY",
            "postal_code": "10013",
            "country": "US",
        },
        "metadata": {"plan": "basic", "source": "referral"},
    },
    {
        "name": "Priya Patel",
        "email": "priya.patel@techcorp.in",
        "phone": "+919876543210",
        "description": "Enterprise client",
        "address": {
            "line1": "78 Koramangala",
            "city": "Bangalore",
            "state": "KA",
            "postal_code": "560034",
            "country": "IN",
        },
        "metadata": {"plan": "enterprise", "source": "sales"},
    },
    {
        "name": "Carlos Mendez",
        "email": "carlos.mendez@startup.mx",
        "phone": "+525512345678",
        "description": "Startup founder",
        "address": {
            "line1": "10 Reforma Ave",
            "city": "Mexico City",
            "postal_code": "06600",
            "country": "MX",
        },
        "metadata": {"plan": "startup", "source": "conference"},
    },
    {
        "name": "Emma Wilson",
        "email": "emma.wilson@consulting.co.uk",
        "phone": "+442071234567",
        "description": "Consulting firm",
        "address": {
            "line1": "1 Canary Wharf",
            "city": "London",
            "postal_code": "E14 5AB",
            "country": "GB",
        },
        "metadata": {"plan": "premium", "source": "linkedin"},
    },
    {
        "name": "Yuki Tanaka",
        "email": "yuki.tanaka@design.jp",
        "phone": "+81312345678",
        "description": "Design agency",
        "address": {
            "line1": "2-1 Shibuya",
            "city": "Tokyo",
            "postal_code": "150-0002",
            "country": "JP",
        },
        "metadata": {"plan": "basic", "source": "website"},
    },
    {
        "name": "Amara Okonkwo",
        "email": "amara.okonkwo@fintech.ng",
        "phone": "+2348012345678",
        "description": "Fintech startup",
        "metadata": {"plan": "startup", "source": "accelerator"},
    },
    {
        "name": "Lucas Dupont",
        "email": "lucas.dupont@creative.fr",
        "phone": "+33123456789",
        "description": "Creative agency",
        "address": {
            "line1": "15 Rue de Rivoli",
            "city": "Paris",
            "postal_code": "75001",
            "country": "FR",
        },
        "metadata": {"plan": "premium", "source": "partner"},
    },
    {
        "name": "Sofia Andersen",
        "email": "sofia.andersen@saas.dk",
        "phone": "+4512345678",
        "description": "SaaS company",
        "metadata": {"plan": "enterprise", "source": "inbound"},
    },
    {
        "name": "Raj Nair",
        "email": "raj.nair@analytics.io",
        "phone": "+14085559012",
        "description": "Data analytics firm",
        "address": {
            "line1": "500 Silicon Valley Blvd",
            "city": "San Jose",
            "state": "CA",
            "postal_code": "95101",
            "country": "US",
        },
        "metadata": {"plan": "enterprise", "source": "cold_outreach"},
    },
]

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _flatten_for_stripe(customer: dict) -> dict:
    """
    Stripe expects nested fields like address[line1], address[city], etc.
    Convert the nested dict to flat form for requests form-encoding.
    """
    flat = {}
    for key, val in customer.items():
        if isinstance(val, dict):
            for sub_key, sub_val in val.items():
                flat[f"{key}[{sub_key}]"] = sub_val
        else:
            flat[key] = val
    return flat


def create_customer(data: dict) -> dict:
    """Create a single customer via Stripe API."""
    flat = _flatten_for_stripe(data)
    response = requests.post(
        f"{BASE_URL}/customers",
        headers=HEADERS,
        data=flat,
        timeout=(10, 30),
    )
    response.raise_for_status()
    return response.json()


def get_existing_emails() -> set:
    """Fetch existing customer emails to avoid duplicates."""
    emails = set()
    starting_after = None
    while True:
        params = {"limit": 100}
        if starting_after:
            params["starting_after"] = starting_after
        resp = requests.get(f"{BASE_URL}/customers", headers=HEADERS, params=params, timeout=(10, 30))
        resp.raise_for_status()
        data = resp.json()
        for c in data["data"]:
            if c.get("email"):
                emails.add(c["email"])
        if not data["has_more"]:
            break
        starting_after = data["data"][-1]["id"]
    return emails


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 55)
    print("  🌱  Stripe Test Data Seeder")
    print("=" * 55)
    print(f"  API Key : {STRIPE_API_KEY[:12]}...{STRIPE_API_KEY[-4:]}")
    print(f"  Mode    : TEST (safe — no real charges)")
    print(f"  Seeding : {len(TEST_CUSTOMERS)} customers")
    print("=" * 55 + "\n")

    # Check for existing customers to avoid duplicates
    print("  Checking for existing customers...")
    existing_emails = get_existing_emails()
    if existing_emails:
        print(f"  Found {len(existing_emails)} existing customer(s) — skipping duplicates\n")

    created = []
    skipped = []
    failed = []

    for i, customer in enumerate(TEST_CUSTOMERS, 1):
        email = customer["email"]

        if email in existing_emails:
            print(f"  [{i:02d}/{len(TEST_CUSTOMERS)}]  ⏭  SKIP  {customer['name']} ({email})")
            skipped.append(email)
            continue

        try:
            result = create_customer(customer)
            created.append(result)
            print(f"  [{i:02d}/{len(TEST_CUSTOMERS)}]  ✅  CREATED  {customer['name']} → {result['id']}")
            time.sleep(0.3)  # be polite to the API rate limits
        except requests.HTTPError as e:
            print(f"  [{i:02d}/{len(TEST_CUSTOMERS)}]  ❌  FAILED   {customer['name']} — {e}")
            failed.append(email)

    # Summary
    print("\n" + "=" * 55)
    print("  Seeding Complete")
    print("=" * 55)
    print(f"  ✅ Created : {len(created)}")
    print(f"  ⏭  Skipped : {len(skipped)} (already existed)")
    print(f"  ❌ Failed  : {len(failed)}")
    print("=" * 55)
    print("\n  Now run the pipeline:")
    print("  → python src/main.py\n")


if __name__ == "__main__":
    main()
