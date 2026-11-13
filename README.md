# Multi-Supplier Product Data Integration Pipeline

## About the Project

This project brings product data from multiple suppliers into one common format.

Each supplier provides product information in a different structure and may use different names for the same attributes. This makes it difficult to combine and maintain product data.

To solve this, I built a pipeline that reads supplier feeds, validates records, standardizes product information, handles conflicting values, and stores the final products in a MySQL database.

The project also includes a dashboard to monitor pipeline runs, view published products, and check rejected records.

## Project Architecture

The project is organized into the following parts:

- **Frontend:** A simple dashboard built with HTML, CSS, and JavaScript.
- **Backend:** Python and FastAPI handle the APIs and data pipeline.
- **Database:** MySQL stores products, supplier information, pipeline history, rejected records, and attribute provenance.
- **Data:** Contains sample product feeds from three suppliers.
- **Scripts:** Generates synthetic supplier data for testing.
- **Tests:** Contains automated tests for the main pipeline components.
- **Docs:** Stores project documentation and design notes.

## Technologies Used

- Python
- FastAPI
- MySQL
- HTML, CSS, JavaScript
- Pandas
- Pytest

## How the Pipeline Works

The pipeline follows these steps:

1. Reads product feeds from three suppliers in CSV and JSON formats.
2. Maps different supplier fields into a common product structure.
3. Validates records and identifies missing or invalid information.
4. Keeps invalid records separately with their rejection reasons.
5. Standardizes product attributes such as names, brands, categories, and GTINs.
6. Identifies matching products and resolves conflicting values using supplier priority.
7. Publishes the final product information into MySQL.
8. Tracks which supplier provided each product attribute.
9. Stores pipeline execution details and processing metrics.

## Running the Project

### 1. Set up the environment

Open PowerShell in the project directory.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure the database

Make sure MySQL Server is running and create the project database:

```sql
CREATE DATABASE multi_supplier_db;
```

Configure your local database credentials in the `.env` file using `.env.example` as a reference.

Do not upload your actual `.env` file or database password when sharing the project.

### 3. Start the application

```powershell
uvicorn backend.main:app --reload
```

### 4. Open the application

- Dashboard: http://127.0.0.1:8000/dashboard
- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

The dashboard displays product counts, supplier records, attribute provenance, pipeline execution history, and rejected records.

## Generating Test Data

To generate 100,000 records for each supplier, run:

```powershell
python scripts/generate_data.py --rows 100000
```

The generated dataset contains 300,000 records across the three suppliers.

## Running Automated Tests

Run the test suite using:

```powershell
pytest -q
```

The current test suite contains 10 tests covering validation, data transformation, supplier mapping, conflict resolution, and provenance.

## Current Performance Results

The pipeline was tested with 300,000 input records.

| Metric | Result |
|---|---:|
| Total input records | 300,000 |
| Accepted records | 300,000 |
| Rejected records | 0 |
| Duplicate records | 0 |
| Published products | 100,000 |
| Automated tests passed | 10 |

The latest successful large-data execution completed in approximately 92 seconds on the development machine.

These results are from the generated test dataset and may vary depending on the system.

## Database Tables

The project uses six main MySQL tables:

- `suppliers` – stores supplier information.
- `pipeline_runs` – stores pipeline execution details.
- `products` – stores standardized product information.
- `product_sources` – links products to their supplier records.
- `attribute_provenance` – tracks the source of individual product attributes.
- `rejected_records` – stores invalid records and their rejection reasons.

## Future Improvements

Some areas that can be improved further include:

- Adding pagination and search to the dashboard.
- Improving pipeline processing speed for larger datasets.
- Adding more validation rules for supplier-specific data.
- Supporting additional supplier feed formats.
- Improving automated tests for failure and retry scenarios.

---

**Project:** Multi-Supplier Product Data Integration Pipeline  
**Purpose:** Standardize, validate, combine, and publish product data from multiple suppliers.