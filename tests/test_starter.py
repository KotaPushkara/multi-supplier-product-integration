
from backend.validation import validate_record
from backend.transformation import (
    normalize_gtin,
    normalize_text,
    map_supplier_record,
)
from backend.conflict_resolution import choose_preferred
from backend.publishing import build_canonical_product


def test_required_fields():
    assert validate_record(
        {"supplier_sku": "A1", "name": "Item"}
    ) == (True, None)


def test_missing_name_rejected():
    ok, reason = validate_record(
        {"supplier_sku": "A1", "name": ""}
    )
    assert not ok
    assert "name" in reason


def test_missing_sku_rejected():
    ok, reason = validate_record(
        {"supplier_sku": "", "name": "Item"}
    )
    assert not ok
    assert "supplier_sku" in reason


def test_gtin_normalization():
    assert normalize_gtin("890-123 456") == "890123456"


def test_text_normalization():
    assert normalize_text("  sample   item ") == "sample item"


def test_supplier_a_mapping():
    result = map_supplier_record(
        {
            "sku": "A1",
            "product_name": "Phone",
            "brand_name": "BrandX",
            "ean": "890-123",
            "dept": "Electronics",
            "price": 100,
            "currency_code": "INR",
        },
        "supplier_a",
    )
    assert result["supplier_sku"] == "A1"
    assert result["name"] == "Phone"
    assert result["gtin"] == "890123"


def test_unknown_supplier_rejected():
    try:
        map_supplier_record({}, "unknown")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_supplier_priority():
    candidates = [
        {"supplier": "supplier_b", "updated_at": "2026-01-02"},
        {"supplier": "supplier_a", "updated_at": "2026-01-01"},
    ]
    result = choose_preferred(
        candidates,
        {"supplier_a": 1, "supplier_b": 2},
    )
    assert result["supplier"] == "supplier_a"


def test_latest_update_breaks_priority_tie():
    candidates = [
        {"supplier": "supplier_a", "updated_at": "2026-01-01"},
        {"supplier": "supplier_a", "updated_at": "2026-01-03"},
    ]
    result = choose_preferred(candidates, {"supplier_a": 1})
    assert result["updated_at"] == "2026-01-03"


def test_canonical_product_provenance():
    records = [
        {
            "supplier": "supplier_a",
            "gtin": "890123",
            "name": "Phone",
            "brand": "BrandX",
            "category": "Electronics",
            "price": 100,
            "currency": "INR",
        },
        {
            "supplier": "supplier_b",
            "gtin": "890123",
            "name": "phone",
            "brand": "BrandX",
            "category": "Electronics",
            "price": 105,
            "currency": "INR",
        },
    ]

    result = build_canonical_product(
        records,
        {"supplier_a": 1, "supplier_b": 2},
    )

    assert result["name"] == "Phone"
    assert result["price"] == 100
    assert result["provenance"]["price"]["supplier"] == "supplier_a"
    assert set(result["sources"]) == {"supplier_a", "supplier_b"}
