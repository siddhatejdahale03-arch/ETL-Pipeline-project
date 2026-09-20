from pydantic import BaseModel



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
            print(f"❌ Invalid product: {error}")

    return valid_products