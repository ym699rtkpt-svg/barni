from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from services.barni_thinking import BarniThinking, ThinkingSection


def _section(thinking: BarniThinking, name: str) -> ThinkingSection | None:
    return next((section for section in thinking.sections if section.name == name), None)


def _narrative_conclusion(thinking: BarniThinking) -> tuple[str, str]:
    """Choose the clearest existing conclusion without creating new reasoning."""
    observations = _section(thinking, "Observations")
    identity = _section(thinking, "Identity")
    confidence = _section(thinking, "Confidence")
    candidates = [
        section for section in (observations, identity, confidence)
        if section is not None and section.tone == "attention" and section.statements
    ]
    if not candidates:
        candidates = [
            section for section in (observations, identity, confidence)
            if section is not None and section.statements
        ]
    if not candidates:
        return thinking.summary, "neutral"
    selected = candidates[0]
    return selected.statements[0], selected.tone


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        [class*="st-key-barni_narrative_shell_"] {
            background: #f3f5ed;
            border: 1px solid rgba(49, 91, 61, 0.16);
            border-radius: 18px;
            padding: 1.05rem 1.2rem 1rem;
            margin: .45rem 0 1rem;
        }
        [class*="st-key-barni_narrative_conclusion_"] {
            background: #fcfbf7;
            border: 1px solid rgba(49, 91, 61, 0.10);
            border-radius: 14px;
            padding: .8rem .95rem .65rem;
            margin: .35rem 0 .75rem;
        }
        [class*="st-key-barni_narrative_conclusion_attention_"] {
            background: #fbf4e8;
            border-color: rgba(174, 112, 42, 0.20);
        }
        [class*="st-key-barni_narrative_action_"] {
            border-left: 3px solid #3f5b44;
            padding: .15rem 0 .15rem .8rem;
            margin: .45rem 0 1rem;
        }
        [class*="st-key-barni_narrative_reason_"] {
            background: rgba(252, 251, 247, 0.64);
            border: 1px solid rgba(49, 91, 61, 0.08);
            border-radius: 12px;
            padding: .65rem .8rem .5rem;
            margin-bottom: .55rem;
        }
        [class*="st-key-barni_narrative_shell_"] p {
            margin-bottom: .25rem;
        }
        [class*="st-key-barni_narrative_shell_"] h3 {
            color: #2f4f37;
            line-height: 1.35;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_barni_thinking(
    thinking: BarniThinking,
    *,
    key_prefix: str,
    on_open_evidence: Callable[[int], None] | None = None,
) -> None:
    _render_styles()
    conclusion, conclusion_tone = _narrative_conclusion(thinking)
    recommendation = _section(thinking, "Recommendation")
    identity = _section(thinking, "Identity")
    memory = _section(thinking, "Memory")
    confidence = _section(thinking, "Confidence")

    with st.container(key=f"barni_narrative_shell_{key_prefix}"):
        st.caption("BARNI'S VIEW")
        with st.container(
            key=f"barni_narrative_conclusion_{conclusion_tone}_{key_prefix}"
        ):
            st.markdown(f"### {conclusion}")

        if recommendation and recommendation.statements:
            st.caption("WHAT TO DO NEXT")
            with st.container(key=f"barni_narrative_action_{key_prefix}"):
                st.write(recommendation.statements[0])

        st.markdown("#### Why I reached this conclusion")
        for index, section in enumerate((identity, memory)):
            if section is None:
                continue
            statements = [statement for statement in section.statements if statement != conclusion]
            if not statements:
                continue
            with st.container(key=f"barni_narrative_reason_{key_prefix}_{index}"):
                for statement in statements:
                    st.write(statement)

        if confidence and confidence.statements and confidence.statements[0] != conclusion:
            with st.container(key=f"barni_narrative_reason_{key_prefix}_check"):
                st.markdown("**Before you decide**")
                st.write(confidence.statements[0])

        st.markdown("#### Supporting evidence")
        if thinking.evidence:
            with st.expander("Show supporting invoices", expanded=False):
                for insight_index, evidence in enumerate(thinking.evidence):
                    st.markdown(f"**{evidence.title}**")
                    st.caption(evidence.explanation)
                    for source_index, source in enumerate(evidence.sources):
                        amount = (
                            f" · ₪{source.total:,.2f}"
                            if source.total is not None else ""
                        )
                        detail = f"{source.invoice_date or 'Date unavailable'}{amount}"
                        if source.invoice_id is not None and on_open_evidence is not None:
                            if st.button(
                                source.label,
                                key=(
                                    f"thinking_evidence_{key_prefix}_"
                                    f"{insight_index}_{source_index}_{source.invoice_id}"
                                ),
                                help=detail,
                                width="stretch",
                            ):
                                on_open_evidence(source.invoice_id)
                                st.rerun()
                        else:
                            st.write(source.label)
                            st.caption(detail)
        else:
            st.caption(
                "This conclusion is based on the invoice details below and the "
                "Business Memory currently available."
            )
