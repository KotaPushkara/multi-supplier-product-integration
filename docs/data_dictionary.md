# Data Dictionary

This document explains the tables used in the Multi-Supplier Product Integration Pipeline and the purpose of their columns.

## 1. suppliers

Stores supplier information and their priority for conflict resolution.

| Column | Data Type | Description |
|---|---|---|
| supplier_id | INT | Unique ID for each supplier. |
| supplier_name | VARCHAR(100) | Name of the supplier. |
| priority | INT | Determines which supplier is preferred when resolving conflicts. Lower values have higher priority. |

## 2. products

Stores the final standardized product information.

| Column | Data Type | Description |
|---|---|---|
| product_id | INT | Unique ID for each product. |
| identity_key | VARCHAR(255) | Unique key used to identify a product. |
| gtin | VARCHAR(30) | Global Trade Item Number, when available. |
| name | VARCHAR(255) | Standardized product name. |
| brand | VARCHAR(255) | Product brand. |
| category | VARCHAR(255) | Standardized product category. |
| price | DECIMAL(12,2) | Product price. |
| currency | VARCHAR(10) | Currency used for the price. |
| created_at | TIMESTAMP | Date and time when the product was created. |
| updated_at | TIMESTAMP | Date and time when the product was last updated. |

## 3. product_sources

Keeps the original supplier information linked to each standardized product.

| Column | Data Type | Description |
|---|---|---|
| source_id | INT | Unique ID for each source record. |
| product_id | INT | Links the source record to a product. |
| supplier_id | INT | Identifies the supplier that provided the record. |
| supplier_sku | VARCHAR(150) | Supplier-specific product code. |
| source_data | JSON | Original supplier record. |
| created_at | TIMESTAMP | Date and time when the source record was created. |

## 4. attribute_provenance

Tracks where each final product attribute came from.

| Column | Data Type | Description |
|---|---|---|
| provenance_id | INT | Unique ID for each provenance record. |
| product_id | INT | Links the attribute to a product. |
| attribute_name | VARCHAR(100) | Name of the attribute, such as brand or price. |
| supplier_id | INT | Supplier selected as the source of the attribute. |
| attribute_value | JSON | Selected attribute value. |

## 5. rejected_records

Stores records that fail validation so they can be reviewed later.

| Column | Data Type | Description |
|---|---|---|
| reject_id | INT | Unique ID for each rejected record. |
| run_id | INT | Pipeline run in which the record was rejected. |
| supplier_name | VARCHAR(100) | Name of the supplier. |
| source_data | JSON | Original rejected record. |
| rejection_reason | TEXT | Reason why the record was rejected. |
| created_at | TIMESTAMP | Date and time when the record was rejected. |

## 6. pipeline_runs

Stores execution history and metrics for each pipeline run.

| Column | Data Type | Description |
|---|---|---|
| run_id | INT | Unique ID for each pipeline execution. |
| started_at | TIMESTAMP | Time when the pipeline started. |
| completed_at | TIMESTAMP | Time when the pipeline finished. |
| status | VARCHAR(30) | Execution status, such as RUNNING or SUCCESS. |
| input_rows | INT | Total number of records received. |
| accepted_rows | INT | Number of records accepted after validation. |
| rejected_rows | INT | Number of records rejected. |
| duplicate_rows | INT | Number of duplicate records detected. |
| output_rows | INT | Number of standardized products published. |
| error_message | TEXT | Error details if the pipeline fails. |

## Database Summary

The database contains six tables:

- `suppliers` – supplier details and priorities.
- `products` – final standardized products.
- `product_sources` – original supplier records.
- `attribute_provenance` – attribute-level source tracking.
- `rejected_records` – invalid records and rejection reasons.
- `pipeline_runs` – pipeline execution history and metrics.

Together, these tables support product integration, conflict resolution, traceability, validation, and pipeline monitoring.