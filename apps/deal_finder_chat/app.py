"""
Flipp Deal-Finder — Streamlit app for Databricks Apps.

Communicates with the Databricks Multi-Agent Supervisor (MAS) endpoint.
Nav: Home, Flyers, Shopping List, AI Assistant. Chat with history and suggested prompts.
"""
from __future__ import annotations

import streamlit as st
from pathlib import Path

from config import FLIPP_LOGO_URL, FLIPP_TAGLINE
from backend_mas import query_mas_simple

st.set_page_config(
    page_title="Flipp Deal-Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Flipp-style light background and branding
st.markdown("""
<style>
    .stApp { background-color: #f5f5f5; }
    .flipp-header { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem; }
    .flipp-logo-tagline { display: flex; align-items: center; gap: 0.75rem; }
    .flipp-tagline { color: #333; font-size: 1.1rem; font-weight: 600; }
    .prompt-chip-wrap { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ----- Header: logo + tagline -----
try:
    st.markdown(f"""
    <div class="flipp-header">
        <div class="flipp-logo-tagline">
            <img src="{FLIPP_LOGO_URL}" alt="Flipp" width="90" onerror="this.outerHTML='<span style=\\'font-size:1.8rem\\'>🛒</span>'">
            <span class="flipp-tagline">{FLIPP_TAGLINE}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
except Exception:
    st.markdown(f"## 🛒 {FLIPP_TAGLINE}")

# ----- Navigation -----
pages = ["Home", "Flyers", "Shopping List", "AI Assistant"]
idx = pages.index(st.session_state.page) if st.session_state.page in pages else 0
nav_cols = st.columns([1, 1, 1, 1, 2])
for i, p in enumerate(pages):
    with nav_cols[i]:
        if st.button(p, key=f"nav_{p}", use_container_width=True, type="primary" if p == st.session_state.page else "secondary"):
            st.session_state.page = p
            st.rerun()
with nav_cols[-1]:
    st.markdown("<div style='text-align:right; color:#666;'>👤</div>", unsafe_allow_html=True)

st.divider()

# ----- Home -----
if st.session_state.page == "Home":
    st.markdown("## Welcome to Flipp Deal-Finder")
    st.markdown("Find the best deals and coupons. Use **AI Assistant** to ask questions, or browse **Flyers**.")

    # Flyer example images (medium size, non-clickable)
    app_dir = Path(__file__).resolve().parent
    flyer_images = [app_dir / "flyer1.jpeg", app_dir / "flyer2.jpeg"]
    if all(p.exists() for p in flyer_images):
        c1, c2 = st.columns(2)
        with c1:
            st.image(str(flyer_images[0]), use_container_width=True, caption="Weekly flyer example")
        with c2:
            st.image(str(flyer_images[1]), use_container_width=True, caption="Weekly flyer example")

    st.info("👆 Go to **AI Assistant** to chat with the deal-finder agent.")
    if st.button("✨ Ask Flipp", key="home_ask"):
        st.session_state.page = "AI Assistant"
        st.rerun()

# ----- Flyers -----
elif st.session_state.page == "Flyers":
    st.markdown("## Weekly Flyers")
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "flyers" / "catalog_style"
    flyer_meta = [
        {"retailer": "Metro Plus", "title": "EVERYTHING YOU NEED FOR THE BIG GAME", "slug": "metro_plus"},
        {"retailer": "FreshCo Weekly", "title": "WEEKLY SAVINGS", "slug": "freshco_weekly"},
        {"retailer": "No Frills", "title": "FLYER DEALS", "slug": "no_frills"},
    ]
    if data_dir.exists():
        all_pdfs = {p.name: p for p in data_dir.glob("*.pdf")}
    else:
        all_pdfs = {}
    for i, meta in enumerate(flyer_meta):
        # Match PDF by slug (e.g. flyer_metro_plus_0.pdf)
        pdf_path = None
        for name, p in all_pdfs.items():
            if meta["slug"] in name:
                pdf_path = p
                break
        with st.expander(f"**{meta['retailer']}** — {meta['title']}", expanded=(i == 0)):
            if pdf_path and pdf_path.exists():
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=pdf_path.name, key=f"flyer_dl_{i}")
            else:
                st.caption("PDF available when run from repo with data/flyers/catalog_style.")
    if st.button("✨ Ask Flipp", key="flyers_ask"):
        st.session_state.page = "AI Assistant"
        st.rerun()

# ----- Shopping List -----
elif st.session_state.page == "Shopping List":
    st.markdown("## Shopping List")
    st.caption("Your saved items. (Placeholder.)")
    st.info("📋 Use AI Assistant to ask for deals, then add to your list.")
    if st.button("✨ Ask Flipp", key="list_ask"):
        st.session_state.page = "AI Assistant"
        st.rerun()

# ----- AI Assistant -----
else:
    st.markdown("## AI Assistant")
    st.caption("Ask about deals, coupons, and flyers. Powered by the Flipp Multi-Agent Supervisor.")

    # Suggested prompt chips
    suggested = ["Best deals near me", "BBQ on a budget", "BOGO this week", "Cheapest diapers"]
    for prompt in suggested:
        if st.button(prompt, key=f"chip_{prompt[:20]}", use_container_width=False):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Finding deals…"):
                    content, citations = query_mas_simple(prompt)
                st.markdown(content or "_No response._")
                if citations:
                    with st.expander("📎 Sources"):
                        for c in citations:
                            st.text(c if isinstance(c, str) else str(c))
            st.session_state.messages.append({"role": "assistant", "content": content or "", "citations": citations})
            st.rerun()

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                with st.expander("📎 Sources"):
                    for c in msg["citations"]:
                        st.text(c if isinstance(c, str) else str(c))

    # Input
    if user_input := st.chat_input("Ask about deals, e.g. What are the best chicken deals?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Finding deals…"):
                content, citations = query_mas_simple(user_input)
            st.markdown(content or "_No response._")
            if citations:
                with st.expander("📎 Sources"):
                    for c in citations:
                        st.text(c if isinstance(c, str) else str(c))
        st.session_state.messages.append({"role": "assistant", "content": content or "", "citations": citations})
        st.rerun()
