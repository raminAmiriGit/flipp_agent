"""
Step 4: Run / provision agents — wait for KA endpoint and optionally add examples.

- Poll Knowledge Assistant endpoint until status is ONLINE.
- KA with add_examples_from_volume=true will ingest JSON question/guideline files from the volume.

Run locally or in a notebook. Uses Databricks SDK.
Config: conf/catalog_config.py.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root for config (Databricks notebook-safe)
SCRIPT_DIR = Path.cwd()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
PROJECT_ROOT = SCRIPT_DIR.parent

from conf.catalog_config import KA_NAME


def get_ka_endpoint_name():
    """Get the serving endpoint name for the Knowledge Assistant."""
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
        
        # Get agent details
        url = f"{host}/api/2.0/agent-framework/agents/{KA_NAME}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            agent = response.json()
            endpoint_name = agent.get("endpoint_name")
            return endpoint_name
        else:
            print(f"Could not find agent {KA_NAME}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting agent endpoint: {e}")
        return None


def wait_for_online(endpoint_name: str, timeout_sec: int = 600, poll_sec: int = 30) -> bool:
    """Poll serving endpoint until READY or timeout."""
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        deadline = time.time() + timeout_sec
        
        print(f"Waiting for endpoint {endpoint_name} to be READY...")
        print(f"  Timeout: {timeout_sec}s, polling every {poll_sec}s")
        print()
        
        while time.time() < deadline:
            try:
                ep = w.serving_endpoints.get(name=endpoint_name)
                state = ep.state.config_update if hasattr(ep.state, 'config_update') else None
                ready_state = ep.state.ready if hasattr(ep.state, 'ready') else None
                
                print(f"  Status: config_update={state}, ready={ready_state}")
                
                if ready_state == "READY" or str(state).upper() == "NOT_UPDATING":
                    print(f"✓ Endpoint {endpoint_name} is READY!")
                    return True
                    
            except Exception as e:
                print(f"  Checking endpoint: {e}")
                
            time.sleep(poll_sec)
            
        print(f"✗ Timeout waiting for {endpoint_name}")
        return False
    except ImportError:
        print("Install databricks-sdk: %pip install databricks-sdk")
        return False


def main() -> None:
    print("=" * 70)
    print("Step 4: Provision agents")
    print("=" * 70)
    print()
    
    print(f"Looking up Knowledge Assistant: {KA_NAME}")
    endpoint_name = get_ka_endpoint_name()
    
    if not endpoint_name:
        print()
        print("⚠ Could not find endpoint. Make sure you ran Step 3 to create the agent.")
        print(f"  Agent name: {KA_NAME}")
        print()
        print("Manual steps:")
        print("  1. Go to Agents in Databricks UI")
        print(f"  2. Find agent: {KA_NAME}")
        print("  3. Check the endpoint status")
        return
    
    print(f"✓ Found endpoint: {endpoint_name}")
    print()
    
    # Wait for endpoint to be ready
    is_ready = wait_for_online(endpoint_name, timeout_sec=600, poll_sec=30)
    
    print()
    print("=" * 70)
    if is_ready:
        print("✓ Step 4 complete! Knowledge Assistant is ready.")
        print()
        print("Next steps:")
        print("  1. Test the agent in AI Playground")
        print(f"  2. Query the endpoint: {endpoint_name}")
        print("  3. Build your chatbot application using the agent")
    else:
        print("⚠ Step 4 incomplete. Endpoint is not ready yet.")
        print()
        print("Check status manually:")
        print("  1. Go to Serving in Databricks UI")
        print(f"  2. Find endpoint: {endpoint_name}")
        print("  3. Wait for status to be READY")
    print("=" * 70)


if __name__ == "__main__":
    main()
