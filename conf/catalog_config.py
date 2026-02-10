"""
Central configuration for Flipp Deal-Finder Agent (catalog, schema, volumes, agent names).
Edit these for your workspace or set via environment variables.
"""
import os

# Unity Catalog
CATALOG = os.environ.get("FLIPP_CATALOG", "ramin_serverless_aws_catalog")
SCHEMA = os.environ.get("FLIPP_SCHEMA", "deal_finder")

# Volume names
VOLUME_RAW = "raw_data"
VOLUME_FLYER_DOCS = "flyer_docs"

# Paths
VOLUME_PATH_RAW = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME_RAW}"
VOLUME_PATH_FLYER_DOCS = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME_FLYER_DOCS}"

# Table names (enriched layer) — see prompts/cursor_generatedata.md
TABLE_DEALS = "deals"
TABLE_RETAILERS = "retailers"
TABLE_STORES = "stores"
TABLE_TRADE_AREAS = "trade_areas"
TABLE_PRODUCTS = "products"
TABLE_CATEGORIES = "categories"
TABLE_PRODUCT_RETAILER_MAP = "product_retailer_map"
TABLE_USERS = "users"
TABLE_SESSIONS = "sessions"
TABLE_EVENTS = "events"
TABLE_STORE_VISITS = "store_visits"
TABLE_CONVERSION_PROXIES = "conversion_proxies"

FULL_TABLE_DEALS = f"{CATALOG}.{SCHEMA}.{TABLE_DEALS}"
FULL_TABLE_RETAILERS = f"{CATALOG}.{SCHEMA}.{TABLE_RETAILERS}"
FULL_TABLE_STORES = f"{CATALOG}.{SCHEMA}.{TABLE_STORES}"
FULL_TABLE_TRADE_AREAS = f"{CATALOG}.{SCHEMA}.{TABLE_TRADE_AREAS}"
FULL_TABLE_PRODUCTS = f"{CATALOG}.{SCHEMA}.{TABLE_PRODUCTS}"
FULL_TABLE_CATEGORIES = f"{CATALOG}.{SCHEMA}.{TABLE_CATEGORIES}"
FULL_TABLE_PRODUCT_RETAILER_MAP = f"{CATALOG}.{SCHEMA}.{TABLE_PRODUCT_RETAILER_MAP}"
FULL_TABLE_USERS = f"{CATALOG}.{SCHEMA}.{TABLE_USERS}"
FULL_TABLE_SESSIONS = f"{CATALOG}.{SCHEMA}.{TABLE_SESSIONS}"
FULL_TABLE_EVENTS = f"{CATALOG}.{SCHEMA}.{TABLE_EVENTS}"
FULL_TABLE_STORE_VISITS = f"{CATALOG}.{SCHEMA}.{TABLE_STORE_VISITS}"
FULL_TABLE_CONVERSION_PROXIES = f"{CATALOG}.{SCHEMA}.{TABLE_CONVERSION_PROXIES}"

# Agent Bricks
KA_NAME = "flipp-knowledge-assistant-2026-02-10"
GENIE_NAME = "Flipp_Deals_Explorer"
MAS_NAME = "Flipp_Deal_Supervisor"

# Model serving (KA endpoint name is created by Agent Bricks; app discovers by KA name/tile_id)
# Use find_ka_by_name to get endpoint name at runtime if needed.
