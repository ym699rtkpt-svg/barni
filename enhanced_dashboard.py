from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from services.business_stories import BusinessStoryEngine, StoryContext
from services.invoice_workflow import approved_documents, invoice_workflow_snapshot
from services.business_identity import BusinessIdentityRepository
from ui.business_story import render_business_stories


def _open_feed() -> None:
    st.session_state.current_page = "קליטה יומית"


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-insights_hero {
            background: #f7f3e9;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 20px;
            padding: 1.35rem 1.55rem;
        }
        [class*="st-key-insights_metric_"],
        [class*="st-key-insights_chart_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.85rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_control_center() -> dict:
    documents = approved_documents()
    workflow = invoice_workflow_snapshot()
    total_vat = (
        float(documents["vat"].fillna(0).sum())
        if not documents.empty and "vat" in documents.columns
        else 0.0
    )
    supplier_count = BusinessIdentityRepository().identity_health()["suppliers"]
    data = {
        "invoice_count": len(documents),
        "supplier_count": supplier_count,
        "vat_total": total_vat,
        "review_count": workflow.needs_attention,
    }
    st.markdown("### Supporting overview")
    st.caption("Context behind Barni's stories")
    metrics = [
        ("Invoices", data["invoice_count"]),
        ("Suppliers", data["supplier_count"]),
        ("VAT", f"₪{data['vat_total']:,.2f}"),
        ("Needs review", data["review_count"]),
    ]
    columns = st.columns(4, gap="medium")
    for index, (column, (label, value)) in enumerate(zip(columns, metrics)):
        with column:
            with st.container(key=f"insights_metric_{index}"):
                st.metric(label, value)
    return data


def render_enhanced_dashboard() -> None:
    _render_styles()
    stories = BusinessStoryEngine().generate(
        StoryContext(since=datetime.now().strftime("%Y-%m-%dT00:00:00")),
        max_stories=3,
    )
    with st.container(key="insights_hero"):
        st.caption("WHAT CHANGED")
        st.markdown("## Insights")
        st.write("The most important supported changes in Business Memory.")
    st.write("")
    render_business_stories(stories, key_prefix="insights_story")
    st.write("")
    render_control_center()
    documents = approved_documents()
    if documents.empty:
        monthly = pd.DataFrame(columns=["month", "total"])
        supplier_spend = pd.DataFrame(columns=["supplier", "total"])
        document_types = pd.DataFrame(columns=["document_type", "count"])
        categories = pd.DataFrame(columns=["category", "subcategory", "documents_count", "total"])
    else:
        documents = documents.copy()
        documents["total"] = pd.to_numeric(documents["total"], errors="coerce")
        documents["_date"] = pd.to_datetime(documents["invoice_date"], errors="coerce")
        documents["month"] = documents["_date"].dt.to_period("M").astype(str)
        monthly = documents.groupby("month")["total"].sum().reset_index().sort_values("month")
        supplier_spend = documents.groupby("supplier")["total"].sum().sort_values(ascending=False).reset_index().head(10)
        document_types = documents["document_type"].replace("", "Not identified").value_counts().rename_axis("document_type").reset_index(name="count")
        categories = documents.groupby(["category", "subcategory"], dropna=False)["total"].agg(documents_count="count", total="sum").reset_index().sort_values("total", ascending=False)

    if documents.empty:
        st.write("")
        st.markdown(
            '<div class="barni-empty-state">No approved invoices yet. Feed Barni an invoice to start seeing purchasing patterns.</div>',
            unsafe_allow_html=True,
        )
        st.button("Feed Barni", type="primary", on_click=_open_feed)
        return

    st.write("")
    st.markdown("### Purchasing activity")
    st.caption("Spend patterns from approved invoices")
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(key="insights_chart_monthly"):
            st.markdown("#### Spend by month")
            if monthly.empty:
                st.caption("No dated purchasing history is available yet.")
            else:
                st.line_chart(monthly.set_index("month")["total"], height=260)
    with right:
        with st.container(key="insights_chart_suppliers"):
            st.markdown("#### Top suppliers")
            if supplier_spend.empty:
                st.caption("No supplier spend is available yet.")
            else:
                st.bar_chart(supplier_spend.set_index("supplier")["total"], height=260)

    st.write("")
    st.markdown("### More detail")
    st.caption("Supporting breakdowns for deeper review")
    category_tab, document_tab = st.tabs(["Categories", "Document types"])
    with category_tab:
        if categories.empty:
            st.caption("No categories have been learned yet.")
        else:
            st.dataframe(categories, hide_index=True, width="stretch")
    with document_tab:
        if document_types.empty:
            st.caption("No document types are available yet.")
        else:
            st.dataframe(document_types, hide_index=True, width="stretch")
