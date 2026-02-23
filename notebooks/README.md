# Custom Knowledge Assistant (LangChain) Notebook

This folder contains a **single notebook** that reimplements Databricks Knowledge Assistant–style RAG using custom libraries, to illustrate how much code is involved compared to using the managed KA.

## Notebook

- **`custom_knowledge_assistant_langchain.ipynb`** – End-to-end flow in one place:
  1. Load PDF flyers from `data/flyers` (table + catalog)
  2. Segment documents (chunking with RecursiveCharacterTextSplitter)
  3. Create vector space (OpenAI embeddings + Chroma)
  4. Build RAG chain (retriever → prompt → OpenAI LLM)
  5. Track with MLflow (experiment, params, LangChain autolog tracing)

## Setup

1. **Python env**  
   Use the project venv or a dedicated env with the notebook dependencies.

2. **Install dependencies** (from repo root or from `notebooks/`):
   ```bash
   pip install -r notebooks/requirements-custom-ka.txt
   ```

3. **Databricks endpoints** (required for embeddings and LLM via OpenAI-compatible API):
   - **DATABRICKS_TOKEN**: From your workspace (Profile → Generate Access Token or [PAT docs](https://docs.databricks.com/en/dev-tools/auth/pat.html)).
   - **DATABRICKS_BASE_URL** (optional): Your MLflow/gateway URL, e.g. `https://<workspace-id>.ai-gateway.cloud.databricks.com/mlflow/v1`. If unset, the notebook uses an example URL; replace with your workspace URL.
   - **DATABRICKS_EMBEDDING_MODEL** / **DATABRICKS_LLM_MODEL** (optional): Your serving endpoint names; default to `text-embedding-3-small` and `databricks-gpt-5-mini`.

   ```bash
   export DATABRICKS_TOKEN=...
   export DATABRICKS_BASE_URL=https://<your-workspace>.ai-gateway.cloud.databricks.com/mlflow/v1  # optional
   ```

4. **Run the notebook**  
   Execute cells in order. The first run will create `chroma_flyers/` and (if enabled) `mlruns/` under the project root.

## Viewing MLflow traces

From the project root:

```bash
mlflow ui
```

Open the experiment `custom_ka_flyer_rag` and a run to see logged params and traces for the RAG chain invocations.
