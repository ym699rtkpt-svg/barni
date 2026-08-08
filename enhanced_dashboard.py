from __future__ import annotations

from datetime import datetime

import streamlit as st

from categorizer import classify_all
from database import category_summary, control_center_data, dashboard_data
from services.business_stories import BusinessStoryEngine, StoryContext
from ui.business_story import render_business_stories


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
    data = control_center_data()
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
    control = render_control_center()
    data = dashboard_data()
    documents = data["documents"]

    if documents.empty:
        st.write("")
        st.markdown(
            '<div class="barni-empty-state">No approved invoices yet. Feed Barni an invoice to start seeing purchasing patterns.</div>',
            unsafe_allow_html=True,
        )
        return

    st.write("")
    st.markdown("### Purchasing activity")
    st.caption("Spend patterns from approved invoices")
    monthly = data["monthly_spend"]
    supplier_spend = data["supplier_spend"].head(10)
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
    categories = category_summary()
    category_tab, document_tab = st.tabs(["Categories", "Document types"])
    with category_tab:
        if categories.empty:
            st.caption("No categories have been learned yet.")
        else:
            st.dataframe(categories, hide_index=True, width="stretch")
    with document_tab:
        if data["document_types"].empty:
            st.caption("No document types are available yet.")
        else:
            st.dataframe(data["document_types"], hide_index=True, width="stretch")

    with st.expander("Internal maintenance"):
        st.caption("Use only when reviewing invoice categorization during the pilot.")
        if st.button("Refresh expense categories", width="stretch"):
            with st.spinner("Barni is reviewing categories..."):
                result = classify_all()
            st.success(f"Reviewed {result['processed']} documents.")
            st.rerun()
