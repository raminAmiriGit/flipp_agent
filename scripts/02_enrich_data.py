"""
Step 2a: Enrich data — build Delta tables from raw parquet.

Reads from Unity Catalog Volume (raw_data/deals, raw_data/retailers),
writes Delta tables in the same catalog/schema for Genie and reporting.

Run on a Databricks cluster. Config: conf/catalog_config.py.
"""
from __future__ import annotations

import sys
from pathlib import Path


from pathlib import Path
import sys

# Add project root for config (Databricks notebook-safe)
SCRIPT_DIR = Path.cwd()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
PROJECT_ROOT = SCRIPT_DIR.parent


# PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from conf.catalog_config import (
    CATALOG,
    SCHEMA,
    VOLUME_RAW,
    VOLUME_FLYER_DOCS,
    VOLUME_PATH_RAW,
    FULL_TABLE_DEALS,
    FULL_TABLE_RETAILERS,
    FULL_TABLE_STORES,
    FULL_TABLE_TRADE_AREAS,
    FULL_TABLE_PRODUCTS,
    FULL_TABLE_CATEGORIES,
    FULL_TABLE_PRODUCT_RETAILER_MAP,
    FULL_TABLE_USERS,
    FULL_TABLE_SESSIONS,
    FULL_TABLE_EVENTS,
    FULL_TABLE_STORE_VISITS,
    FULL_TABLE_CONVERSION_PROXIES,
)


def main() -> None:
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()

    print("Step 2a: Enrich data — Delta tables from raw parquet")

    # Ensure flyer_docs volume exists for Step 2b uploads
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME_FLYER_DOCS}")
    print(f"  Volume {CATALOG}.{SCHEMA}.{VOLUME_FLYER_DOCS} ready for flyer PDFs.")

    # Dimension and fact tables from raw parquet (see prompts/cursor_generatedata.md)
    tables = [
        ("retailers", FULL_TABLE_RETAILERS),
        ("stores", FULL_TABLE_STORES),
        ("trade_areas", FULL_TABLE_TRADE_AREAS),
        ("categories", FULL_TABLE_CATEGORIES),
        ("products", FULL_TABLE_PRODUCTS),
        ("product_retailer_map", FULL_TABLE_PRODUCT_RETAILER_MAP),
        ("users", FULL_TABLE_USERS),
        ("sessions", FULL_TABLE_SESSIONS),
        ("events", FULL_TABLE_EVENTS),
        ("store_visits", FULL_TABLE_STORE_VISITS),
        ("conversion_proxies", FULL_TABLE_CONVERSION_PROXIES),
        ("deals", FULL_TABLE_DEALS),
    ]
    for path_suffix, full_table in tables:
        try:
            df = spark.read.parquet(f"{VOLUME_PATH_RAW}/{path_suffix}")
            df.write.mode("overwrite").saveAsTable(full_table)
            print(f"  Wrote table {full_table}")
        except Exception as e:
            print(f"  Skip {full_table}: {e}")

    print("\nStep 2a done. Next: run 02_upload_flyer_docs.py (local) to upload PDFs to Volume, then Step 3.")


if __name__ == "__main__":
    main()
