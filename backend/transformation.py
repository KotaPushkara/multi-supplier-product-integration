import re


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_gtin(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return digits or None


def map_supplier_record(record, supplier):
    mappings = {
        "supplier_a": {
            "supplier_sku": "sku",
            "name": "product_name",
            "brand": "brand_name",
            "gtin": "ean",
            "category": "dept",
            "price": "price",
            "currency": "currency_code",
        },
        "supplier_b": {
            "supplier_sku": "supplier_item",
            "name": "title",
            "brand": "maker",
            "gtin": "barcode",
            "category": "category_name",
            "price": "unit_price",
            "currency": "currency",
        },
        "supplier_c": {
            "supplier_sku": "supplierSku",
            "name": "description",
            "brand": "manufacturer",
            "gtin": "gtin_code",
            "category": "product_type",
            "price": "cost",
            "currency": "currencyCode",
        },
    }

    if supplier not in mappings:
        raise ValueError(f"Unknown supplier: {supplier}")

    mapping = mappings[supplier]

    standardized = {
        key: record.get(source)
        for key, source in mapping.items()
    }

    standardized["supplier"] = supplier

    return standardize_record(standardized)


def standardize_record(record):
    return {
        "supplier_sku": normalize_text(record.get("supplier_sku")),
        "name": normalize_text(record.get("name")),
        "brand": normalize_text(record.get("brand")),
        "gtin": normalize_gtin(record.get("gtin")),
        "category": normalize_text(record.get("category")),
        "price": record.get("price"),
        "currency": normalize_text(
            record.get("currency") or "INR"
        ).upper(),
        "supplier": record.get("supplier"),
    }