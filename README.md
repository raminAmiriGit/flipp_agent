# About Flipp

Flipp is a digital shopping platform that aggregates weekly circulars, flyers, and promotions from over 2,000 retailers (including Walmart, Kroger, Lowe's, and Home Depot) and serves them to 100 million+ high-intent shoppers across North America. Flipp's platform connects retailers and brands to consumers through digital flyers, coupons, loyalty card integration, and shopping lists.

Flipp is already a Databricks customer. Their primary data sources — content from retail partners and user-generated shopper behavior — were historically siloed and unstructured. They use the Databricks Lakehouse and Agent Bricks / Mosaic AI.

---

## Deal-Finder Agent (This Repo)

A **conversational deal-finding chatbot** built with **Databricks Agent Bricks** (Knowledge Assistant), grounded in Flipp-style flyer data. Shoppers ask natural-language questions and get deal recommendations with **citations** to source flyers.

### The Problem

Flipp's 100M+ shoppers browse hundreds of flyers weekly. Deal discovery is largely manual — users search by store or keyword, and ~70% find it hard to navigate. There is no intent-aware, conversational interface (e.g. *"I'm hosting a barbecue for 10 people — what are the best deals near me?"*).

### The Solution

A **Knowledge Assistant** that:

- Answers in natural language, grounded in flyer and promotional content.
- Recommends deals with **citations** back to source flyers.
- Can be used by shoppers or internal teams.

### Implementation (Step-by-Step)

| Step | Description |
|------|-------------|
| **1. Create data** | Synthetic deals catalog (parquet) + flyer PDFs with JSON examples |
| **2. Enrich data** | Delta tables from parquet; upload PDFs to UC Volume |
| **3. Create agents** | Knowledge Assistant (and optional Genie + MAS) |
| **4. Run / provision** | Wait for KA endpoint ONLINE; add examples from volume |
| **5. Create app** | Streamlit chat app on Databricks calling the KA endpoint |

**Full guide:** [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)

**Quick file index:**

- Config: `conf/catalog_config.py`
- Step 1: `scripts/01_create_data.py`, `scripts/generate_flyer_pdfs.py`
- Step 2: `scripts/02_enrich_data.py`, `scripts/02_upload_flyer_docs.py`
- Step 3: `scripts/03_create_agents.py`
- Step 4: `scripts/04_provision_agents.py`
- Step 5: `apps/deal_finder_chat/` (Streamlit app)

---

## Information Extraction (Alternative Use Case)

Flipp also receives promotional content from 1,600+ partners in many formats (PDFs, feeds, APIs). The content operations team manually turns these into structured flyer items (product, price, discount %, category, validity, etc.) — 900+ hours monthly. **Agent Bricks: Information Extraction** can automate turning incoming retailer content into structured Delta Lake tables. That use case is separate from the deal-finder chatbot above.