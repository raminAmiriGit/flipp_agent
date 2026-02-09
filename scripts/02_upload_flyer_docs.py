"""
Step 2b: Upload flyer PDFs and JSON examples to Unity Catalog Volume.

Reads from local data/flyers/ (table_style and catalog_style), uploads to
/Volumes/<catalog>/<schema>/flyer_docs for the Knowledge Assistant.

Run locally (Python 3.9+). Requires databricks-sdk and configured Databricks profile.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from conf.catalog_config import CATALOG, SCHEMA, VOLUME_FLYER_DOCS, VOLUME_PATH_FLYER_DOCS

# Local flyer output from generate_flyer_pdfs.py
DATA_FLYERS = PROJECT_ROOT / "data" / "flyers"


def ensure_volume_exists(w) -> None:
    """Remind to create volume if needed. Volume is created in Step 2a (02_enrich_data.py on cluster)."""
    print(f"  Using volume: {VOLUME_PATH_FLYER_DOCS}")
    print("  (Create it first by running 02_enrich_data.py on a Databricks cluster, or create manually in SQL.)")


def upload_with_sdk(local_path: Path, volume_path: str) -> None:
    """Upload a file to a UC volume using Databricks SDK."""
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.files import Upload

    w = WorkspaceClient()
    with open(local_path, "rb") as f:
        w.files.upload(volume_path, f)


def main() -> None:
    if not DATA_FLYERS.exists():
        print(f"Run generate_flyer_pdfs.py first to create {DATA_FLYERS}")
        sys.exit(1)

    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        print("Install databricks-sdk: pip install databricks-sdk")
        sys.exit(1)

    w = WorkspaceClient()
    ensure_volume_exists(w)
    uploaded = 0

    for subdir in ("table_style", "catalog_style"):
        src_dir = DATA_FLYERS / subdir
        if not src_dir.exists():
            continue
        for f in src_dir.iterdir():
            if f.suffix not in (".pdf", ".json"):
                continue
            # e.g. /Volumes/flipp_demo/deal_finder/flyer_docs/table_style/flyer_metro_plus_0.pdf
            rel = f.relative_to(DATA_FLYERS)
            volume_path = f"{VOLUME_PATH_FLYER_DOCS}/{rel}"
            try:
                with open(f, "rb") as fp:
                    w.files.upload(volume_path, fp)
                print(f"  Uploaded {f.name} -> {volume_path}")
                uploaded += 1
            except Exception as e:
                # Volume might not exist; create via SQL first
                print(f"  Failed {f.name}: {e}")

    if uploaded == 0:
        print("No files uploaded. Ensure volume exists:")
        print(f"  CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME_FLYER_DOCS};")
        print("  (Run in a Databricks notebook or Step 2a after creating the volume there.)")
    else:
        print(f"\nStep 2b done. Uploaded {uploaded} files to {VOLUME_PATH_FLYER_DOCS}")
    print("Next: Step 3 — create Knowledge Assistant pointing at this volume.")


if __name__ == "__main__":
    main()
