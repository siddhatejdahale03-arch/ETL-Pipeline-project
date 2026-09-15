import json
from pathlib import Path

import requests


API_URL = "https://dummyjson.com/products"


def fetch_products():
    print("🚀 Fetching products from DummyJSON...")

    response = requests.get(API_URL)

    print("Status Code:", response.status_code)

    response.raise_for_status()

    data = response.json()

    print("Total Products:", data["total"])

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / "dummyjson_products.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"✅ Raw data saved successfully: {file_path}")

    return data


if __name__ == "__main__":
    fetch_products()