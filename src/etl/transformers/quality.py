import polars as pl


def validate_products(df: pl.DataFrame) -> None:
    """
    Run data quality checks on the transformed product DataFrame.
    """

    # 1. Check required columns for null values
    required_columns = [
        "product_id",
        "product_name",
        "category",
        "price",
        "stock_quantity",
    ]

    for column in required_columns:
        null_count = df[column].null_count()

        if null_count > 0:
            raise ValueError(
                f"Data quality error: {column} contains {null_count} null values"
            )

    # 2. Check duplicate product IDs
    duplicate_count = (
        df.group_by("product_id")
        .agg(pl.len().alias("count"))
        .filter(pl.col("count") > 1)
        .height
    )

    if duplicate_count > 0:
        raise ValueError(
            f"Data quality error: {duplicate_count} duplicate product IDs found"
        )

    # 3. Check negative prices
    negative_prices = df.filter(pl.col("price") < 0).height

    if negative_prices > 0:
        raise ValueError(
            f"Data quality error: {negative_prices} products have negative prices"
        )

    # 4. Check negative stock
    negative_stock = df.filter(pl.col("stock_quantity") < 0).height

    if negative_stock > 0:
        raise ValueError(
            f"Data quality error: {negative_stock} products have negative stock"
        )

    print("Data quality checks passed.")
    print(f"Validated rows: {df.height}")