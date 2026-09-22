import polars as pl
from sqlalchemy import text

from etl.config.database import engine


def load_products(df: pl.DataFrame) -> int:
    """
    Load transformed products into PostgreSQL.
    """

    records = df.to_dicts()

    if not records:
        print("No products to load.")
        return 0

    insert_sql = text(
        """
        INSERT INTO products (
            product_id,
            product_name,
            description,
            category,
            price,
            discount_percentage,
            rating,
            stock_quantity,
            brand,
            sku,
            weight,
            availability_status,
            warranty_information,
            shipping_information
        )
        VALUES (
            :product_id,
            :product_name,
            :description,
            :category,
            :price,
            :discount_percentage,
            :rating,
            :stock_quantity,
            :brand,
            :sku,
            :weight,
            :availability_status,
            :warranty_information,
            :shipping_information
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(insert_sql, records)

    print(f"Loaded {len(records)} products into PostgreSQL.")

    return len(records)