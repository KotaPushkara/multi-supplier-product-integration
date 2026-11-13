from pathlib import Path
import csv
import json

def read_feed(path: str):
    """Read CSV or JSON feed and return a list of dictionaries."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        with file_path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    if suffix == ".json":
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("products", [])
        if not isinstance(data, list):
            raise ValueError("JSON feed must contain a list of products")
        return data
    raise ValueError(f"Unsupported feed format: {suffix}")