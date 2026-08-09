from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import streamlit as st

from services.business_stories import BusinessStory
from services.evidence import source_invoice_id


def _render_story_styles() -> None:
    st.markdown(
        """
        <style>
        [class*="st-key-home_story_"],
        [class*="st-key-insights_story_"],
        [class*="st-key-feed_journal_"],
        [class*="st-key-feed_completion_story_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.11);
            border-radius: 16px;
            padding: 0.85rem 1rem;
        }
        [class*="st-key-home_story_"][class*="attention"],
        [class*="st-key-insights_story_"][class*="attention"],
        [class*="st-key-feed_journal_"][class*="attention"],
        [class*="st-key-feed_completion_story_"][class*="attention"] {
            background: #fbf4e8;
            border-color: rgba(174, 112, 42, 0.20);
        }
        [class*="st-key-home_story_"] h3,
        [class*="st-key-insights_story_"] h3,
        [class*="st-key-feed_journal_"] h3,
        [class*="st-key-feed_completion_story_"] h3 {
            color: #2f4f37;
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _open_invoice(invoice_id: int) -> None:
    st.session_state.search_selected_kind = "invoice"
    st.session_state.search_selected_value = invoice_id
    st.session_state.search_show_document = False
    st.session_state.current_page = "חיפוש חשבוניות"


def _open_identity_review() -> None:
    st.session_state.current_page = "Identity Review"


def _story_reference(story: BusinessStory) -> str:
    occurred_at = str(story.occurred_at or "").strip()
    if occurred_at:
        try:
            value = datetime.fromisoformat(occurred_at)
            return value.strftime("%d %b %Y · %H:%M") if "T" in occurred_at else value.strftime("%d %b %Y")
        except ValueError:
            return occurred_at
    if story.evidence:
        source = story.evidence[-1]
        number = f"Invoice #{source.invoice_number}" if source.invoice_number else "Source invoice"
        return f"{number} · {source.invoice_date or 'Date unavailable'}"
    return ""


def render_business_story(story: BusinessStory, *, key: str, show_evidence: bool = True) -> None:
    _render_story_styles()
    with st.container(key=f"{key}_{story.tone}"):
        st.markdown(f"### {story.icon} {story.title}")
        st.write(story.description)
        reference = _story_reference(story)
        if reference:
            st.caption(reference)
        if story.recommended_action == "Review identities":
            st.button(
                "Review identities",
                key=f"{key}_identity_action",
                on_click=_open_identity_review,
            )
        if show_evidence and story.evidence:
            with st.expander("View evidence"):
                for index, source in enumerate(story.evidence):
                    total = f" · ₪{source.total:,.2f}" if source.total is not None else ""
                    st.caption(f"{source.label}{total}")
                    evidence_ref = next(
                        (ref for ref in story.claim.evidence
                         if source_invoice_id(ref) == source.invoice_id),
                        None,
                    ) if story.claim else None
                    target_id = source_invoice_id(evidence_ref) if evidence_ref else source.invoice_id
                    st.button(
                        "Open invoice",
                        key=f"{key}_evidence_{index}_{source.invoice_id}",
                        on_click=_open_invoice,
                        args=(target_id,),
                    )


def render_business_stories(
    stories: Sequence[BusinessStory], *, key_prefix: str, show_evidence: bool = True
) -> None:
    for index, story in enumerate(stories):
        render_business_story(
            story,
            key=f"{key_prefix}_{index}",
            show_evidence=show_evidence,
        )
