"""
Backend for Flipp Deal-Finder Chat: query Multi-Agent Supervisor (MAS) serving endpoint.

Uses MAS name from config; resolves endpoint name via env FLIPP_MAS_ENDPOINT_NAME
or by listing serving endpoints and matching MAS naming (e.g. mas-*).

Uses the Databricks OpenAI client (responses.create) so the MAS returns a proper
reply; the control-plane query() can return empty choices for agent endpoints.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from config import FLIPP_MAS_ENDPOINT_NAME, MAS_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flipp.backend_mas")


def get_client():
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient()


def find_mas_endpoint() -> str:
    """Resolve MAS endpoint name: env first, then list endpoints and match by name."""
    if FLIPP_MAS_ENDPOINT_NAME:
        logger.info("Using MAS endpoint from env: %s", FLIPP_MAS_ENDPOINT_NAME)
        return FLIPP_MAS_ENDPOINT_NAME
    try:
        w = get_client()
        for ep in w.serving_endpoints.list():
            name = getattr(ep, "name", "") or ""
            if "mas-" in name.lower() or "supervisor" in name.lower():
                logger.info("Resolved MAS endpoint: %s", name)
                return name
            if MAS_NAME and MAS_NAME.replace("_", "-").lower() in name.lower():
                logger.info("Resolved MAS endpoint by name: %s", name)
                return name
    except Exception as e:
        logger.warning("Endpoint discovery failed: %s", e)
    logger.warning("No MAS endpoint found")
    return ""


def is_tool_call(obj: Any) -> bool:
    """Check if an object is a tool call (not user-facing text)."""
    if obj is None:
        return False
    # Check for tool call attributes
    obj_type = type(obj).__name__
    if "ToolCall" in obj_type or "FunctionCall" in obj_type:
        return True
    # Check for tool_calls attribute
    if hasattr(obj, "tool_calls") and obj.tool_calls:
        return True
    # Check for type field indicating function_call
    if hasattr(obj, "type") and obj.type == "function_call":
        return True
    return False


def extract_text_from_content(content_block: Any) -> str:
    """Extract text from a content block, filtering out tool calls."""
    if content_block is None:
        return ""
    
    # If it's a tool call, skip it
    if is_tool_call(content_block):
        return ""
    
    # If it has a text attribute, use it
    if hasattr(content_block, "text") and content_block.text:
        return str(content_block.text)
    
    # If it's a dict with text key
    if isinstance(content_block, dict):
        if "text" in content_block:
            return str(content_block.get("text", ""))
        if "content" in content_block:
            return str(content_block.get("content", ""))
    
    # If it's a string, return it
    if isinstance(content_block, str):
        return content_block
    
    return ""


def extract_supervisor_response(content: str, supervisor_name: str | None = None) -> str:
    """
    Extract only the supervisor's final answer from MAS output.

    MAS returns multiple agents' output (e.g. Genie table + supervisor summary).
    We look for <name>SupervisorName</name> and return the text after it so the
    app shows only the supervisor's reply, not tool calls or sub-agent output.
    
    Also filters out lines that look like tool calls or error messages.
    """
    if not content:
        return content
    
    # First, try to find the supervisor's response by name tag
    name = (supervisor_name or MAS_NAME or "").strip()
    if name:
        tag = f"<name>{re.escape(name)}</name>"
        idx = content.find(tag)
        tag_len = len(tag)
        if idx == -1:
            tag_ci = f"<name>{name.lower()}</name>"
            idx = content.lower().find(tag_ci)
            tag_len = len(tag_ci)
        if idx >= 0:
            result = content[idx + tag_len :].strip()
            if result:
                logger.debug("Extracted supervisor response by name tag, len=%d", len(result))
                return result
    
    # If no name tag found, filter out tool calls and intermediate steps
    lines = content.split("\n")
    filtered_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        # Skip empty lines
        if not line_stripped:
            continue
        # Skip lines that look like tool calls
        if "ResponseFunctionToolCall" in line_stripped:
            continue
        if "function_call" in line_stripped and ("arguments=" in line_stripped or "call_id=" in line_stripped):
            continue
        # Skip name tags for sub-agents
        if line_stripped.startswith("<name>") and line_stripped.endswith("</name>"):
            agent_name = line_stripped[6:-7]
            # Keep supervisor name tags, skip others
            if name and agent_name.lower() != name.lower():
                continue
        # Skip error messages from sub-agents
        if "query failed with error:" in line_stripped.lower():
            continue
        if "UNRESOLVED_ROUTINE" in line_stripped or "SQLSTATE:" in line_stripped:
            continue
        
        filtered_lines.append(line)
    
    result = "\n".join(filtered_lines).strip()
    if result and result != content:
        logger.debug("Filtered content, original_len=%d, filtered_len=%d", len(content), len(result))
    
    return result if result else content


def query_mas(
    messages: list[dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """
    Send chat messages to the MAS (Multi-Agent Supervisor) endpoint.

    Uses the Databricks OpenAI client (ResponsesAgent API: responses.create with input=...)
    so the agent returns a proper response. The control-plane query() returns empty choices
    for this endpoint type.
    messages: [{"role": "user"|"assistant", "content": "..."}]
    Returns: {"content": "...", "citations": [...], "error": "..." }
    """
    endpoint = find_mas_endpoint()
    if not endpoint:
        return {
            "content": "",
            "citations": [],
            "error": (
                "MAS endpoint not found. Set FLIPP_MAS_ENDPOINT_NAME to the serving endpoint name "
                f"(e.g. mas-xxx), or ensure a MAS named '{MAS_NAME}' is deployed."
            ),
        }

    try:
        w = get_client()
        client = w.serving_endpoints.get_open_ai_client()
        input_list = [
            {"role": (m.get("role") or "user").lower(), "content": m.get("content", "") or ""}
            for m in messages
        ]
        # Endpoint URL the SDK uses (invocations)
        try:
            host = getattr(w.config, "host", "").rstrip("/")
            endpoint_url = f"{host}/serving-endpoints/{endpoint}/invocations"
            logger.info("MAS endpoint URL: %s", endpoint_url)
        except Exception:
            pass
        logger.info("Querying MAS via OpenAI client endpoint=%s input_len=%d", endpoint, len(input_list))
        content = ""
        citations = []
        response = None

        # Try ResponsesAgent API first (input=...)
        try:
            response = client.responses.create(model=endpoint, input=input_list)
        except Exception as resp_err:
            logger.info("responses.create failed (%s), trying chat.completions", resp_err)

        if response is None:
            # Fallback: ChatAgent API (messages=...)
            response = client.chat.completions.create(
                model=endpoint,
                messages=input_list,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        # Parse: output is a list of ResponseOutputMessage (MAS can return multiple; use all for full reply).
        if getattr(response, "output", None) is not None:
            out = response.output
            if isinstance(out, list) and len(out) > 0:
                all_text_parts = []
                for msg in out:
                    # Skip tool calls entirely
                    if is_tool_call(msg):
                        logger.debug("Skipping tool call message")
                        continue
                    
                    if isinstance(msg, dict):
                        text = msg.get("content", msg.get("text", ""))
                        if text:
                            all_text_parts.append(text)
                    elif hasattr(msg, "content") and msg.content:
                        # Handle content that might be a list of blocks
                        content_blocks = msg.content if isinstance(msg.content, list) else [msg.content]
                        for block in content_blocks:
                            text = extract_text_from_content(block)
                            if text:
                                all_text_parts.append(text)
                    elif isinstance(msg, str):
                        all_text_parts.append(msg)
                    # Skip converting unknown objects to strings - they're likely tool calls
                
                content = "\n\n".join(p for p in all_text_parts if p).strip()
                if len(out) > 1:
                    logger.debug("MAS output messages count=%d, text_parts=%d, combined_len=%d", 
                               len(out), len(all_text_parts), len(content))
            elif isinstance(out, str):
                content = out
        if not content and getattr(response, "choices", None) and len(response.choices) > 0:
            first = response.choices[0]
            msg = getattr(first, "message", first)
            content = getattr(msg, "content", "") or ""
            citations = getattr(msg, "citations", []) or []
        if not content and getattr(response, "predictions", None) and len(response.predictions) > 0:
            pred = response.predictions[0]
            if isinstance(pred, dict):
                content = pred.get("content", pred.get("text", ""))
                citations = pred.get("citations", [])
            else:
                content = str(pred)
        if not content and response is not None and hasattr(response, "__dict__"):
            logger.warning("MAS response keys: %s", list(response.__dict__.keys()))
        if not isinstance(citations, list):
            citations = []
        # Show only the supervisor's final answer (strip tool calls and sub-agent output)
        content = extract_supervisor_response(content)
        logger.info("MAS response content_len=%d", len(content))
        return {"content": content, "citations": citations, "error": None}
    except Exception as e:
        logger.exception("MAS query failed: %s", e)
        return {"content": "", "citations": [], "error": str(e)}


def query_mas_simple(user_message: str) -> tuple[str, list]:
    """One-shot query: (assistant_text, citations)."""
    out = query_mas([{"role": "user", "content": user_message}])
    if out.get("error"):
        return f"Error: {out['error']}", []
    return out.get("content", ""), out.get("citations", [])
