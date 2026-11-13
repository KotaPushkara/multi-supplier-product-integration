def choose_preferred(candidates, supplier_priority=None):
    """Choose by supplier priority, then latest update."""

    supplier_priority = supplier_priority or {}

    if not candidates:
        return {}

    return max(
        candidates,
        key=lambda row: (
            -supplier_priority.get(row.get("supplier"), 10000),
            str(row.get("updated_at") or ""),
            str(row.get("supplier") or ""),
        ),
    )