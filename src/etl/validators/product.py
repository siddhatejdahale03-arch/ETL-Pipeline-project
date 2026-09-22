from pydantic import BaseModel

from etl.utils.logger import get_logger


logger = get_logger(__name__)


class Product(BaseModel):
    id: int
    title: str
    price: float
    category: str


def validate_products(products):
    valid_products = []

    for product in products:
        try:
            validated_product = Product(**product)
            valid_products.append(validated_product)

        except Exception as error:
            logger.error(
                f"❌ Invalid product: {error}"
            )

    return valid_products