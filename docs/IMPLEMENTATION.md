# Flipp Deal-Finder Agent — Implementation Guide

This guide implements a **conversational deal-finding chatbot** on Databricks using Agent Bricks (Knowledge Assistant), grounded in Flipp-style flyer data and promotional content. Shoppers ask natural-language questions and get deal recommendations with citations to source flyers.

## The Problem

Flipp's 100M+ shoppers browse hundreds of flyers weekly. Deal discovery is largely manual — users search by store or keyword. About 70% find it hard to navigate content. There is no intent-aware, conversational interface (e.g., *"I'm hosting a barbecue for 10 people — what are the best deals near me?"*).

## The Solution

A **Knowledge Assistant** agent that:

- Answers in natural language, grounded in flyer and promotional data.
- Recommends deals with **citations** back to source flyers.
- Can be used by shoppers or internal teams.

Optional extensions: **Genie** for SQL over structured deal tables, and **Multi-Agent Supervisor (MAS)** to route between document Q&A and data Q&A.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 1: Create Data                                                     │
│  • Synthetic deals catalog (parquet)                                    │
│  • Flyer PDFs + JSON (question/guideline) for KA examples                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 2: Enrich Data                                                     │
│  • Delta table(s) from deals parquet                                     │
│  • Upload PDFs + JSON to Unity Catalog Volume                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 3: Create Agents                                                   │
│  • Knowledge Assistant (KA) → volume with flyer PDFs                     │
│  • Optional: Genie Space on deals table, MAS to route                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 4: Run / Provision                                                 │
│  • Provision KA endpoint                                                 │
│  • Add examples from volume JSON files                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 5: Create App                                                      │
│  • Databricks app (e.g. Streamlit) that calls KA endpoint               │
│  • Chat UI with citations                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Index

| Step | Purpose | File(s) |
|------|---------|--------|
| — | Overview and config | `docs/IMPLEMENTATION.md`, `conf/catalog_config.py` |
| 1 | Create data | `scripts/01_create_data.py`, `scripts/generate_flyer_pdfs.py` |
| 2 | Enrich data | `scripts/02_enrich_data.py`, `scripts/02_upload_flyer_docs.py` |
| 3 | Create agents | `scripts/03_create_agents.py` |
| 4 | Run / provision | `scripts/04_provision_agents.py` |
| 5 | App | `apps/deal_finder_chat/` (Streamlit + app config) |

---

## Prerequisites

- Databricks workspace with Unity Catalog.
- Permissions: create catalog/schema/volume, create and query tables, create Knowledge Assistant, use Model Serving (for KA endpoint).
- For PDF generation locally: `reportlab` (see `requirements-synthetic.txt`).
- For running scripts on Databricks: cluster or DAB job with access to the same catalog/schema.

---

## Step 1: Create Data

**Goal:** Produce raw data for flyers and deals.

1. **Deals catalog (parquet)**  
   Run `scripts/01_create_data.py` on a Databricks cluster (or locally with Spark).  
   - Creates catalog/schema/volume if needed.  
   - Writes synthetic `deals` (and optionally `retailers`) to a Volume as parquet (e.g. `/Volumes/<catalog>/<schema>/raw_data/deals`).

2. **Flyer PDFs + JSON examples**  
   Run `scripts/generate_flyer_pdfs.py` locally to generate table-style and catalog-style flyer PDFs under `data/flyers/`.  
   - Add or reuse logic to write one JSON per flyer (or per theme) with `question` and `guideline` for the Knowledge Assistant.  
   - These PDFs + JSONs are used in Step 2 (upload to Volume) and Step 3 (KA).

**Config:** Set catalog/schema in `conf/catalog_config.py` (or env) and use the same in Step 2 and 3.

---

## Step 2: Enrich Data

**Goal:** Put data in the right shape and place for agents and apps.

1. **Delta tables**  
   Run `scripts/02_enrich_data.py` on Databricks.  
   - Reads parquet from the Volume (e.g. `raw_data/deals`).  
   - Writes Delta tables in Unity Catalog (e.g. `silver.deals` or `gold.deals`).  
   - Optional: add store/location, category, or validity columns for “deals near me” and filters.

2. **Flyer documents in Volume**  
   Same script (or a dedicated upload step):  
   - Ensure volume path for flyers exists (e.g. `.../flyer_docs`).  
   - Upload PDFs and their JSON example files from `data/flyers/` to that path.  
   - Knowledge Assistant will use this path as the document source.

---

## Step 3: Create Agents

**Goal:** Create the Knowledge Assistant and optionally Genie + MAS.

1. **Knowledge Assistant (KA)**  
   Run `scripts/03_create_agents.py` (or call Agent Bricks MCP / SDK).  
   - Create a KA with:  
     - **Name:** e.g. `Flipp_Deal_Finder`  
     - **Volume path:** the flyer document path (e.g. `/Volumes/<catalog>/<schema>/<volume>/flyer_docs`)  
     - **Description:** Conversational deal-finding chatbot grounded in flyer content.  
     - **Instructions:** Answer only from flyers; recommend deals and cite source flyer (retailer, validity).  
   - Enable “add examples from volume” so JSON question/guideline files are used.

2. **Optional: Genie Space**  
   Create a Genie Space on the enriched deals table so users can ask natural-language questions over structured data (e.g. “best deals this week in Produce”).

3. **Optional: Multi-Agent Supervisor (MAS)**  
   Create a MAS that routes:  
   - “Deal recommendations from flyer text” → KA  
   - “Aggregate or filter deals by store/category/dates” → Genie  

   Use `scripts/03_create_agents.py` to create KA (and optionally Genie + MAS) so one place owns all agent definitions.

---

## Step 4: Run / Provision

**Goal:** Ensure the KA (and optional MAS) are provisioned and ready.

1. Run `scripts/04_provision_agents.py` (or use the Agent Bricks UI).  
   - Poll KA (and MAS) endpoint status until `ONLINE`.  
   - If you use “add examples from volume”, ensure JSON files are in the volume; the KA will pick them up when the endpoint is ONLINE.

2. **Smoke test**  
   Send a test question to the KA endpoint (e.g. “What chicken deals are in the flyers this week?”) and confirm an answer with a citation.

---

## Step 5: Create App

**Goal:** A Databricks-hosted app that exposes the deal-finder chatbot.

1. **App structure**  
   Under `apps/deal_finder_chat/`:  
   - `app.py` — Streamlit (or Dash) UI: chat input, display messages and citations.  
   - `backend_ka.py` — Calls the KA model serving endpoint (OpenAI-compatible chat).  
   - `app.yaml` — Databricks Apps configuration.  
   - `requirements.txt` — `streamlit`, `databricks-sdk`, etc.

2. **Behavior**  
   - User types a question (e.g. “I’m hosting a barbecue for 10 people — what are the best deals?”).  
   - App sends the question to the KA (or MAS) endpoint.  
   - App shows the reply and any citations (e.g. “Source: Metro Plus flyer, valid Feb 5–11”).

3. **Deploy**  
   Deploy the app via Databricks Apps (or Asset Bundle) so users open it from the workspace.

---

## Configuration

- **Catalog / schema / volume:** Centralized in `conf/catalog_config.py` (or env vars). Use the same names in create data, enrich data, create agents, and app.  
- **KA name / volume path:** Must match the volume where you uploaded flyer PDFs + JSON.  
- **Endpoint:** App uses the KA’s (or MAS’s) serving endpoint name from Agent Bricks.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Create synthetic deals (parquet) and flyer PDFs + JSON examples. |
| 2 | Enrich: Delta tables from parquet; upload PDFs + JSON to UC Volume. |
| 3 | Create Knowledge Assistant (and optionally Genie + MAS). |
| 4 | Provision agents and add examples; smoke-test KA. |
| 5 | Build and deploy the deal-finder chat app on Databricks. |

After this, shoppers (or internal users) can use the app to ask intent-based questions and get deal recommendations with citations to the source flyers.
