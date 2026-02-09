# Flipp Deal-Finder Chat App

Streamlit app that calls the Flipp Deal-Finder Knowledge Assistant (Agent Bricks). Users ask natural-language questions and get deal recommendations with citations to source flyers.

## Setup

1. Complete Steps 1–4 of the [implementation guide](../../docs/IMPLEMENTATION.md): create data, enrich, create KA, provision.
2. Set the KA serving endpoint name:
   - **Env:** `FLIPP_KA_ENDPOINT_NAME=<your-ka-endpoint-name>`
   - Or in `app.yaml` under `env.FLIPP_KA_ENDPOINT_NAME`.
3. Get the endpoint name from Databricks: Agent Bricks → your Knowledge Assistant → endpoint name (e.g. `ka-<tile_id>-endpoint`).

## Run locally

```bash
pip install -r requirements.txt
export FLIPP_KA_ENDPOINT_NAME=your-ka-endpoint-name
streamlit run app.py
```

## Deploy on Databricks

- Use **Databricks Apps** or **Asset Bundles** to deploy this folder.
- Ensure the app has access to the same workspace and Model Serving (query the KA endpoint).
