from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import streamlit as st


def render_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --barni-ink: #24362b;
            --barni-muted: #6f7b73;
            --barni-green: #315b3d;
            --barni-green-soft: #e7eee2;
            --barni-beige: #f7f3e9;
            --barni-surface: #fcfbf7;
            --barni-border: rgba(45, 70, 53, 0.11);
        }
        .stApp { background: #fbfaf6; color: var(--barni-ink); }
        .block-container {
            max-width: 1240px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3, h4, h5, h6 {
            color: var(--barni-ink);
            letter-spacing: -0.018em;
        }
        h2 { margin-bottom: 0.2rem; }
        h3 { margin-top: 1.6rem; margin-bottom: 0.15rem; }
        [data-testid="stCaptionContainer"] { color: var(--barni-muted); }
        div.stButton > button,
        div.stDownloadButton > button {
            min-height: 2.65rem;
            border-radius: 12px;
            border-color: var(--barni-border);
            box-shadow: none;
            font-weight: 600;
        }
        div.stButton > button[kind="primary"] {
            background: var(--barni-green);
            border-color: var(--barni-green);
            color: white;
        }
        div.stButton > button:hover,
        div.stDownloadButton > button:hover {
            border-color: rgba(49, 91, 61, 0.35);
            color: var(--barni-green);
        }
        div.stButton > button[kind="primary"]:hover {
            background: #294f34;
            color: white;
        }
        [data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            border-radius: 12px;
        }
        [data-testid="stMetric"] { min-height: 4.5rem; }
        [data-testid="stMetricLabel"] { color: var(--barni-muted); }
        [data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
        }
        [data-testid="stAlert"] { border-radius: 14px; }
        [data-testid="stExpander"] {
            border-color: var(--barni-border);
            border-radius: 14px;
            background: rgba(252, 251, 247, 0.7);
        }
        .barni-empty-state {
            background: var(--barni-surface);
            border: 1px solid var(--barni-border);
            border-radius: 16px;
            padding: 1rem 1.15rem;
            color: var(--barni-muted);
        }
        [class*="st-key-barni_page_header_"] {
            max-width: 760px;
            margin-bottom: 0.9rem;
        }
        [class*="st-key-barni_page_header_"] h2 {
            margin: 0 0 0.15rem;
        }
        [class*="st-key-barni_page_header_"] [data-testid="stCaptionContainer"] {
            font-size: 0.92rem;
        }
        [class*="st-key-barni_primary_workspace_"] {
            background: var(--barni-beige);
            border: 1px solid var(--barni-border);
            border-radius: 20px;
            padding: 1.15rem 1.3rem;
            margin-bottom: 1.05rem;
            box-shadow: 0 7px 24px rgba(36, 54, 43, 0.045);
        }
        [class*="st-key-barni_primary_workspace_"] h3 {
            margin-top: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, supporting_text: str, *, key: str) -> None:
    """Render the shared title and one-sentence page introduction."""
    with st.container(key=f"barni_page_header_{key}"):
        st.markdown(f"## {title}")
        st.caption(supporting_text)


@contextmanager
def primary_workspace(*, key: str) -> Iterator[None]:
    """Group a page's primary state and actions into one visual surface."""
    with st.container(key=f"barni_primary_workspace_{key}"):
        yield
