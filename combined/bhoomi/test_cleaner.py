from transformers.cleaner import clean_customer_data


def test_clean_customer_data_trims_strings():
    result = clean_customer_data(
        {
            "id": "cus_123",
            "name": "  Alice Johnson  ",
            "email": " alice@example.com ",
        }
    )

    assert result["name"] == "Alice Johnson"
    assert result["email"] == "alice@example.com"


def test_clean_customer_data_converts_blank_strings_to_none():
    result = clean_customer_data(
        {
            "id": "cus_123",
            "name": "   ",
        }
    )

    assert result["name"] is None