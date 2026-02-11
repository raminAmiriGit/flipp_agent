# Flipp Deal-Finder Chat App

Streamlit app that talks to the **Flipp Multi-Agent Supervisor (MAS)**. Users get a simple nav (Home, Flyers, Shopping List, AI Assistant), browse flyer examples, and chat with the deal-finder agent. Built to run **on your machine** and as a **Databricks App**.

## Features

- **Branding:** Flipp logo (top-left) and tagline "Your Smart Deal Finder"
- **Nav:** Home, Flyers, Shopping List, AI Assistant
- **Flyers:** Sample flyers from `data/flyers/catalog_style` (PDF download when run from repo)
- **AI Assistant:** Chat with history; suggested chips (e.g. "Best deals near me", "BBQ on a budget"); responses from MAS with optional citations
- **Profile icon:** Top-right placeholder (no action)

## Config

- **MAS name** and optional **endpoint** come from `flipp_agent/conf/catalog_config.py` or env:
  - `FLIPP_MAS_NAME` — default `Flipp_Deal_Supervisor`
  - `FLIPP_MAS_ENDPOINT_NAME` — optional; if set, the app uses this serving endpoint name instead of resolving it from the MAS name

## Run locally

```bash
cd flipp_agent/apps/deal_finder_chat
pip install -r requirements.txt
# Optional: set endpoint to skip discovery
export FLIPP_MAS_ENDPOINT_NAME=mas-682564f5-endpoint
streamlit run app.py
```

## Deploy on Databricks Apps

1. Ensure the **MAS** (and its KA + Genie agents) are created and the MAS endpoint is **ONLINE**.
2. From the app folder:
   ```bash
   databricks apps deploy .
   ```
   Or deploy from the Workspace UI (Apps → Create → upload this folder).
3. Optionally set `FLIPP_MAS_ENDPOINT_NAME` in the app’s env (in `app.yaml` or in the UI) to the MAS serving endpoint name (e.g. `mas-682564f5-endpoint`).
4. If not set, the app discovers the endpoint by listing serving endpoints and choosing one whose name contains `mas-` or `supervisor`.

The app uses the Databricks SDK (and workspace auth when run in Databricks) to call the MAS chat endpoint.
