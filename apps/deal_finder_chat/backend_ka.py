"""
Backend for Flipp Deal-Finder Chat: query Knowledge Assistant serving endpoint.

Uses Databricks SDK to call the KA (OpenAI-compatible chat) and return
assistant message and any citations.
"""
from __future__ import annotations

import os
from typing import Any

# KA endpoint name: set via env or discovered from Agent Bricks (find_ka_by_name -> endpoint_name)
ENDPOINT_NAME = os.environ.get("FLIPP_KA_ENDPOINT_NAME", "")


def get_client():
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient()


def find_ka_endpoint() -> str:
    """Resolve KA endpoint name from Agent Bricks if not set."""
    if ENDPOINT_NAME:
        return ENDPOINT_NAME
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        # Agent Bricks: list or get by name to obtain endpoint_name
        # Fallback: use FLIPP_KA_ENDPOINT_NAME or a default
        tiles = getattr(w, "agent_bricks", None) or getattr(w, "tiles", None)
        if tiles and hasattr(tiles, "list"):
            for t in tiles.list():
                if getattr(t, "name", "") == "Flipp_Deal_Finder":
                    return getattr(t, "endpoint_name", "") or ""
    except Exception:
        pass
    return ""


def query_ka(messages: list[dict[str, str]], max_tokens: int = 1024, temperature: float = 0.2) -> dict[str, Any]:
    """
    Send chat messages to the Knowledge Assistant endpoint.

    messages: [{"role": "user"|"assistant", "content": "..."}]
    Returns: {"content": "...", "citations": [...], "error": "..." }
    """
    endpoint = ENDPOINT_NAME or find_ka_endpoint()
    if not endpoint:
        return {
            "content": "",
            "citations": [],
            "error": "Knowledge Assistant endpoint not configured. Set FLIPP_KA_ENDPOINT_NAME or create the KA in Step 3.",
        }

    try:
        w = get_client()
        # OpenAI-compatible chat on Databricks model serving (SDK: messages, max_tokens, temperature)
        response = w.serving_endpoints.query(
            name=endpoint,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # Response: .choices[0].message.content (and optionally .citations)
        if not getattr(response, "choices", None):
            return {"content": "", "citations": [], "error": "Empty response from endpoint."}
        first = response.choices[0]
        msg = getattr(first, "message", first)
        content = getattr(msg, "content", "") or ""
        citations = getattr(msg, "citations", []) or []
        if not isinstance(citations, list):
            citations = []
        return {"content": content, "citations": citations, "error": None}
    except Exception as e:
        return {"content": "", "citations": [], "error": str(e)}


def query_ka_simple(user_message: str) -> tuple[str, list]:
    """One-shot query: (assistant_text, citations)."""
    out = query_ka([{"role": "user", "content": user_message}])
    if out.get("error"):
        return f"Error: {out['error']}", []
    return out.get("content", ""), out.get("citations", [])
