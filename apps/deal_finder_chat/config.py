"""
App config: MAS/KA names from conf/catalog_config or env.
When running as Databricks App, env vars can override.
"""
import os

# Agent names (from flipp_agent/conf/catalog_config.py)
MAS_NAME = os.environ.get("FLIPP_MAS_NAME", "Flipp_Deal_Supervisor")
KA_NAME = os.environ.get("FLIPP_KA_NAME", "flipp-knowledge-assistant-2026-02-10")

# Endpoint name (set to skip discovery)
FLIPP_MAS_ENDPOINT_NAME = os.environ.get("FLIPP_MAS_ENDPOINT_NAME", "")

# Flipp branding
FLIPP_LOGO_URL = os.environ.get(
    "FLIPP_LOGO_URL",
    "https://app.flipp.com/wp-content/uploads/2020/04/Flipp-logo-blue.png",
)
FLIPP_TAGLINE = "Your Smart Deal Finder"
