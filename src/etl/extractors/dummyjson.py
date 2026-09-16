import json
from pathlib import Path

import requests


API_URL = "https://dummyjson.com/products"
LIMIT = 10


def fetch_products():
    print("🚀 Fetching products from DummyJSON...")

    all_products = []
    skip = 0

    while True:
        params = {
            "limit": LIMIT,
            "skip": skip,
        }

        response = requests.get(API_URL, params=params)

        print(
            f"Fetching: limit={LIMIT}, "
            f"skip={skip}, "
            f"Status={response.status_code}"
        )

        response.raise_for_status()

        data = response.json()
        products = data["products"]

        all_products.extend(products)

        print(f"Received {len(products)} products")

        if skip + LIMIT >= data["total"]:
            break

        skip += LIMIT

    print(f"✅ Total products fetched: {len(all_products)}")

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / "dummyjson_products.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(all_products, file, indent=2)

    print(f"✅ Raw data saved successfully: {file_path}")

    return all_products


if __name__ == "__main__":
    fetch_products()