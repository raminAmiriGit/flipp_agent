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
)


def main() -> None:
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()

    print("Step 2a: Enrich data — Delta tables from raw parquet")

    # Ensure flyer_docs volume exists for Step 2b uploads
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME_FLYER_DOCS}")
    print(f"  Volume {CATALOG}.{SCHEMA}.{VOLUME_FLYER_DOCS} ready for flyer PDFs.")

    # Retailers dimension
    retailers_df = spark.read.parquet(f"{VOLUME_PATH_RAW}/retailers")
    retailers_df.write.mode("overwrite").saveAsTable(FULL_TABLE_RETAILERS)
    print(f"  Wrote table {FULL_TABLE_RETAILERS}")

    # Deals fact (with validity and category for filtering)
    deals_df = spark.read.parquet(f"{VOLUME_PATH_RAW}/deals")
    deals_df.write.mode("overwrite").saveAsTable(FULL_TABLE_DEALS)
    print(f"  Wrote table {FULL_TABLE_DEALS}")

    print("\nStep 2a done. Next: run 02_upload_flyer_docs.py (local) to upload PDFs to Volume, then Step 3.")


if __name__ == "__main__":
    main()
