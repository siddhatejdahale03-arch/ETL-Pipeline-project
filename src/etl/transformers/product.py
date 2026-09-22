import polars as pl


def transform_products(products: list[dict]) -> pl.DataFrame:
    """
    Transform validated DummyJSON products
    into the internal product warehouse schema.
    """

    df = pl.DataFrame(products)

    df = df.select(
        [
            pl.col("id").alias("product_id"),
            pl.col("title").alias("product_name"),
            pl.col("description"),
            pl.col("category"),
            pl.col("price").cast(pl.Float64),
            pl.col("discountPercentage").alias("discount_percentage").cast(pl.Float64),
            pl.col("rating").cast(pl.Float64),
            pl.col("stock").alias("stock_quantity").cast(pl.Int64),
            pl.col("brand"),
            pl.col("sku"),
            pl.col("weight").cast(pl.Float64),
            pl.col("availabilityStatus").alias("availability_status"),
            pl.col("warrantyInformation").alias("warranty_information"),
            pl.col("shippingInformation").alias("shipping_information"),
        ]
    )

    return df