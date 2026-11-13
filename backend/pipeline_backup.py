
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

        # Register suppliers and their priorities.
        for supplier, details in SUPPLIERS.items():
            cursor.execute(
                """
                INSERT INTO suppliers (supplier_name, priority)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE priority = VALUES(priority)
                """,
                (supplier, details["priority"]),
            )

        cursor.execute("SELECT supplier_id, supplier_name FROM suppliers")
        supplier_ids = {
            name: supplier_id
            for supplier_id, name in cursor.fetchall()
        }

        all_records = []
        seen_sources = set()

        # Read, map and validate supplier feeds.
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
                        cursor.execute(
                            """
                            INSERT INTO rejected_records
                            (run_id, supplier_name, source_data, rejection_reason)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                run_id,
                                supplier,
                                json.dumps(raw_record, default=str),
                                reason,
                            ),
                        )
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
                    standardized["_identity_key"] = (
                        "GTIN:" + standardized["gtin"]
                        if standardized.get("gtin")
                        else "SOURCE:"
                        + supplier
                        + ":"
                        + standardized["supplier_sku"]
                    )

                    accepted_rows += 1
                    all_records.append(standardized)

                except Exception as error:
                    rejected_rows += 1
                    cursor.execute(
                        """
                        INSERT INTO rejected_records
                        (run_id, supplier_name, source_data, rejection_reason)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            run_id,
                            supplier,
                            json.dumps(raw_record, default=str),
                            str(error),
                        ),
                    )

        # Group records that refer to the same product.
        grouped = {}
        for record in all_records:
            key = record["_identity_key"]
            grouped.setdefault(key, []).append(record)

        priorities = {
            supplier: details["priority"]
            for supplier, details in SUPPLIERS.items()
        }

        # Build and publish canonical products.
        for identity_key, records in grouped.items():
            canonical = build_canonical_product(
                records, priorities
            )

            price = convert_price(canonical.get("price"))

            cursor.execute(
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
                (
                    identity_key,
                    canonical.get("gtin"),
                    canonical.get("name"),
                    canonical.get("brand"),
                    canonical.get("category"),
                    price,
                    canonical.get("currency"),
                ),
            )

            cursor.execute(
                "SELECT product_id FROM products WHERE identity_key = %s",
                (identity_key,),
            )
            product_id = cursor.fetchone()[0]

            # Store every supplier's original record.
            for record in records:
                supplier_id = supplier_ids[record["supplier"]]

                cursor.execute(
                    """
                    INSERT INTO product_sources
                    (product_id, supplier_id, supplier_sku, source_data)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        product_id = VALUES(product_id),
                        source_data = VALUES(source_data)
                    """,
                    (
                        product_id,
                        supplier_id,
                        record["supplier_sku"],
                        json.dumps(record["_raw_record"], default=str),
                    ),
                )

            # Store the supplier that won each canonical attribute.
            for attribute, details in canonical["provenance"].items():
                supplier_id = supplier_ids[details["supplier"]]

                cursor.execute(
                    """
                    INSERT INTO attribute_provenance
                    (product_id, attribute_name, supplier_id, attribute_value)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        supplier_id = VALUES(supplier_id),
                        attribute_value = VALUES(attribute_value)
                    """,
                    (
                        product_id,
                        attribute,
                        supplier_id,
                        json.dumps(details["value"], default=str),
                    ),
                )

            output_rows += 1

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