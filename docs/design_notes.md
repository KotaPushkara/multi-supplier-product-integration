# Design Notes

## 1. Project Overview

The goal of this project is to combine product data from three suppliers into one common format. Since each supplier uses different column names and data formats, the pipeline standardizes the data before storing it in the database.

## 2. Data Ingestion

The pipeline reads product data from three supplier feeds:

- Supplier A – CSV file
- Supplier B – CSV file
- Supplier C – JSON file

Each supplier has a different data structure. The ingestion process reads these files and passes the records to the next stage.

## 3. Data Validation

Before processing, each record is checked for required information.

Currently, the pipeline checks whether the supplier SKU and product name are available.

Records that fail validation are stored in the `rejected_records` table along with the original data and rejection reason.

## 4. Data Transformation

Each supplier uses different column names for similar product information.

The transformation process maps these fields into a common structure.

For example:
- `product_name` from Supplier A becomes `name`.
- `title` from Supplier B becomes `name`.
- `description` from Supplier C becomes `name`.

The pipeline also normalizes text, GTIN values, and currency information.

## 5. Product Identification

The pipeline uses GTIN to identify matching products across suppliers.

When GTIN is not available, it uses the supplier name and supplier SKU to create an alternative identity key.

This helps avoid treating unrelated products as the same product.

## 6. Conflict Resolution

Different suppliers may provide different values for the same product.

The pipeline uses supplier priority to select the preferred value.

The current priority order is:

1. Supplier A
2. Supplier B
3. Supplier C

For each product attribute, the pipeline selects the value from the preferred supplier that provides that attribute. The selected source is also recorded.

## 7. Data Publishing and Traceability

After processing, the final standardized product information is stored in the `products` table.

The original supplier records are stored in `product_sources`.

The `attribute_provenance` table records which supplier provided each selected product attribute.

This makes it possible to trace the source of the final product information.

## 8. Duplicate Handling and Reruns

The pipeline checks supplier-specific product identifiers to detect duplicate records within a supplier feed.

It also uses unique product identity keys and database upsert operations to avoid creating duplicate products when the same input is processed again.

Existing source and provenance records are updated when their stored values change.

## 9. Monitoring and Performance

Each pipeline execution is recorded in the `pipeline_runs` table.

The pipeline tracks:
- Total input records
- Accepted records
- Rejected records
- Duplicate records
- Published products
- Execution status

Batch database operations are used to improve processing performance.

In the latest large test, the pipeline processed 300,000 input records and published 100,000 products successfully.

## 10. Current Limitations

- All supplier feed records are currently loaded into memory before processing.
- Supplier field mappings are maintained in the Python code.
- The current validation checks only the required supplier SKU and product name fields.

These areas can be improved in future versions.