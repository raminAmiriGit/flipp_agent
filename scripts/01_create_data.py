"""
Step 1: Create data for Flipp Deal-Finder Agent.

Generates:
1. Synthetic deals catalog (and retailers) as parquet in Unity Catalog Volume.
2. Assumes flyer PDFs (and JSON examples) are produced by generate_flyer_pdfs.py
   and live under data/flyers/; they are uploaded in Step 2.

Run on a Databricks cluster (Spark available). Config: conf/catalog_config.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root for config
# PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Add project root for config (Databricks notebook-safe)
from pathlib import Path
import sys

# Add project root for config (Databricks notebook-safe)
SCRIPT_DIR = Path.cwd()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
PROJECT_ROOT = SCRIPT_DIR.parent

from conf.catalog_config import CATALOG, SCHEMA, VOLUME_RAW, VOLUME_PATH_RAW

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
N_DEALS = 5000
N_RETAILERS = 20
# Date range: next 2 weeks from "today" for validity
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pyspark.sql import SparkSession

SEED = 42
np.random.seed(SEED)

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=14)
START_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Synthetic retailers (Flipp-style)
RETAILER_NAMES = [
    "Metro Plus", "FreshCo Weekly", "No Frills", "Walmart", "Kroger", "Lowe's", "Home Depot",
    "Loblaws", "Sobeys", "Food Basics", "Giant Tiger", "Canadian Tire", "Costco", "Real Canadian Superstore",
    "Shoppers Drug Mart", "Rexall", "Dollarama", "Target", "Whole Foods", "Save-On-Foods",
]

# Product categories for deals
CATEGORIES = [
    "Meat & Poultry", "Frozen", "Bakery", "Deli", "Pantry", "Snacks", "Dairy & Deli",
    "Beverages", "Produce", "Dairy", "Household", "Personal Care", "Baby", "Pet",
]

# Example product names (expand in real use)
PRODUCT_NAMES = [
    "Chicken Wings", "Ground Beef", "Pork Chops", "Marinated Chicken", "Beef Burger",
    "French Fries", "Ice Cream", "Pizza", "Appetizers", "Frozen Vegetables",
    "Sliced Bread", "Buns", "Bagels", "Croissants", "Muffins",
    "Frankfurters", "Deli Ham", "Cheese Slices", "Hummus", "Dips",
    "Pasta", "Rice", "Cereal", "Condiments", "Canned Soup", "Olive Oil",
    "Chips", "Crackers", "Cookies", "Nuts", "Granola Bars",
    "Milk", "Yogurt", "Butter", "Eggs", "Cream Cheese",
    "Soft Drinks", "Juice", "Water", "Coffee", "Tea",
    "Apples", "Bananas", "Salad Kit", "Tomatoes", "Potatoes", "Onions",
    "Laundry Detergent", "Paper Towels", "Dish Soap", "Trash Bags",
    "Shampoo", "Soap", "Toothpaste", "Deodorant", "Sunscreen",
]


def get_spark() -> SparkSession:
    return SparkSession.builder.getOrCreate()


def create_infrastructure(spark: SparkSession) -> None:
    # Check if catalog exists, if not provide helpful error
    catalogs = [row.catalog for row in spark.sql("SHOW CATALOGS").collect()]
    if CATALOG not in catalogs:
        raise ValueError(
            f"Catalog '{CATALOG}' does not exist. Please create it first using the Databricks UI "
            f"(Catalog > Create Catalog) or SQL: CREATE CATALOG {CATALOG};"
        )
    
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME_RAW}")


def generate_retailers(spark: SparkSession) -> pd.DataFrame:
    """Generate retailer dimension (raw)."""
    rows = []
    for i, name in enumerate(RETAILER_NAMES[:N_RETAILERS]):
        rows.append({
            "retailer_id": f"R{i+1:04d}",
            "retailer_name": name,
            "region": np.random.choice(["North", "South", "East", "West"], p=[0.3, 0.25, 0.25, 0.2]),
        })
    return pd.DataFrame(rows)


def generate_deals(spark: SparkSession, retailers_pdf: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic deals (one row per deal)."""
    retailer_ids = retailers_pdf["retailer_id"].tolist()
    retailer_names = retailers_pdf.set_index("retailer_id")["retailer_name"].to_dict()

    deals = []
    for i in range(N_DEALS):
        rid = np.random.choice(retailer_ids)
        rname = retailer_names[rid]
        category = np.random.choice(CATEGORIES)
        product = np.random.choice(PRODUCT_NAMES)
        brand = np.random.choice(["Store Brand", "Name Brand", "Premium", "Adonis", "Selection", "Irresistible", "No Name"], p=[0.35, 0.25, 0.1, 0.1, 0.1, 0.05, 0.05])
        was_price = round(float(np.random.lognormal(2.5, 0.8)), 2)
        discount_pct = np.random.choice([5, 10, 15, 20, 25, 30, 40, 50], p=[0.15, 0.2, 0.2, 0.15, 0.12, 0.1, 0.05, 0.03])
        current_price = round(was_price * (1 - discount_pct / 100), 2)
        valid_days = np.random.randint(0, 13)
        valid_from = (START_DATE + timedelta(days=valid_days)).strftime("%Y-%m-%d")
        valid_to = (START_DATE + timedelta(days=valid_days + 6)).strftime("%Y-%m-%d")
        unit = np.random.choice(["each", "per lb", "per kg", "2/$", "4/$", "bunch", "bag"], p=[0.4, 0.15, 0.1, 0.15, 0.05, 0.1, 0.05])

        deals.append({
            "deal_id": f"D{i+1:06d}",
            "retailer_id": rid,
            "retailer_name": rname,
            "product_name": product,
            "brand": brand,
            "category": category,
            "current_price": current_price,
            "was_price": was_price,
            "discount_pct": discount_pct,
            "unit": unit,
            "valid_from": valid_from,
            "valid_to": valid_to,
        })

    return pd.DataFrame(deals)


def main() -> None:
    spark = get_spark()
    print(f"Step 1: Create data → catalog={CATALOG}, schema={SCHEMA}, volume={VOLUME_RAW}")

    create_infrastructure(spark)
    print("  Created catalog / schema / volume (if not exists).")

    retailers_pdf = generate_retailers(spark)
    deals_pdf = generate_deals(spark, retailers_pdf)
    print(f"  Generated {len(retailers_pdf):,} retailers, {len(deals_pdf):,} deals.")

    spark.createDataFrame(retailers_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/retailers")
    spark.createDataFrame(deals_pdf).write.mode("overwrite").parquet(f"{VOLUME_PATH_RAW}/deals")
    print(f"  Wrote parquet to {VOLUME_PATH_RAW}/retailers and .../deals")

    print("\nStep 1 done. Next: run generate_flyer_pdfs.py (local) for PDFs + JSON, then Step 2 (enrich + upload).")


if __name__ == "__main__":
    main()
