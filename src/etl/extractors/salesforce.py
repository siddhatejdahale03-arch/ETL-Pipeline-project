import json
import os
from pathlib import Path
from dotenv import load_dotenv
from simple_salesforce import Salesforce

load_dotenv()


def fetch_salesforce_leads():
    print("🚀 Salesforce Authentication দিয়ে Live Lead Data extract করা হচ্ছে...")

    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    security_token = os.getenv("SALESFORCE_SECURITY_TOKEN", "")

    try:
        # domain="login" ব্যবহার করলে এটি সঠিক Endpoint (login.salesforce.com) এ হিট করবে
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain="login",
        )

        soql_query = "SELECT Id, FirstName, LastName, Company, Email, Status, CreatedDate FROM Lead LIMIT 50"
        results = sf.query_all(soql_query)
        leads = results.get("records", [])

        # Extra attributes বাদ দেয়া
        for lead in leads:
            lead.pop("attributes", None)

        raw_dir = Path("data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        file_path = raw_dir / "salesforce_leads.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2)

        print(
            f"🎉 SUCCESS! সফলভাবে {len(leads)} টি Real Salesforce Lead Data পাওয়া গেছে: {file_path}"
        )
        return leads

    except Exception as e:
        print(f"\n❌ Salesforce API Connection Error: {e}")
        return None


if __name__ == "__main__":
    fetch_salesforce_leads()