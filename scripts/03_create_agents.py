"""
Step 3: Create Agent Bricks — Knowledge Assistant (and optional Genie + MAS).

Creates:
1. Knowledge Assistant (KA): document Q&A over flyer PDFs in UC Volume.
2. Optional: Genie Space on deals table for natural-language SQL.
3. Optional: Multi-Agent Supervisor (MAS) routing between KA and Genie.

Run locally or in a notebook. uses Databricks REST API.
Config: conf/catalog_config.py.
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


def create_ka_via_api():
    """Create or update Knowledge Assistant using Databricks REST API."""
    try:
        from databricks.sdk import WorkspaceClient
        import requests
        
        w = WorkspaceClient()
        host = w.config.host
        
        # Get token from notebook context (works in serverless with runtime auth)
        try:
            token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
        except:
            # Fallback to SDK token if available
            token = w.config.token
            if not token:
                raise ValueError("Could not get authentication token. Make sure you're running in a Databricks notebook.")
        
        # API endpoint for creating agents
        url = f"{host}/api/2.0/agent-framework/agents"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": KA_NAME,
            "description": KA_DESCRIPTION,
            "agent_type": "KNOWLEDGE_ASSISTANT",
            "knowledge_sources": [
                {
                    "type": "UC_VOLUME",
                    "volume_path": VOLUME_PATH_FLYER_DOCS
                }
            ],
            "instructions": KA_INSTRUCTIONS,
            "model": "databricks-meta-llama-3-1-70b-instruct",  # Default model
            "add_examples_from_volume": True
        }
        
        print(f"Creating Knowledge Assistant: {KA_NAME}")
        print(f"  Volume: {VOLUME_PATH_FLYER_DOCS}")
        print(f"  Description: {KA_DESCRIPTION}")
        print()
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print("✓ Knowledge Assistant created successfully!")
            print(f"  Agent ID: {result.get('agent_id', 'N/A')}")
            print(f"  Endpoint: {result.get('endpoint_name', 'N/A')}")
            return result
        elif response.status_code == 409:
            print("⚠ Knowledge Assistant already exists. Updating...")
            # Try to update instead
            update_url = f"{host}/api/2.0/agent-framework/agents/{KA_NAME}"
            response = requests.patch(update_url, headers=headers, json=payload)
            if response.status_code == 200:
                print("✓ Knowledge Assistant updated successfully!")
                return response.json()
            else:
                print(f"✗ Update failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
        else:
            print(f"✗ Failed to create Knowledge Assistant: {response.status_code}")
            print(f"  Response: {response.text}")
            print()
            print("Alternative: Create via Databricks UI:")
            print("  1. Go to Agents in the left navigation")
            print("  2. Click 'Build' on Knowledge Assistant tile")
            print(f"  3. Name: {KA_NAME}")
            print(f"  4. Knowledge source: {VOLUME_PATH_FLYER_DOCS}")
            print(f"  5. Description: {KA_DESCRIPTION}")
            print(f"  6. Instructions: {KA_INSTRUCTIONS}")
            return None
            
    except ImportError:
        print("Install databricks-sdk: %pip install databricks-sdk")
        return None
    except Exception as e:
        print(f"Error creating Knowledge Assistant: {e}")
        print()
        print("Alternative: Create via Databricks UI:")
        print("  1. Go to Agents in the left navigation")
        print("  2. Click 'Build' on Knowledge Assistant tile")
        print(f"  3. Name: {KA_NAME}")
        print(f"  4. Knowledge source: {VOLUME_PATH_FLYER_DOCS}")
        print(f"  5. Description: {KA_DESCRIPTION}")
        print(f"  6. Instructions: {KA_INSTRUCTIONS}")
        return None


def main() -> None:
    print("=" * 70)
    print("Step 3: Create Agent Bricks")
    print("=" * 70)
    print()
    
    # Create Knowledge Assistant
    result = create_ka_via_api()
    
    print()
    print("-" * 70)
    print("Optional: Create Genie Space on deals table for SQL-style questions:")
    print(f"  Tables: {FULL_TABLE_DEALS}")
    print(f"  Genie name: {GENIE_NAME}")
    print()
    print("Optional: Create MAS to route between KA (flyer Q&A) and Genie (deals data):")
    print(f"  MAS name: {MAS_NAME}")
    print("-" * 70)
    print()
    
    if result:
        print("✓ Step 3 complete! Next: Run 04_provision_agents.py to wait for endpoint to be ready.")
    else:
        print("⚠ Step 3 incomplete. Create the agent via UI, then run 04_provision_agents.py")


if __name__ == "__main__":
    main()
