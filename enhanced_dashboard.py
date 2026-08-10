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
        .st-key-insights_low_data {
            max-width: 760px;
            background: #f7f3e9;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 16px;
            padding: 1rem 1.15rem .85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _has_spend_trend_evidence(monthly: pd.DataFrame) -> bool:
    """A time trend requires spending observations in two distinct months."""
    return (
        not monthly.empty
        and "month" in monthly.columns
        and monthly["month"].replace("", pd.NA).dropna().nunique() >= 2
    )


def _supplier_comparison_data(documents: pd.DataFrame) -> pd.DataFrame:
    """Compare only suppliers supported by repeat approved purchases."""
    if documents.empty or not {"supplier", "total"}.issubset(documents.columns):
        return pd.DataFrame(columns=["supplier", "total", "invoice_count"])
    values = documents.copy()
    values["supplier"] = values["supplier"].fillna("").astype(str).str.strip()
    values = values[values["supplier"] != ""]
    values["total"] = pd.to_numeric(values["total"], errors="coerce").fillna(0)
    comparison = (
        values.groupby("supplier")["total"]
        .agg(total="sum", invoice_count="count")
        .reset_index()
    )
    comparison = comparison[comparison["invoice_count"] >= 2]
    if len(comparison) < 2:
        return comparison.iloc[0:0]
    return comparison.sort_values("total", ascending=False).head(10)


def _meaningful_category_data(documents: pd.DataFrame) -> pd.DataFrame:
    """Keep raw records intact while suppressing mostly-uncategorized analysis."""
    columns = ["category", "subcategory", "documents_count", "total"]
    if documents.empty or "category" not in documents.columns:
        return pd.DataFrame(columns=columns)
    values = documents.copy()
    normalized = values["category"].fillna("").astype(str).str.strip().str.casefold()
    unknown = normalized.isin({"", "לא מסווג", "uncategorized", "not classified"})
    if int((~unknown).sum()) <= int(unknown.sum()):
        return pd.DataFrame(columns=columns)
    values = values[~unknown].copy()
    return (
        values.groupby(["category", "subcategory"], dropna=False)["total"]
        .agg(documents_count="count", total="sum")
        .reset_index()
        .sort_values("total", ascending=False)
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
        supplier_spend = pd.DataFrame(columns=["supplier", "total", "invoice_count"])
        document_types = pd.DataFrame(columns=["document_type", "count"])
        categories = pd.DataFrame(columns=["category", "subcategory", "documents_count", "total"])
    else:
        documents = documents.copy()
        documents["total"] = pd.to_numeric(documents["total"], errors="coerce")
        documents["_date"] = pd.to_datetime(documents["invoice_date"], errors="coerce")
        documents["month"] = documents["_date"].dt.to_period("M").astype(str)
        monthly = documents.groupby("month")["total"].sum().reset_index().sort_values("month")
        supplier_spend = _supplier_comparison_data(documents)
        document_types = documents["document_type"].replace("", "Not identified").value_counts().rename_axis("document_type").reset_index(name="count")
        categories = _meaningful_category_data(documents)

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
            if not _has_spend_trend_evidence(monthly):
                st.caption(
                    "Barni is still learning. Spending across another month will "
                    "make this trend useful."
                )
            else:
                st.line_chart(monthly.set_index("month")["total"], height=260)
    with right:
        with st.container(key="insights_chart_suppliers"):
            st.markdown("#### Top suppliers")
            if supplier_spend.empty:
                st.caption(
                    "Barni is still learning. A useful comparison needs repeat "
                    "purchases from more than one supplier."
                )
            else:
                st.bar_chart(supplier_spend.set_index("supplier")["total"], height=260)

    st.write("")
    st.markdown("### More detail")
    st.caption("Supporting breakdowns for deeper review")
    category_tab, document_tab = st.tabs(["Categories", "Document types"])
    with category_tab:
        if categories.empty:
            st.caption(
                "Barni does not yet have enough reliable category information."
            )
        else:
            st.dataframe(categories, hide_index=True, width="stretch")
    with document_tab:
        if document_types.empty:
            st.caption("No document types are available yet.")
        else:
            st.dataframe(document_types, hide_index=True, width="stretch")
