# Multi-Supplier Product Data Integration Pipeline

## About the Project

This project combines product data from multiple suppliers into one common format.

Each supplier provides product information in a different structure and uses different names for similar attributes. This makes it difficult to manage and compare product information.

To solve this problem, I developed a pipeline that reads supplier feeds, validates records, standardizes product details, handles conflicting values, and stores the final product information in a MySQL database.

The project also includes a web dashboard to monitor pipeline runs, view published products, and check rejected records.

## Project Architecture

The project is divided into the following components:

- **Frontend:** A dashboard built using HTML, CSS, and JavaScript.
- **Backend:** Python and FastAPI handle the data pipeline and API requests.
- **Database:** MySQL stores product information, supplier records, pipeline history, rejected records, and attribute provenance.
- **Data:** Contains product feeds from three different suppliers.
- **Scripts:** Generates synthetic supplier data for testing.
- **Tests:** Contains automated tests for the main pipeline components.
- **Docs:** Includes architecture, data dictionary, and design documentation.

## Technologies Used

- Python
- FastAPI
- MySQL
- HTML, CSS, and JavaScript
- Pytest

## How the Pipeline Works

The pipeline processes supplier data through the following steps:

1. Reads product feeds from three suppliers in CSV and JSON formats.
2. Maps supplier-specific fields into a common product structure.
3. Validates records and identifies missing or invalid information.
4. Stores invalid records separately along with their rejection reasons.
5. Standardizes product attributes such as names, brands, categories, and GTINs.
6. Identifies matching products and resolves conflicting values using supplier priority.
7. Saves the final product information in MySQL.
8. Tracks the supplier responsible for each product attribute.
9. Records pipeline execution details and processing metrics.

## Running the Project

### 1. Set Up the Environment

Open PowerShell in the project directory and run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure the Database

Make sure MySQL Server is running and create the project database:

```sql
CREATE DATABASE multi_supplier_db;
```

Create a `.env` file using `.env.example` as a reference and add your local database credentials.

Do not upload your actual `.env` file or database password to GitHub.

### 3. Start the Application

Run the following command:

```powershell
uvicorn backend.main:app --reload
```

### 4. Open the Application

Once the server is running, open these URLs in your browser:

- **Dashboard:** http://127.0.0.1:8000/dashboard
- **API Documentation:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health

The dashboard displays product counts, supplier records, attribute provenance, pipeline execution history, and rejected records.

## Generating Test Data

To generate 100,000 records for each supplier, run:

```powershell
python scripts/generate_data.py --rows 100000
```

This generates a total of 300,000 records across the three suppliers.

## Running Automated Tests

Run the tests using:

```powershell
python -m pytest -q
```

The current test suite contains 10 tests covering validation, data transformation, supplier mapping, conflict resolution, and attribute provenance.

## Performance Results

The pipeline was tested using 300,000 input records.

| Metric | Result |
|---|---:|
| Total input records | 300,000 |
| Accepted records | 300,000 |
| Rejected records | 0 |
| Duplicate records | 0 |
| Published products | 100,000 |
| Automated tests passed | 10 |

The latest successful execution with 300,000 records took approximately 92 seconds on the development machine. Actual execution time may vary depending on the system.

## Database Tables

The project uses six main MySQL tables:

- `suppliers` - Stores supplier information and priorities.
- `pipeline_runs` - Stores pipeline execution details and metrics.
- `products` - Stores standardized product information.
- `product_sources` - Links published products to their original supplier records.
- `attribute_provenance` - Tracks the source of individual product attributes.
- `rejected_records` - Stores invalid records and their rejection reasons.

## Future Improvements

Some areas that could be improved further include:

- Adding pagination and search options to the dashboard.
- Improving processing speed for larger datasets.
- Adding more supplier-specific validation rules.
- Supporting additional supplier feed formats.
- Expanding automated tests for failure and retry scenarios.

---

**Project:** Multi-Supplier Product Data Integration Pipeline

**Purpose:** To validate, standardize, combine, and publish product data from multiple suppliers.