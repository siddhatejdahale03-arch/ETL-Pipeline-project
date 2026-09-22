import json

from etl.transformers.product import transform_products
from etl.transformers.quality import validate_products
from etl.loaders.postgres import load_products


def main():
    with open("data/raw/dummyjson_products.json", "r") as file:
        products = json.load(file)

    df = transform_products(products)

    validate_products(df)

    loaded_count = load_products(df)

    print(f"Successfully loaded: {loaded_count}")


if __name__ == "__main__":
    main()
