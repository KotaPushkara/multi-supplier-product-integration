from .conflict_resolution import choose_preferred


def build_canonical_product(records, supplier_priority=None):
    """Build a canonical product with field-level source traceability."""

    if not records:
        return None

    fields = [
        "gtin",
        "name",
        "brand",
        "category",
        "price",
        "currency",
    ]

    product = {}
    provenance = {}

    for field in fields:
        candidates = [
            row for row in records
            if row.get(field) not in (None, "")
        ]

        if candidates:
            selected = choose_preferred(
                candidates, supplier_priority
            )
            product[field] = selected.get(field)

            provenance[field] = {
                "supplier": selected.get("supplier"),
                "value": selected.get(field),
            }
        else:
            product[field] = None

    product["sources"] = sorted({
        row.get("supplier")
        for row in records
        if row.get("supplier")
    })

    product["provenance"] = provenance

    return product