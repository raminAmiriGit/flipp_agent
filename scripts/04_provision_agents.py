"""
Step 4: Run / provision agents — wait for KA endpoint and optionally add examples.

- Poll Knowledge Assistant endpoint until status is ONLINE.
- KA with add_examples_from_volume=true will ingest JSON question/guideline files from the volume.

Run locally or in a notebook. Uses Databricks SDK or MCP get_ka / get_serving_endpoint_status.
Config: conf/catalog_config.py.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from conf.catalog_config import KA_NAME


def get_ka_status_via_sdk():
    """Look up KA by name and return endpoint status (if SDK supports it)."""
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        # Agent Bricks may expose list/get; fallback to serving endpoint by naming convention
        # Endpoint name is often derived from tile_id, e.g. ka-<tile_id>-endpoint
        return None, "Use MCP find_ka_by_name then get_serving_endpoint_status to check."
    except ImportError:
        return None, "Install databricks-sdk. Or use MCP: find_ka_by_name -> get_ka -> get_serving_endpoint_status."


def wait_for_online(endpoint_name: str, timeout_sec: int = 600, poll_sec: int = 30) -> bool:
    """Poll serving endpoint until READY or timeout."""
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                ep = w.serving_endpoints.get(name=endpoint_name)
                state = getattr(ep, "state", None) or getattr(ep, "config", {})
                if str(state).upper() == "READY":
                    print(f"  Endpoint {endpoint_name} is READY.")
                    return True
            except Exception as e:
                print(f"  Check endpoint: {e}")
            time.sleep(poll_sec)
        print(f"  Timeout waiting for {endpoint_name}")
        return False
    except ImportError:
        return False


def main() -> None:
    print("Step 4: Provision agents")
    print(f"  1. Create KA via MCP create_or_update_ka (Step 3).")
    print(f"  2. Use MCP find_ka_by_name(name='{KA_NAME}') to get tile_id and endpoint_name.")
    print("  3. Use MCP get_serving_endpoint_status(name=<endpoint_name>) until state is READY.")
    print("  4. If add_examples_from_volume was true, examples are added when endpoint is ONLINE.")
    print()
    _, msg = get_ka_status_via_sdk()
    print(msg)
    print("\nStep 4 done when KA endpoint is ONLINE. Next: Step 5 — run the deal-finder chat app.")


if __name__ == "__main__":
    main()
