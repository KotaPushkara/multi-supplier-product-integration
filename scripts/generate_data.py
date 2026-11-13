import argparse, csv, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)

    a_dir, b_dir, c_dir = DATA / "supplier_a", DATA / "supplier_b", DATA / "supplier_c"
    for d in (a_dir, b_dir, c_dir):
        d.mkdir(parents=True, exist_ok=True)

    a_rows, b_rows, c_rows = [], [], []
    for i in range(1, args.rows + 1):
        gtin = f"890100000{i:05d}"
        sku = f"A-{i:06d}"
        name = f"Sample Product {i}"
        brand = f"Brand {((i - 1) % 10) + 1}"
        category = ["Electronics", "Home", "Grocery"][i % 3]
        price = round(random.uniform(5, 500), 2)
        a_rows.append({"sku": sku, "product_name": name, "brand_name": brand, "ean": gtin, "dept": category, "price": price, "currency_code": "INR"})
        b_rows.append({"supplier_item": f"B-{i:06d}", "title": name.lower(), "maker": brand, "barcode": gtin, "category_name": category.lower(), "unit_price": price + 2, "currency": "INR"})
        c_rows.append({"supplierSku": f"C-{i:06d}", "description": name, "manufacturer": brand, "gtin_code": gtin, "product_type": category, "cost": price + 1, "currencyCode": "INR"})

    with (a_dir / "feed.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(a_rows[0].keys()))
        w.writeheader(); w.writerows(a_rows)
    with (b_dir / "feed.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(b_rows[0].keys()))
        w.writeheader(); w.writerows(b_rows)
    with (c_dir / "feed.json").open("w", encoding="utf-8") as f:
        json.dump({"products": c_rows}, f, indent=2)
    print(f"Generated {args.rows} records per supplier using seed={args.seed}")

if __name__ == "__main__":
    main()