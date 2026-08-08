from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from database import search_invoices
from services.invoice_intelligence import (
    Category,
    Insight,
    Severity,
    select_proactive_insights,
)
from services.invoice_intelligence_adapter import analyze_invoice_record
from services.business_identity import BusinessIdentityRepository, InvoiceEvidence


@dataclass(frozen=True)
class ThinkingSection:
    name: str
    prompt: str
    statements: tuple[str, ...]
    tone: str = "neutral"


@dataclass(frozen=True)
class BarniThinking:
    summary: str
    sections: tuple[ThinkingSection, ...]
    evidence: tuple["ThinkingEvidence", ...] = ()


@dataclass(frozen=True)
class ThinkingEvidence:
    title: str
    explanation: str
    sources: tuple[InvoiceEvidence, ...]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _same_supplier(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_canonical = left.get("canonical_supplier_id")
    right_canonical = right.get("canonical_supplier_id")
    if left_canonical and right_canonical:
        return int(left_canonical) == int(right_canonical)
    left_id = _text(left.get("supplier_id"))
    right_id = _text(right.get("supplier_id"))
    if left_id and right_id:
        return left_id == right_id
    left_name = _text(left.get("supplier")).casefold()
    right_name = _text(right.get("supplier")).casefold()
    return bool(left_name and right_name and left_name == right_name)


def _previous_supplier_invoices(
    invoice: Mapping[str, Any],
    invoices: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    current_id = int(invoice.get("id") or 0)
    return [
        record
        for record in invoices
        if _same_supplier(record, invoice)
        and (not current_id or int(record.get("id") or 0) != current_id)
    ]


def _identity_section(invoice: Mapping[str, Any]) -> ThinkingSection:
    supplier = _text(invoice.get("canonical_supplier_name") or invoice.get("supplier"))
    document_type = _text(invoice.get("document_type"))
    if supplier and document_type:
        statement = f"I believe this is a {document_type} from {supplier}."
        tone = "positive"
    elif supplier:
        statement = (
            f"I believe this document belongs to {supplier}, but I need your help "
            "confirming what kind of document it is."
        )
        tone = "attention"
    elif document_type:
        statement = (
            f"This looks like a {document_type}, but I couldn't confidently identify "
            "the supplier."
        )
        tone = "attention"
    else:
        statement = (
            "I can see this is a business document, but I need your help identifying "
            "the supplier and document type."
        )
        tone = "attention"
    return ThinkingSection("Identity", "What is this document?", (statement,), tone)


def _memory_section(
    invoice: Mapping[str, Any],
    previous: Sequence[Mapping[str, Any]],
) -> ThinkingSection:
    supplier = _text(invoice.get("canonical_supplier_name") or invoice.get("supplier"))
    if not supplier:
        statement = (
            "I need a confirmed supplier before I can connect this invoice to "
            "Business Memory."
        )
        tone = "attention"
    elif previous:
        count = len(previous)
        noun = "invoice" if count == 1 else "invoices"
        statement = f"I found {count} previous {noun} from {supplier}."
        tone = "neutral"
    else:
        statement = f"I haven't seen a previous invoice from {supplier} yet."
        tone = "positive"
    return ThinkingSection("Memory", "What do I already know?", (statement,), tone)


def _observation_section(insights: Sequence[Insight]) -> ThinkingSection:
    meaningful_categories = {
        Category.PRICE,
        Category.PRODUCT,
        Category.DUPLICATE,
        Category.SPEND,
        Category.TAX,
        Category.BEHAVIOR,
    }
    proactive = select_proactive_insights(insights)
    candidates = proactive or list(insights)
    observations = tuple(
        insight.description
        for insight in candidates
        if insight.category in meaningful_categories
    )[:2]
    if not observations:
        return ThinkingSection(
            "Observations",
            "What changed?",
            (
                "I don't see an important change supported by the business history I have.",
            ),
        )
    attention = any(
        insight.category in meaningful_categories
        and insight.severity in {Severity.ATTENTION, Severity.WARNING}
        for insight in candidates
    )
    return ThinkingSection(
        "Observations",
        "What changed?",
        observations,
        "attention" if attention else "positive",
    )


def _surfaced_observation_insights(insights: Sequence[Insight]) -> list[Insight]:
    meaningful_categories = {
        Category.PRICE,
        Category.PRODUCT,
        Category.DUPLICATE,
        Category.SPEND,
        Category.TAX,
        Category.BEHAVIOR,
    }
    proactive = select_proactive_insights(insights)
    candidates = proactive or list(insights)
    return [
        insight for insight in candidates
        if insight.category in meaningful_categories
    ][:2]


def _missing_key_details(invoice: Mapping[str, Any]) -> list[str]:
    fields = (
        ("supplier", "supplier"),
        ("invoice_number", "invoice number"),
        ("invoice_date", "invoice date"),
        ("total", "total"),
    )
    return [label for field, label in fields if invoice.get(field) in (None, "")]


def _has_recorded_uncertainty(invoice: Mapping[str, Any]) -> bool:
    if invoice.get("machine_issues") or invoice.get("model_notes"):
        return True
    try:
        confidence = float(invoice.get("confidence"))
    except (TypeError, ValueError):
        return False
    return confidence < 0.90


def _confidence_section(invoice: Mapping[str, Any]) -> ThinkingSection:
    missing = _missing_key_details(invoice)
    has_recorded_uncertainty = _has_recorded_uncertainty(invoice)
    try:
        confidence = float(invoice.get("confidence"))
    except (TypeError, ValueError):
        confidence = None

    if missing:
        if len(missing) == 1:
            detail_text = missing[0]
        else:
            detail_text = ", ".join(missing[:-1]) + f" and {missing[-1]}"
        statement = f"I need your help checking the {detail_text}."
        tone = "attention"
    elif has_recorded_uncertainty:
        statement = "Some details still need a careful check before I learn from this invoice."
        tone = "attention"
    elif confidence is None:
        statement = "I have enough information to explain this invoice, but please check the key details."
        tone = "neutral"
    else:
        statement = "The key details look consistent enough for your review."
        tone = "positive"
    return ThinkingSection("Confidence", "What am I unsure about?", (statement,), tone)


def _recommendation_section(
    invoice: Mapping[str, Any],
    insights: Sequence[Insight],
) -> ThinkingSection:
    categories = {insight.category for insight in insights}
    missing = _missing_key_details(invoice)
    already_approved = _text(invoice.get("status")).lower() == "approved"
    insight_needs_attention = any(
        insight.severity in {Severity.ATTENTION, Severity.WARNING}
        for insight in insights
    )
    recommended = next(
        (
            insight.recommended_next_action
            for insight in select_proactive_insights(insights)
            if insight.recommended_next_action
        ),
        None,
    )
    if already_approved and (missing or insight_needs_attention or _has_recorded_uncertainty(invoice)):
        statement = (
            "This invoice is already in Business Memory. Review the detail I flagged "
            "and update it if necessary."
        )
        tone = "attention"
    elif already_approved:
        statement = "This invoice is already in Business Memory. Review the evidence below if you need more detail."
        tone = "positive"
    elif Category.DUPLICATE in categories:
        statement = recommended or "Compare this with the invoice I already remember before deciding whether to keep it."
        tone = "attention"
    elif recommended:
        statement = recommended
        tone = "attention"
    elif missing or insight_needs_attention or _has_recorded_uncertainty(invoice):
        statement = "Check the details I flagged below, correct anything necessary, then approve it."
        tone = "attention"
    else:
        statement = "Review the invoice below. If it looks right, approve it and I will remember it."
        tone = "positive"
    return ThinkingSection("Recommendation", "What should you do?", (statement,), tone)


def think_about_invoice(
    invoice: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]] | None = None,
    invoices: Sequence[Mapping[str, Any]] | None = None,
) -> BarniThinking:
    invoice_record = dict(invoice)
    item_records = [dict(item) for item in (items or invoice_record.get("items") or [])]
    history = (
        [dict(record) for record in invoices]
        if invoices is not None
        else search_invoices(statuses=[]).to_dict("records")
    )
    identities = BusinessIdentityRepository()
    if invoices is None:
        supplier_identity = identities.supplier_identity(
            _text(invoice_record.get("supplier")),
            _text(invoice_record.get("supplier_id")),
        )
        if supplier_identity is not None:
            invoice_record["canonical_supplier_id"] = supplier_identity.id
            invoice_record["canonical_supplier_name"] = supplier_identity.canonical_name
    elif not invoice_record.get("canonical_supplier_id"):
        supplier_id = _text(invoice_record.get("supplier_id"))
        supplier_name = _text(invoice_record.get("supplier")).casefold()
        known_identity = next(
            (
                record for record in history
                if (
                    supplier_id
                    and _text(record.get("supplier_id")) == supplier_id
                    or supplier_name
                    and _text(record.get("supplier")).casefold() == supplier_name
                )
                and record.get("canonical_supplier_id")
            ),
            None,
        )
        if known_identity is not None:
            invoice_record["canonical_supplier_id"] = known_identity["canonical_supplier_id"]
            invoice_record["canonical_supplier_name"] = known_identity.get("canonical_supplier_name")
    insights = analyze_invoice_record(
        invoice_record,
        item_records,
        history,
        max_insights=10,
    )
    previous = _previous_supplier_invoices(invoice_record, history)
    sections = (
        _identity_section(invoice_record),
        _memory_section(invoice_record, previous),
        _observation_section(insights),
        _confidence_section(invoice_record),
        _recommendation_section(invoice_record, insights),
    )
    evidence_records = {
        int(record.get("id") or 0): record
        for record in [*history, invoice_record]
        if int(record.get("id") or 0) > 0
    }

    def sources_for(insight: Insight) -> tuple[InvoiceEvidence, ...]:
        if invoices is None:
            return identities.resolve_evidence(insight.source_record_ids)
        sources = []
        for source_id in insight.source_record_ids:
            try:
                record = evidence_records.get(int(source_id))
            except (TypeError, ValueError):
                record = None
            if record is None:
                continue
            sources.append(InvoiceEvidence(
                source_record_id=source_id,
                invoice_id=int(record.get("id") or 0),
                supplier=_text(record.get("canonical_supplier_name") or record.get("supplier")),
                invoice_number=_text(record.get("invoice_number")),
                invoice_date=_text(record.get("invoice_date")),
                total=record.get("total"),
                document_type=_text(record.get("document_type")),
                archived_path=_text(record.get("archived_path")),
            ))
        return tuple(sources)

    evidence = tuple(
        ThinkingEvidence(
            title=insight.title,
            explanation=insight.explanation,
            sources=sources_for(insight),
        )
        for insight in _surfaced_observation_insights(insights)
        if insight.source_record_ids
    )
    needs_attention = any(section.tone == "attention" for section in sections)
    summary = (
        "I found a few details worth checking before I learn from this invoice."
        if needs_attention
        else "I understand the key details. Here is what I think matters."
    )
    return BarniThinking(summary=summary, sections=sections, evidence=evidence)
