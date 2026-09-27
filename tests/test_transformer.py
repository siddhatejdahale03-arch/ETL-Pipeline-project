from models.customer import Customer
from transformers.transformer import transform_customer


def test_transform_customer():
    customer = Customer(
        id="cus_123",
        name="  Alice Johnson  ",
        email=" Alice@Example.COM ",
        currency="USD",
        created=0,
    )

    result = transform_customer(customer)

    assert result["id"] == "cus_123"
    assert result["name"] == "Alice Johnson"
    assert result["email"] == "alice@example.com"
    assert result["currency"] == "usd"
    assert result["created"] == "1970-01-01T00:00:00+00:00"