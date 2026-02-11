"""
Step 3: Create Agent Bricks — Knowledge Assistant, Genie, and (optional) MAS.

1. Knowledge Assistant (KA): document Q&A over flyer PDFs in UC Volume.
   - PDFs and companion JSON files live in flyer_docs Volume.
   - JSON files used as examples: each must have "question" and "guideline" keys
     (human-labeled examples). With add_examples_from_volume=true, the KA
     auto-ingests these to improve accuracy. See generate_flyer_pdfs.py.

2. Genie Space: natural-language SQL over structured tables (deals, retailers,
   stores, products, etc.). Table list in config.

3. Multi-Agent Supervisor (MAS): routes between KA and Genie. Requires
   Agent Bricks preview enabled in the workspace.

Config: conf/catalog_config.py. Use MCP: create_or_update_ka, create_or_update_genie, create_or_update_mas.
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
print(PROJECT_ROOT)
from conf.catalog_config import (
    CATALOG,
    SCHEMA,
    VOLUME_PATH_FLYER_DOCS,
    FULL_TABLE_DEALS,
    FULL_TABLE_RETAILERS,
    FULL_TABLE_STORES,
    FULL_TABLE_TRADE_AREAS,
    FULL_TABLE_PRODUCTS,
    FULL_TABLE_CATEGORIES,
    FULL_TABLE_PRODUCT_RETAILER_MAP,
    FULL_TABLE_STORE_VISITS,
    FULL_TABLE_CONVERSION_PROXIES,
    KA_NAME,
    GENIE_NAME,
    MAS_NAME,
)

# All structured tables for Genie (per cursor_agent.md)
GENIE_TABLE_IDENTIFIERS = [
    FULL_TABLE_DEALS,
    FULL_TABLE_RETAILERS,
    FULL_TABLE_STORES,
    FULL_TABLE_TRADE_AREAS,
    FULL_TABLE_PRODUCTS,
    FULL_TABLE_CATEGORIES,
    FULL_TABLE_PRODUCT_RETAILER_MAP,
    FULL_TABLE_STORE_VISITS,
    FULL_TABLE_CONVERSION_PROXIES,
]

# -----------------------------------------------------------------------------
# KNOWLEDGE ASSISTANT
# -----------------------------------------------------------------------------
KA_DESCRIPTION = (
    "Conversational deal-finding chatbot grounded in Flipp flyer and promotional content. "
    "Answers natural-language questions about current deals and recommends products with citations to source flyers."
)
KA_INSTRUCTIONS = (
    "You are a helpful Flipp deal-finder assistant. "
    "Answer only from the provided flyer documents. "
    "When recommending deals, always cite the source (retailer name and validity dates). "
    "If the user asks about events (e.g. barbecue, party), suggest relevant categories: meat, buns, condiments, snacks, drinks. "
    "Keep answers concise and list specific products with prices when available."
)


def create_ka_via_sdk():
    """Create or update Knowledge Assistant using Databricks SDK (Agent Bricks API)."""
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.agents import CreateKnowledgeAssistantRequest
    except ImportError:
        print("Install databricks-sdk. For Agent Bricks, use MCP create_or_update_ka with:")
        print(f"  name: {KA_NAME}")
        print(f"  volume_path: {VOLUME_PATH_FLYER_DOCS}")
        print(f"  description: {KA_DESCRIPTION}")
        print(f"  instructions: {KA_INSTRUCTIONS}")
        print("  add_examples_from_volume: true")
        return

    w = WorkspaceClient()
    # Agent Bricks KA creation may be via a different API surface; if not available, print MCP instructions
    print("Create the Knowledge Assistant via Databricks UI or MCP tool create_or_update_ka:")
    print(f"  name: {KA_NAME}")
    print(f"  volume_path: {VOLUME_PATH_FLYER_DOCS}")
    print(f"  description: {KA_DESCRIPTION}")
    print(f"  instructions: {KA_INSTRUCTIONS}")
    print("  add_examples_from_volume: true")


def main() -> None:
    print("Step 3: Create Agent Bricks")
    print(f"  KA name: {KA_NAME}")
    print(f"  Volume: {VOLUME_PATH_FLYER_DOCS}")
    print()
    create_ka_via_sdk()
    print()
    print("Genie Space (structured data): use create_or_update_genie with:")
    print(f"  display_name: {GENIE_NAME}")
    print(f"  table_identifiers: {GENIE_TABLE_IDENTIFIERS}")
    print()
    print("MAS (optional, requires Agent Bricks preview): use create_or_update_mas with")
    print(f"  name: {MAS_NAME}, agents: [KA by ka_tile_id, Genie by genie_space_id]")
    print("\nStep 3: Use MCP create_or_update_ka (add_examples_from_volume=true for JSON examples), create_or_update_genie, create_or_update_mas.")


if __name__ == "__main__":
    main()
