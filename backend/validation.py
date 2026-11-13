REQUIRED_FIELDS = ("supplier_sku", "name")

def validate_record(record: dict):
    """Return (is_valid, reason). Supplier-specific mapping happens before this stage."""
    missing = [field for field in REQUIRED_FIELDS if not str(record.get(field, "")).strip()]
    if missing:
        return False, "Missing required field(s): " + ", ".join(missing)
    return True, None