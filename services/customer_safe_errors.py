from __future__ import annotations

from pathlib import Path
from typing import Mapping


_ISSUE_MESSAGES = {
    "missing_supplier": "Check the supplier.",
    "missing_supplier_id": "Check the supplier number.",
    "missing_invoice_number": "Check the invoice number.",
    "missing_invoice_date": "Check the invoice date.",
    "missing_document_type": "Check the document type.",
    "missing_total": "Check the total.",
    "missing_line_items": "Check the products.",
    "missing_taxable_amount": "Check the amount before VAT.",
    "missing_exempt_amount": "Check the VAT-exempt amount.",
    "missing_vat": "Check the VAT amount.",
    "missing_statement_month": "Check the statement month.",
    "amount_mismatch": "The invoice amounts need a quick check.",
    "vat_rate_mismatch": "The VAT details need a quick check.",
    "exempt_document_with_nonzero_vat": "The VAT details need a quick check.",
    "extraction_service_unavailable": "I couldn't read everything reliably.",
}


def source_recovery_message(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return (
            "I couldn't read everything reliably. Check the highlighted details below. "
            "Try a clearer copy if the original is difficult to read."
        )
    return (
        "I couldn't read everything reliably. Check the highlighted details below. "
        "Try a clearer copy if the photo is difficult to read."
    )


def customer_review_reasons(
    document: Mapping[str, object],
    *,
    queue_status: str = "review",
    source_path: Path | None = None,
) -> tuple[str, ...]:
    """Translate stored diagnostics without ever rendering untrusted error text."""
    reasons: list[str] = []
    raw_issues = document.get("machine_issues") or ()
    if isinstance(raw_issues, str):
        raw_issues = (raw_issues,)
    for issue in raw_issues:
        key = str(issue or "").strip()
        message = _ISSUE_MESSAGES.get(key)
        if message and message not in reasons:
            reasons.append(message)

    raw_notes = document.get("model_notes") or ()
    if isinstance(raw_notes, str):
        raw_notes = (raw_notes,)
    if any(str(note or "").strip() for note in raw_notes):
        message = "I couldn't read everything reliably."
        if message not in reasons:
            reasons.append(message)

    if queue_status == "error":
        message = source_recovery_message(source_path or Path("invoice"))
        if message not in reasons:
            reasons.append(message)

    if not reasons and queue_status == "review":
        try:
            confidence = float(document.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < 0.90:
            reasons.append("Check the highlighted details before approval.")

    return tuple(reasons)
