
import pandas as pd
import pytest

from main import extract_data, validate_and_transform


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "order_id": [101, 102, 102, 103, 104, 105],
        "customer": ["A", "B", "B", "C", "D", "E"],
        "product": [
            "Keyboard", "Mouse", "Mouse", "Monitor", None, "Webcam"
        ],
        "price": [1500, 500, 500, -100, 800, 1200],
        "quantity": [2, 1, 1, 1, 1, 0]
    })


def test_duplicate_order_is_rejected(sample_data):
    clean, rejected = validate_and_transform(sample_data)

    assert not clean["order_id"].duplicated().any()
    assert rejected["rejection_reason"].str.contains(
        "Duplicate order ID"
    ).any()


def test_negative_price_is_rejected(sample_data):
    clean, rejected = validate_and_transform(sample_data)

    assert (clean["price"] >= 0).all()
    assert rejected["rejection_reason"].str.contains(
        "Negative price"
    ).any()


def test_missing_product_is_rejected(sample_data):
    clean, rejected = validate_and_transform(sample_data)

    assert clean["product"].notna().all()
    assert rejected["rejection_reason"].str.contains(
        "Missing product"
    ).any()


def test_quantity_must_be_positive(sample_data):
    clean, rejected = validate_and_transform(sample_data)

    assert (clean["quantity"] > 0).all()
    assert rejected["rejection_reason"].str.contains(
        "Quantity must be positive"
    ).any()


def test_every_row_is_accounted_for(sample_data):
    clean, rejected = validate_and_transform(sample_data)

    assert len(clean) + len(rejected) == len(sample_data)


def test_extract_rejects_missing_columns(tmp_path):
    file_path = tmp_path / "bad.csv"
    file_path.write_text("order_id,customer\n101,A", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing columns"):
        extract_data(file_path)
