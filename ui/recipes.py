from __future__ import annotations

import streamlit as st


def render_recipes() -> None:
    st.markdown("## Recipes")
    st.caption("Understand what each dish costs and where the price comes from.")

    st.write("")
    st.markdown(
        """
        <div class="barni-empty-state">
            Recipe costing is not ready for your business data yet. Barni will only
            show recipe costs after ingredients, quantities, and product matches can
            be supported by stored information.
        </div>
        """,
        unsafe_allow_html=True,
    )
