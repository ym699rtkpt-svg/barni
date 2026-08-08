from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from services.invoice_intelligence import Insight


def render_barni_noticed(
    insights: Sequence[Insight],
    *,
    key_prefix: str,
) -> None:
    st.markdown(
        """
        <style>
        [class*="st-key-barni_notice_"] {
            background: rgba(252, 251, 247, 0.78);
            border: 1px solid rgba(49, 91, 61, 0.10);
            border-radius: 12px;
            padding: .55rem .7rem .42rem;
            margin-bottom: .45rem;
        }
        [class*="st-key-barni_notice_"] p:first-child {
            margin-bottom: .12rem;
            color: #24362b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Barni noticed")
    if not insights:
        st.caption("Everything looks normal.")
        return

    for index, insight in enumerate(insights[:3]):
        with st.container(key=f"barni_notice_{key_prefix}_{index}"):
            st.markdown(f"{insight.icon} **{insight.title}**")
            st.write(insight.description)
