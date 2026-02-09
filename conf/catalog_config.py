"""
Central configuration for Flipp Deal-Finder Agent (catalog, schema, volumes, agent names).
Edit these for your workspace or set via environment variables.
"""
import os

# Unity Catalog
CATALOG = os.environ.get("FLIPP_CATALOG", "flipp_demo")
SCHEMA = os.environ.get("FLIPP_SCHEMA", "deal_finder")

# Volume names
VOLUME_RAW = "raw_data"
VOLUME_FLYER_DOCS = "flyer_docs"

# Paths
VOLUME_PATH_RAW = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME_RAW}"
VOLUME_PATH_FLYER_DOCS = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME_FLYER_DOCS}"

# Table names (enriched layer)
TABLE_DEALS = "deals"
TABLE_RETAILERS = "retailers"
FULL_TABLE_DEALS = f"{CATALOG}.{SCHEMA}.{TABLE_DEALS}"
FULL_TABLE_RETAILERS = f"{CATALOG}.{SCHEMA}.{TABLE_RETAILERS}"

# Agent Bricks
KA_NAME = "Flipp_Deal_Finder"
GENIE_NAME = "Flipp_Deals_Explorer"
MAS_NAME = "Flipp_Deal_Supervisor"

# Model serving (KA endpoint name is created by Agent Bricks; app discovers by KA name/tile_id)
# Use find_ka_by_name to get endpoint name at runtime if needed.
