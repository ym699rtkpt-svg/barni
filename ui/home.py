from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import datetime

from ai_accountant import render_ai_accountant
from database import dashboard_data
from services.invoice_workflow import approved_documents, invoice_workflow_snapshot
from services.business_stories import BusinessStoryEngine, StoryContext
from ui.workflow_status import render_workflow_status
from ui.business_story import render_business_story


def _render_home_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-home_hero {
            background: #f7f3e9;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 20px;
            padding: 1.05rem 1.25rem;
        }
        .st-key-home_hero_ask {
            background: transparent;
            border: 0;
            padding: 0;
        }
        .st-key-home_hero h2,
        .st-key-home_hero strong,
        .st-key-home_hero label {
            color: #2f4f37;
        }
        .st-key-home_hero [data-testid="stCaptionContainer"] {
            color: #738078;
        }
        .st-key-home_ask_query [data-baseweb="input"] {
            background: #fcfbf7;
            border-color: rgba(63, 91, 68, 0.18);
        }
        .st-key-home_ask_query input {
            color: #2f4f37;
            background: #fcfbf7;
            -webkit-text-fill-color: #2f4f37;
        }
        .st-key-home_ask_query input::placeholder {
            color: #738078;
            opacity: 0.82;
            -webkit-text-fill-color: #738078;
        }
        [class*="st-key-home_metric_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.6rem 0.9rem;
        }
        [class*="st-key-home_ask_query_suggestion_"] button {
            min-height: 1.8rem;
            padding: 0.2rem 0.35rem;
            font-size: 0.74rem;
            color: #3f5b44;
            background: #fcfbf7;
            border-color: rgba(63, 91, 68, 0.18);
            box-shadow: none;
        }
        [class*="st-key-home_ask_query_suggestion_"] button:hover {
            color: #2f4f37;
            background: #eef3e8;
            border-color: rgba(63, 91, 68, 0.24);
        }
        .st-key-home_hero_feed button {
            width: 160px;
            min-height: 42px;
            padding: 0.45rem 1rem;
            border: 1px solid #3f5b44;
            border-radius: 14px;
            background: #3f5b44;
            color: #ffffff;
            font-size: 0.88rem;
            font-weight: 650;
            box-shadow: 0 5px 14px rgba(63, 91, 68, 0.18);
            transition: background-color 180ms ease,
                        border-color 180ms ease,
                        box-shadow 180ms ease,
                        transform 180ms ease;
        }
        .st-key-home_hero_feed button:hover {
            border-color: #315b3d;
            background: #315b3d;
            color: #ffffff;
            box-shadow: 0 7px 18px rgba(63, 91, 68, 0.24);
            transform: translateY(-1px);
        }
        [class*="st-key-home_priority_"] {
            background: #f8f8f4;
            border: 1px solid rgba(45, 70, 53, 0.08);
            border-radius: 16px;
            min-height: 8rem;
            padding: 0.75rem 0.9rem;
        }
        [class*="st-key-home_priority_attention_"] {
            background: #fbf4e8;
            border-color: rgba(174, 112, 42, 0.20);
        }
        [class*="st-key-home_priority_negative_"] {
            background: #faf0ed;
            border-color: rgba(151, 74, 55, 0.18);
        }
        [class*="st-key-home_priority_positive_"] {
            background: #f1f5ed;
            border-color: rgba(63, 91, 68, 0.16);
        }
        [class*="st-key-home_priority_neutral_"] {
            background: #f8f8f4;
            border-color: rgba(45, 70, 53, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value: str, key: str) -> None:
    with st.container(key=key):
        st.metric(label, value)


def _go_to(page: str) -> None:
    st.session_state.current_page = page
    st.rerun()


def _money(value: float) -> str:
    return f"₪{value:,.2f}"


def _count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def render_home():
    _render_home_styles()
    data = dashboard_data()
    workflow = invoice_workflow_snapshot()
    invoices = approved_documents()
    items = data["items"].copy()
    if not items.empty and "invoice_id" in items.columns:
        approved_ids = set(invoices.get("id", pd.Series(dtype=int)).tolist())
        items = items[items["invoice_id"].isin(approved_ids)].copy()
    business_stories = BusinessStoryEngine().generate(
        StoryContext(since=datetime.now().strftime("%Y-%m-%dT00:00:00")),
        max_stories=3,
    )

    if invoices.empty:
        invoices["invoice_date_dt"] = pd.Series(dtype="datetime64[ns]")
        this_month = invoices
    else:
        invoices["invoice_date_dt"] = pd.to_datetime(
            invoices["invoice_date"], errors="coerce"
        )
        current_month = pd.Timestamp.now().to_period("M")
        this_month = invoices[
            invoices["invoice_date_dt"].dt.to_period("M") == current_month
        ]

    invoice_count = int(len(this_month))
    monthly_spend = float(
        pd.to_numeric(this_month.get("total"), errors="coerce").fillna(0).sum()
    )
    supplier_count = int(
        this_month.get("supplier", pd.Series(dtype=str))
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    product_items = items
    if not product_items.empty and "line_type" in product_items.columns:
        product_items = product_items[product_items["line_type"] == "product"]
    products_tracked = int(
        product_items.get("description", pd.Series(dtype=str))
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    if workflow.needs_attention:
        status_line = (
            f"{_count_phrase(workflow.needs_attention, 'invoice')} need your attention."
        )
    elif workflow.pending_review:
        status_line = (
            f"{_count_phrase(workflow.pending_review, 'invoice')} waiting for approval."
        )
    elif workflow.duplicate:
        status_line = f"I found {_count_phrase(workflow.duplicate, 'duplicate invoice')}."
    elif workflow.learning:
        status_line = f"Barni is learning from {_count_phrase(workflow.learning, 'invoice')}."
    elif business_stories:
        status_line = business_stories[0].description
    elif invoices.empty:
        status_line = "Feed me an invoice and I will start building your business picture."
    else:
        status_line = (
            "Everything looks calm today. I’m watching supplier prices "
            "and recent invoices."
        )

    with st.container(key="home_hero"):
        hero_copy, hero_action = st.columns(
            [1, 1], gap="medium", vertical_alignment="center"
        )
        with hero_copy:
            st.caption("BARNI · YOUR BUSINESS ASSISTANT")
            st.markdown("## Welcome back")
            st.write(status_line)
        with hero_action:
            with st.container(key="home_hero_ask"):
                st.markdown("**Ask Barni**")
                st.caption("Ask about invoices, suppliers or spending")
                render_ai_accountant(
                    compact=True,
                    query_key="home_ask_query",
                    input_label="Ask Barni",
                    input_placeholder="Ask anything about your business...",
                    helper_text="Ask in English or Hebrew.",
                    hide_input_label=True,
                    suggested_questions=[
                        "What changed this week?",
                        "Which supplier raised prices?",
                        "Show me unusual invoices",
                    ],
                )
                if st.button(
                    "⬆ Feed Barni",
                    key="home_hero_feed",
                    type="primary",
                ):
                    _go_to("קליטה יומית")

    st.write("")
    st.markdown("### Invoice Workflow")
    st.caption("One shared status across Barni")
    render_workflow_status(workflow, key_prefix="home_workflow")

    st.write("")
    st.markdown("### Business Snapshot")
    st.caption("This month at a glance")
    overview_columns = st.columns(4, gap="medium")
    overview = [
        ("Invoices this month", f"{invoice_count:,}"),
        ("Spend this month", _money(monthly_spend)),
        ("Suppliers this month", f"{supplier_count:,}"),
        ("Products tracked", f"{products_tracked:,}"),
    ]
    for index, (column, (label, value)) in enumerate(zip(overview_columns, overview)):
        with column:
            _metric_card(label, value, key=f"home_metric_{index}")

    st.write("")
    st.markdown("### Barni Priorities Today")
    st.caption("Your morning briefing — only what matters now")
    latest_story = st.session_state.get("barni_latest_business_story")
    priority_cards = ([latest_story] if latest_story else []) + business_stories
    unique_cards = []
    seen = set()
    for story in priority_cards:
        key = (story.story_type, tuple(source.invoice_id for source in story.evidence))
        if key not in seen:
            seen.add(key)
            unique_cards.append(story)
    priority_cards = unique_cards[:3]
    priority_columns = st.columns(len(priority_cards), gap="medium")
    for index, (column, story) in enumerate(zip(priority_columns, priority_cards)):
        with column:
            render_business_story(
                story,
                key=f"home_story_{index}",
                show_evidence=True,
            )
