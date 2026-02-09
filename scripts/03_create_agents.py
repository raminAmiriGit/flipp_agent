"""
Step 3: Create Agent Bricks — Knowledge Assistant (and optional Genie + MAS).

Creates:
1. Knowledge Assistant (KA): document Q&A over flyer PDFs in UC Volume.
2. Optional: Genie Space on deals table for natural-language SQL.
3. Optional: Multi-Agent Supervisor (MAS) routing between KA and Genie.

Run locally or in a notebook. Uses Databricks MCP tools or SDK.
Config: conf/catalog_config.py.

To run via MCP (Cursor/Agent): use create_or_update_ka with the volume path below.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from conf.catalog_config import (
    CATALOG,
    SCHEMA,
    VOLUME_PATH_FLYER_DOCS,
    FULL_TABLE_DEALS,
    KA_NAME,
    GENIE_NAME,
    MAS_NAME,
)

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
    print("Optional: Create Genie Space on deals table for SQL-style questions:")
    print(f"  Tables: {FULL_TABLE_DEALS}")
    print(f"  Genie name: {GENIE_NAME}")
    print()
    print("Optional: Create MAS to route between KA (flyer Q&A) and Genie (deals data):")
    print(f"  MAS name: {MAS_NAME}")
    print("\nStep 3: Use MCP create_or_update_ka (and create_or_update_genie / create_or_update_mas) or Databricks UI to create the agents.")


if __name__ == "__main__":
    main()
