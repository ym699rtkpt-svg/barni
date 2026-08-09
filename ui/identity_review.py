from __future__ import annotations

from pathlib import Path

import streamlit as st

from services.business_identity import BusinessIdentityRepository, InvoiceEvidence
from services.identity_review import IdentityReviewCandidate, IdentityReviewService


def _styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-identity_review_hero {
            max-width: 900px; background: #f7f3e9;
            border: 1px solid rgba(45,70,53,.12); border-radius: 20px;
            padding: 1.25rem 1.45rem .95rem; margin-bottom: 1rem;
        }
        .st-key-identity_review_card {
            max-width: 900px; background: #fcfbf7;
            border: 1px solid rgba(45,70,53,.12); border-radius: 18px;
            padding: 1rem 1.15rem .8rem;
            box-shadow: 0 5px 18px rgba(36,54,43,.05);
        }
        [class*="st-key-review_evidence_"] {
            background: #f8f8f4; border: 1px solid rgba(45,70,53,.09);
            border-radius: 14px; padding: .75rem .85rem;
        }
        .identity-confidence {
            display: inline-block; color: #315b3d; background: #e7eee2;
            border-radius: 999px; padding: .22rem .58rem;
            font-size: .78rem; font-weight: 700;
        }
        .identity-pair {
            color: #24362b; font-size: 1.05rem; font-weight: 700;
            margin: .35rem 0 .7rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _back_to_memory() -> None:
    st.session_state.current_page = "Business Memory"
    st.session_state.pop("identity_review_selected", None)


def _money(value) -> str:
    try:
        return f"₪{float(value):,.2f}"
    except (TypeError, ValueError):
        return "Unknown amount"


def _evidence_card(source: InvoiceEvidence, key: str) -> None:
    with st.container(key=f"review_evidence_{key}"):
        st.markdown(f"**{source.supplier or 'Missing supplier'}**")
        number = f"Invoice #{source.invoice_number}" if source.invoice_number else "No invoice number"
        st.caption(f"{number} · {source.invoice_date or 'Date unavailable'} · {_money(source.total)}")
        path = Path(source.archived_path) if source.archived_path else None
        if path and path.exists():
            if path.suffix.lower() == ".pdf":
                try:
                    st.pdf(path.read_bytes(), height=270)
                except Exception:
                    st.download_button("Open original invoice", path.read_bytes(), path.name, key=f"download_{key}")
            else:
                st.image(str(path), width="stretch")
        else:
            st.caption("The original preview is unavailable. Stored invoice details remain as evidence.")


def _resolve(
    service: IdentityReviewService, candidate: IdentityReviewCandidate,
    action: str, keep_canonical_id: int | None = None,
) -> None:
    try:
        if action == "confirm":
            service.confirm(candidate.id, keep_canonical_id=keep_canonical_id)
            message = "Thanks. I’ll remember these as one identity."
        elif action == "reject":
            service.reject(candidate.id)
            message = "Understood. I’ll keep these identities separate."
        else:
            service.acknowledge(candidate.id)
            message = "Understood. I’ll keep these observations separate."
    except (ValueError, RuntimeError):
        st.error("I couldn't save this decision. Nothing changed. Review the evidence and try again.")
        return
    st.session_state.identity_review_message = message
    st.session_state.pop("identity_review_selected", None)
    st.rerun()


def _review_card(service: IdentityReviewService, candidate: IdentityReviewCandidate) -> None:
    with st.container(key="identity_review_card"):
        st.caption("WHAT I THINK")
        st.markdown(f"### {candidate.title}")
        st.write(candidate.explanation)
        if candidate.source_id != candidate.target_id:
            st.markdown(
                f'<div class="identity-pair">{candidate.source_name} &nbsp;⇄&nbsp; {candidate.target_name}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<span class="identity-confidence">{candidate.confidence:.0%} confidence</span>',
            unsafe_allow_html=True,
        )

        st.markdown("#### Why I think so")
        for reason in candidate.reasons:
            st.markdown(f"- {reason}")

        st.markdown("#### Supporting evidence")
        if candidate.evidence:
            visible = candidate.evidence[:2]
            columns = st.columns(len(visible), gap="medium")
            for index, (column, source) in enumerate(zip(columns, visible)):
                with column:
                    _evidence_card(source, f"{candidate.id}_{index}")
            if len(candidate.evidence) > 2:
                with st.expander(f"See {len(candidate.evidence) - 2} more source invoices"):
                    for source in candidate.evidence[2:]:
                        st.write(source.label)
        else:
            st.caption("The original record is unavailable, so Barni will not resolve this automatically.")

        st.write("")
        if candidate.review_type in {"supplier_match", "product_match"}:
            keep_id = st.radio(
                "Canonical name to keep",
                [candidate.source_id, candidate.target_id],
                format_func=lambda value: candidate.source_name if value == candidate.source_id else candidate.target_name,
                horizontal=True,
                key=f"keep_identity_{candidate.id}",
            )
            confirm, reject = st.columns(2)
            if confirm.button("✓ Confirm Match", type="primary", width="stretch", key=f"confirm_{candidate.id}"):
                _resolve(service, candidate, "confirm", keep_id)
            if reject.button("✗ Keep Separate", width="stretch", key=f"reject_{candidate.id}"):
                _resolve(service, candidate, "reject")
            st.caption("If you confirm this once, I won’t ask again unless conflicting evidence appears.")
        else:
            if st.button("✓ I reviewed this — keep observations separate", type="primary", width="stretch", key=f"ack_{candidate.id}"):
                _resolve(service, candidate, "acknowledge")
            st.caption("Barni will not compare these observations as if they were equivalent.")


def _manual_corrections(service: IdentityReviewService) -> None:
    identities = service.identities
    suppliers = {value.id: value for value in identities.suppliers()}
    products = {value.id: value for value in identities.products()}
    with st.expander("Correct something Barni already remembers", expanded=False):
        st.caption("Use these controls only when the queue does not describe the correction you need.")
        action = st.radio("Correction", ["Merge", "Split", "Rename"], horizontal=True)
        entity_type = st.radio("Identity", ["supplier", "product"], horizontal=True, key="correction_type")
        options = suppliers if entity_type == "supplier" else products
        if not options:
            st.caption("No identities are available yet.")
            return
        if action == "Merge" and len(options) >= 2:
            with st.form("manual_identity_merge"):
                source = st.selectbox("Merge this identity", list(options), format_func=lambda value: options[value].canonical_name)
                target = st.selectbox("Into this canonical identity", list(options), index=1, format_func=lambda value: options[value].canonical_name)
                reason = st.text_input("Why are they the same?", placeholder="Same real product or supplier")
                if st.form_submit_button("⇄ Merge identities"):
                    try:
                        if entity_type == "supplier":
                            identities.merge_suppliers(source, target, reason=reason or "Manually confirmed as the same supplier")
                        else:
                            identities.merge_products(source, target, reason=reason or "Manually confirmed as the same product")
                    except ValueError:
                        st.error("I couldn't merge these identities. Choose two different identities and try again.")
                    else:
                        st.success("Barni now remembers one canonical identity.")
                        st.rerun()
        elif action == "Split":
            canonical_id = st.selectbox("Identity to split", list(options), format_func=lambda value: options[value].canonical_name)
            records = service.identity_records(entity_type, canonical_id)
            record_options = {record.record_id: record for record in records}
            with st.form("manual_identity_split"):
                selected = st.multiselect("Evidence that belongs to the new identity", list(record_options), format_func=lambda value: record_options[value].label)
                new_name = st.text_input("New canonical name")
                reason = st.text_input("Why should these records be separate?")
                if st.form_submit_button("⇅ Split identity"):
                    try:
                        identities.split_identity(entity_type, canonical_id, selected, new_name, reason=reason or "Evidence belongs to a separate identity")
                    except ValueError:
                        st.error("I couldn't split this identity. Select the source evidence and provide a new name.")
                    else:
                        st.success("The evidence now belongs to a separate identity.")
                        st.rerun()
        elif action == "Rename":
            with st.form("manual_identity_rename"):
                canonical_id = st.selectbox("Identity to rename", list(options), format_func=lambda value: options[value].canonical_name)
                new_name = st.text_input("Canonical name")
                if st.form_submit_button("✎ Rename identity"):
                    try:
                        identities.rename_identity(entity_type, canonical_id, new_name)
                    except ValueError:
                        st.error("I couldn't rename this identity. Enter a clear name and try again.")
                    else:
                        st.success("The canonical name has been updated without changing source invoices.")
                        st.rerun()


def _decision_history(service: IdentityReviewService) -> None:
    decisions = service.decisions()
    with st.expander("Previous teaching decisions", expanded=False):
        if not decisions:
            st.caption("No identity decisions yet.")
            return
        for decision in decisions:
            columns = st.columns([4, 1], vertical_alignment="center")
            columns[0].markdown(f"**{decision.label}**")
            columns[0].caption(f"{decision.reason or decision.decision_type} · {decision.actor} · {decision.decided_at}")
            if decision.reversible and columns[1].button("↩ Undo", key=f"undo_identity_{decision.id}"):
                try:
                    service.undo(decision.id)
                except ValueError:
                    st.error("I couldn't undo this decision. Nothing changed. Refresh the review and try again.")
                else:
                    st.success("The previous decision was undone. No source evidence was deleted.")
                    st.rerun()


def render_identity_review() -> None:
    _styles()
    service = IdentityReviewService()
    st.button("← Business Memory", on_click=_back_to_memory)
    candidates = service.pending(limit=5)

    with st.container(key="identity_review_hero"):
        st.caption("BARNI'S LEARNING CLASSROOM")
        st.markdown("## Help Barni learn")
        if candidates:
            st.write(f"I found {len(candidates)} valuable identity review{'s' if len(candidates) != 1 else ''}. One answer can improve future comparisons.")
        else:
            st.write("I don’t need help with any important identity right now.")

    message = st.session_state.pop("identity_review_message", None)
    if message:
        st.success(message)

    if candidates:
        candidate_ids = {candidate.id: candidate for candidate in candidates}
        selected_id = st.session_state.get("identity_review_selected")
        if selected_id not in candidate_ids:
            selected_id = candidates[0].id
            st.session_state.identity_review_selected = selected_id
        if len(candidates) > 1:
            selected_id = st.selectbox(
                "Review", list(candidate_ids), index=list(candidate_ids).index(selected_id),
                format_func=lambda value: candidate_ids[value].title,
                key="identity_review_picker",
            )
        _review_card(service, candidate_ids[selected_id])
    else:
        st.success("Everything Barni remembers is consistent enough for now.")

    st.write("")
    _manual_corrections(service)
    _decision_history(service)
