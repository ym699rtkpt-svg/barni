from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import datetime

from database import dashboard_data
from knowledge_engine.line_classifier import is_product_line
from services.invoice_workflow import approved_documents, invoice_workflow_snapshot
from services.business_stories import BusinessStoryEngine, StoryContext
from services.visible_learning import LearningSnapshot, capture_learning_snapshot
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
    if page == "קליטה יומית":
        st.session_state["daily_intake_show_uploader"] = True
    st.session_state.current_page = page
    st.rerun()


def _money(value: float) -> str:
    return f"₪{value:,.2f}"


def _count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def _first_session_knowledge_summary(snapshot: LearningSnapshot) -> str:
    facts = [
        _count_phrase(snapshot.suppliers, "supplier"),
        _count_phrase(snapshot.products, "product"),
        _count_phrase(snapshot.invoices, "approved invoice"),
    ]
    facts = [fact for fact, count in zip(
        facts,
        (snapshot.suppliers, snapshot.products, snapshot.invoices),
    ) if count > 0]
    if not facts:
        return "I've started remembering your business."
    if len(facts) == 1:
        remembered = facts[0]
    else:
        remembered = f"{', '.join(facts[:-1])}, and {facts[-1]}"
    return f"I now remember {remembered}."


def _order_home_priorities(stories: list, *, first_session: bool) -> list:
    if not first_session:
        return stories
    return sorted(
        stories,
        key=lambda story: story.story_type == "identity_review_needed",
    )


def _monthly_activity(
    invoices: pd.DataFrame,
    *,
    current_month: pd.Period | None = None,
) -> tuple[pd.DataFrame, int, float, int]:
    """Return the existing calendar-month metrics as one testable presentation unit."""
    dated = invoices.copy()
    if dated.empty:
        dated["invoice_date_dt"] = pd.Series(dtype="datetime64[ns]")
        this_month = dated
    else:
        dated["invoice_date_dt"] = pd.to_datetime(
            dated["invoice_date"], errors="coerce"
        )
        month = current_month or pd.Timestamp.now().to_period("M")
        this_month = dated[
            dated["invoice_date_dt"].dt.to_period("M") == month
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
    return this_month, invoice_count, monthly_spend, supplier_count


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
    first_session = bool(
        st.session_state.get("barni_first_session_home_active")
    )
    first_session_summary = (
        _first_session_knowledge_summary(capture_learning_snapshot())
        if first_session
        else ""
    )

    _, invoice_count, monthly_spend, supplier_count = _monthly_activity(
        invoices
    )

    product_items = items
    if not product_items.empty:
        product_items = product_items[
            product_items.apply(
                lambda row: is_product_line(row.to_dict()),
                axis=1,
            )
        ]
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
            [1.5, .7], gap="medium", vertical_alignment="center"
        )
        with hero_copy:
            st.caption("BARNI · YOUR BUSINESS ASSISTANT")
            if first_session:
                st.markdown("## I know a little about your business now.")
                st.write(first_session_summary)
            else:
                st.markdown("## Welcome back")
                st.write(status_line)
        with hero_action:
            if st.button(
                "Continue invoice review"
                if workflow.open_count
                else "Feed Barni",
                key="home_hero_feed",
                type="primary",
                width="stretch",
            ):
                _go_to("קליטה יומית")
            st.caption(
                "Finish the invoices waiting for you."
                if workflow.open_count
                else "Upload today's invoices."
            )

    st.write("")
    st.markdown("### Invoice Workflow")
    st.caption("One shared status across Barni")
    render_workflow_status(workflow, key_prefix="home_workflow")

    st.write("")
    st.markdown("### Business Snapshot")
    st.caption(
        "Current calendar month only — separate from the total knowledge "
        "Barni remembers above."
        if first_session
        else "Activity in the current calendar month only."
    )
    overview_columns = st.columns(4, gap="medium")
    overview = [
        ("Invoices this month", f"{invoice_count:,}"),
        ("Spend this month", _money(monthly_spend)),
        ("Suppliers this month", f"{supplier_count:,}"),
        ("Products Barni knows (all time)", f"{products_tracked:,}"),
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
    priority_cards = _order_home_priorities(
        unique_cards,
        first_session=first_session,
    )[:3]
    priority_columns = st.columns(len(priority_cards), gap="medium")
    for index, (column, story) in enumerate(zip(priority_columns, priority_cards)):
        with column:
            render_business_story(
                story,
                key=f"home_story_{index}",
                show_evidence=True,
            )
