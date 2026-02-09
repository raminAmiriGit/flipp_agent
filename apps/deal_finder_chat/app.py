"""
Flipp Deal-Finder Chat — Streamlit app.

Conversational UI for the Knowledge Assistant: ask natural-language questions
about deals and get recommendations with citations to source flyers.
"""
from __future__ import annotations

import streamlit as st

from backend_ka import query_ka_simple

st.set_page_config(page_title="Flipp Deal-Finder", page_icon="🛒", layout="centered")

st.title("🛒 Flipp Deal-Finder")
st.caption("Ask about current flyer deals. Answers are grounded in Flipp flyer content with citations.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander("📎 Sources"):
                for c in msg["citations"]:
                    st.text(c if isinstance(c, str) else str(c))

if prompt := st.chat_input("e.g. I'm hosting a barbecue for 10 people — what are the best deals?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Finding deals…"):
            content, citations = query_ka_simple(prompt)
        st.markdown(content or "_No response._")
        if citations:
            with st.expander("📎 Sources"):
                for c in citations:
                    st.text(c if isinstance(c, str) else str(c))

    st.session_state.messages.append({
        "role": "assistant",
        "content": content or "",
        "citations": citations,
    })
