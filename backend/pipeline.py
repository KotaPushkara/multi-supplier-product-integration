
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .database import get_connection
from .ingestion import read_feed
from .transformation import map_supplier_record
from .validation import validate_record
from .publishing import build_canonical_product


SUPPLIERS = {
    "supplier_a": {"file": "supplier_a/feed.csv", "priority": 1},
    "supplier_b": {"file": "supplier_b/feed.csv", "priority": 2},
    "supplier_c": {"file": "supplier_c/feed.json", "priority": 3},
}

BATCH_SIZE = 1000


def convert_price(value):
    if value in (None, ""):
        return None
    try:
        price = Decimal(str(value))
        if not price.is_finite() or price < 0:
            return None
        return price
    except (InvalidOperation, ValueError):
        return None


def execute_batches(cursor, sql, rows):
    for start in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(
            sql,
            rows[start:start + BATCH_SIZE]
        )


def run_pipeline(data_dir="data"):
    connection = get_connection()
    cursor = connection.cursor()
    run_id = None

    input_rows = 0
    accepted_rows = 0
    rejected_rows = 0
    duplicate_rows = 0
    output_rows = 0

    try:
        cursor.execute(
            "INSERT INTO pipeline_runs (status) VALUES ('RUNNING')"
        )
        run_id = cursor.lastrowid

        # Register suppliers.
        supplier_rows = [
            (name, details["priority"])
            for name, details in SUPPLIERS.items()
        ]

        execute_batches(
            cursor,
            """
            INSERT INTO suppliers (supplier_name, priority)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE priority = VALUES(priority)
            """,
            supplier_rows,
        )

        cursor.execute(
            "SELECT supplier_id, supplier_name FROM suppliers"
        )
        supplier_ids = {
            name: supplier_id
            for supplier_id, name in cursor.fetchall()
        }

        all_records = []
        seen_sources = set()
        rejected_batch = []

        # Ingest and validate.
        for supplier, details in SUPPLIERS.items():
            file_path = Path(data_dir) / details["file"]
            records = read_feed(str(file_path))

            for raw_record in records:
                input_rows += 1

                try:
                    standardized = map_supplier_record(
                        raw_record, supplier
                    )

                    is_valid, reason = validate_record(standardized)

                    if not is_valid:
                        rejected_rows += 1
                        rejected_batch.append((
                            run_id,
                            supplier,
                            json.dumps(raw_record, default=str),
                            reason,
                        ))
                        continue

                    source_key = (
                        supplier,
                        standardized["supplier_sku"],
                    )

                    if source_key in seen_sources:
                        duplicate_rows += 1
                        continue

                    seen_sources.add(source_key)

                    standardized["_raw_record"] = raw_record

                    gtin = standardized.get("gtin")

                    standardized["_identity_key"] = (
                        "GTIN:" + gtin
                        if gtin
                        else "SOURCE:"
                        + supplier
                        + ":"
                        + standardized["supplier_sku"]
                    )

                    all_records.append(standardized)
                    accepted_rows += 1

                except Exception as error:
                    rejected_rows += 1
                    rejected_batch.append((
                        run_id,
                        supplier,
                        json.dumps(raw_record, default=str),
                        str(error),
                    ))

        # Save rejected records in batches.
        execute_batches(
            cursor,
            """
            INSERT INTO rejected_records
            (run_id, supplier_name, source_data, rejection_reason)
            VALUES (%s, %s, %s, %s)
            """,
            rejected_batch,
        )

        # Group records by product identity.
        grouped = {}

        for record in all_records:
            key = record["_identity_key"]
            grouped.setdefault(key, []).append(record)

        priorities = {
            supplier: details["priority"]
            for supplier, details in SUPPLIERS.items()
        }

        product_rows = []
        source_rows = []
        product_keys = []

        # Prepare canonical products.
        for identity_key, records in grouped.items():
            canonical = build_canonical_product(
                records, priorities
            )

            product_rows.append((
                identity_key,
                canonical.get("gtin"),
                canonical.get("name"),
                canonical.get("brand"),
                canonical.get("category"),
                convert_price(canonical.get("price")),
                canonical.get("currency"),
            ))

            product_keys.append(identity_key)

        # Bulk upsert canonical products.
        execute_batches(
            cursor,
            """
            INSERT INTO products
            (identity_key, gtin, name, brand, category, price, currency)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                gtin = VALUES(gtin),
                name = VALUES(name),
                brand = VALUES(brand),
                category = VALUES(category),
                price = VALUES(price),
                currency = VALUES(currency)
            """,
            product_rows,
        )

        # Fetch product IDs in chunks.
        product_ids = {}

        for start in range(0, len(product_keys), 500):
            keys = product_keys[start:start + 500]
            placeholders = ",".join(["%s"] * len(keys))

            cursor.execute(
                f"""
                SELECT product_id, identity_key
                FROM products
                WHERE identity_key IN ({placeholders})
                """,
                tuple(keys),
            )

            for product_id, identity_key in cursor.fetchall():
                product_ids[identity_key] = product_id

        # Prepare source records and provenance.
        provenance_rows = []

        for identity_key, records in grouped.items():
            product_id = product_ids[identity_key]

            for record in records:
                supplier_id = supplier_ids[record["supplier"]]

                source_rows.append((
                    product_id,
                    supplier_id,
                    record["supplier_sku"],
                    json.dumps(record["_raw_record"], default=str),
                ))

            canonical = build_canonical_product(
                records, priorities
            )

            for attribute, details in canonical["provenance"].items():
                provenance_rows.append((
                    product_id,
                    attribute,
                    supplier_ids[details["supplier"]],
                    json.dumps(details["value"], default=str),
                ))

        # Bulk upsert supplier source records.
        execute_batches(
            cursor,
            """
            INSERT INTO product_sources
            (product_id, supplier_id, supplier_sku, source_data)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                product_id = IF(
                    NOT (product_id <=> VALUES(product_id)),
                    VALUES(product_id),
                    product_id
                ),
                source_data = IF(
                    NOT (source_data <=> VALUES(source_data)),
                    VALUES(source_data),
                    source_data
                )
            """,
            source_rows,
        )

        # Bulk upsert attribute provenance only when values change.
        execute_batches(
            cursor,
            """
            INSERT INTO attribute_provenance
            (product_id, attribute_name, supplier_id, attribute_value)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                supplier_id = IF(
                    NOT (supplier_id <=> VALUES(supplier_id)),
                    VALUES(supplier_id),
                    supplier_id
                ),
                attribute_value = IF(
                    NOT (attribute_value <=> VALUES(attribute_value)),
                    VALUES(attribute_value),
                    attribute_value
                )
            """,
            provenance_rows,
        )
        output_rows = len(product_rows)

        cursor.execute(
            """
            UPDATE pipeline_runs
            SET completed_at = CURRENT_TIMESTAMP,
                status = 'SUCCESS',
                input_rows = %s,
                accepted_rows = %s,
                rejected_rows = %s,
                duplicate_rows = %s,
                output_rows = %s
            WHERE run_id = %s
            """,
            (
                input_rows,
                accepted_rows,
                rejected_rows,
                duplicate_rows,
                output_rows,
                run_id,
            ),
        )

        connection.commit()

        return {
            "run_id": run_id,
            "status": "SUCCESS",
            "input_rows": input_rows,
            "accepted_rows": accepted_rows,
            "rejected_rows": rejected_rows,
            "duplicate_rows": duplicate_rows,
            "output_rows": output_rows,
        }

    except Exception as error:
        connection.rollback()

        if run_id is not None:
            cursor.execute(
                """
                UPDATE pipeline_runs
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'FAILED',
                    error_message = %s
                WHERE run_id = %s
                """,
                (str(error), run_id),
            )
            connection.commit()

        raise

    finally:
        cursor.close()
        connection.close()