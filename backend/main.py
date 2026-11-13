from fastapi import FastAPI, HTTPException, Query
from .database import get_connection
from .pipeline import run_pipeline

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Multi-Supplier Product Integration API",
    version="1.0.0",
    description="API for multi-supplier product data integration"
)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)

@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/")
def root():
    return {
        "message": "Multi-Supplier Product Data Integration Pipeline",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "multi-supplier-pipeline"
    }


@app.post("/run")
def execute_pipeline():
    try:
        return run_pipeline()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/products")
def get_products(limit: int = Query(default=100, ge=1, le=1000)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT product_id, identity_key, gtin, name,
                   brand, category, price, currency
            FROM products
            ORDER BY product_id
            LIMIT %s
            """,
            (limit,)
        )
        return {"products": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()


@app.get("/runs")
def get_pipeline_runs(limit: int = Query(default=20, ge=1, le=100)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT run_id, started_at, completed_at, status,
                   input_rows, accepted_rows, rejected_rows,
                   duplicate_rows, output_rows, error_message
            FROM pipeline_runs
            ORDER BY run_id DESC
            LIMIT %s
            """,
            (limit,)
        )
        return {"runs": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()


@app.get("/metrics")
def get_metrics():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        queries = {
            "products": "SELECT COUNT(*) AS total FROM products",
            "sources": "SELECT COUNT(*) AS total FROM product_sources",
            "provenance": "SELECT COUNT(*) AS total FROM attribute_provenance",
            "rejected": "SELECT COUNT(*) AS total FROM rejected_records",
        }

        metrics = {}

        for key, query in queries.items():
            cursor.execute(query)
            metrics[key] = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total_runs,
                   SUM(status = 'SUCCESS') AS successful_runs,
                   SUM(status = 'FAILED') AS failed_runs
            FROM pipeline_runs
            """
        )
        metrics.update(cursor.fetchone())

        return metrics
    finally:
        cursor.close()
        connection.close()
@app.get("/rejected")
def get_rejected_records(limit: int = Query(default=100, ge=1, le=1000)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT reject_id, run_id, supplier_name,
                   source_data, rejection_reason, created_at
            FROM rejected_records
            ORDER BY reject_id DESC
            LIMIT %s
            """,
            (limit,)
        )
        return {"rejected_records": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()
