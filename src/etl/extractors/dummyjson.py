import json
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from etl.utils.logger import get_logger


API_URL = "https://dummyjson.com/products"
LIMIT = 10

logger = get_logger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def fetch_page(skip):
    params = {
        "limit": LIMIT,
        "skip": skip,
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=10,
    )

    logger.info(
        f"Fetching: limit={LIMIT}, "
        f"skip={skip}, "
        f"Status={response.status_code}"
    )

    response.raise_for_status()

    return response.json()


def fetch_products():
    logger.info("🚀 Fetching products from DummyJSON...")

    all_products = []
    skip = 0

    while True:
        data = fetch_page(skip)

        products = data["products"]
        all_products.extend(products)

        logger.info(f"Received {len(products)} products")

        if skip + LIMIT >= data["total"]:
            break

        skip += LIMIT

    logger.info(f"✅ Total products fetched: {len(all_products)}")

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / "dummyjson_products.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(all_products, file, indent=2)

    logger.info(f"✅ Raw data saved successfully: {file_path}")

    return all_products


if __name__ == "__main__":
    fetch_products()