import streamlit as st

from ai_accountant import render_ai_accountant


def render_home():
    st.subheader("🥚 Barni")
    st.caption("I learn your business from every document you add.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Feed Barni")
        st.write("Upload invoices to expand your business memory.")

    with col2:
        st.markdown("### What I Already Know")
        st.write("Suppliers, invoices, products, prices, and trends.")

    st.info(
        "Barni is still at the beginning of its evolution. "
        "As more information comes in, the insights will become "
        "more accurate and useful."
    )

    st.markdown("---")
    st.markdown("## 💬 Ask Barni")
    st.caption(
        "Ask about suppliers, invoices, expenses, "
        "and the business information I have already learned."
    )

    render_ai_accountant()