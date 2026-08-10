
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from ai_extractor import extract_with_ai
from parser_engine import parse_invoice, extract_items
from services.business_identity import (
    BusinessIdentityRepository,
    CanonicalSupplier,
    normalize_identity_text,
    normalize_vat_id,
)
from services.pilot_support import log_runtime_error


DOCUMENT_REQUIREMENTS = {
    "חשבונית מס": {
        "required": ["supplier", "supplier_id", "invoice_number", "invoice_date", "total"],
        "items_required": True,
    },
    "חשבונית מס/קבלה": {
        "required": ["supplier", "supplier_id", "invoice_number", "invoice_date", "total"],
        "items_required": True,
    },
    "חשבונית זיכוי": {
        "required": ["supplier", "supplier_id", "invoice_number", "invoice_date", "total"],
        "items_required": True,
    },
    "קבלה": {
        "required": ["supplier", "supplier_id", "invoice_number", "invoice_date", "total"],
        "items_required": False,
    },
    "תעודת משלוח": {
        "required": ["supplier", "supplier_id", "invoice_number", "invoice_date"],
        "items_required": True,
    },
    "ריכוז חשבון": {
        "required": ["supplier", "supplier_id", "invoice_date", "total"],
        "items_required": True,
    },
    "דרישת תשלום": {
        "required": ["supplier", "invoice_date", "total"],
        "items_required": False,
    },
    "אחר": {
        "required": ["supplier", "invoice_date"],
        "items_required": False,
    },
}


def _as_text(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _as_number(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _source_contains_name(source_text: str, supplier_name: str) -> bool:
    """Require the extracted supplier spelling to be visible in source text."""
    candidate = normalize_identity_text(supplier_name)
    source = _supplier_evidence_region(source_text)
    if len(candidate.replace(" ", "")) < 3 or not source:
        return False
    return f" {candidate} " in f" {source} "


def _source_contains_identifier(source_text: str, supplier_id: str) -> bool:
    """Match a source-visible identifier without joining unrelated numbers."""
    candidate = normalize_vat_id(supplier_id)
    if len(candidate) < 5:
        return False
    source_identifiers = {
        normalize_vat_id(value)
        for value in re.findall(
            r"(?<!\d)\d(?:[\s.\-/]?\d){4,}(?!\d)",
            _supplier_evidence_region(source_text),
        )
    }
    return candidate in source_identifiers


def _supplier_evidence_region(source_text: str) -> str:
    """Prefer the issuer header and exclude explicit recipient/customer blocks."""
    source = normalize_identity_text(source_text)
    boundaries = (
        " לכבוד ",
        " פרטי לקוח ",
        " bill to ",
        " customer ",
    )
    positions = [source.find(marker) for marker in boundaries]
    positions = [position for position in positions if position >= 0]
    return source[:min(positions)] if positions else source


def ground_supplier_identity(
    document: dict,
    source_text: str,
    *,
    source_text_method: str = "",
    identity_lookup: Callable[[str], CanonicalSupplier | None] | None = None,
) -> dict:
    """Fail closed unless supplier identity is traceable to source evidence.

    A new supplier name must appear in locally derived source text. A supplier
    ID may recover an established canonical identity only when that ID is also
    visible in the source. Manual owner corrections happen later in Review and
    therefore do not pass through this extraction-only gate.
    """
    grounded = dict(document)
    supplier = _as_text(grounded.get("supplier"))
    supplier_id = _as_text(grounded.get("supplier_id"))
    id_is_visible = _source_contains_identifier(source_text, supplier_id)

    if _source_contains_name(source_text, supplier):
        if source_text_method in {"local_pdf_ocr", "local_image_ocr"}:
            grounded["supplier_grounding"] = "ocr_source_text"
            grounded["warnings"] = list(grounded.get("warnings") or []) + [
                "supplier_requires_confirmation"
            ]
        else:
            grounded["supplier_grounding"] = "visible_source_text"
        if supplier_id and not id_is_visible:
            grounded["supplier_id"] = ""
        return grounded

    canonical = None
    if supplier_id and id_is_visible:
        lookup = identity_lookup or (
            lambda value: BusinessIdentityRepository().supplier_identity(
                "", value, ensure=False
            )
        )
        try:
            canonical = lookup(supplier_id)
        except Exception:
            # Identity-memory availability must not turn a recoverable supplier
            # uncertainty into a failed invoice extraction.
            canonical = None

    if canonical is not None:
        grounded["supplier"] = canonical.canonical_name
        grounded["supplier_id"] = canonical.vat_id or supplier_id
        grounded["supplier_grounding"] = "approved_supplier_id"
        return grounded

    grounded["supplier"] = ""
    grounded["supplier_confidence"] = 0.0
    grounded["supplier_grounding"] = "unsupported"
    if supplier_id and not id_is_visible:
        grounded["supplier_id"] = ""
    return grounded


def normalize_document(document: dict) -> dict:
    normalized = dict(document)

    for field in (
        "supplier_id",
        "invoice_number",
        "related_document_number",
        "supplier",
        "invoice_date",
        "due_date",
        "statement_month",
        "currency",
        "tax_treatment",
    ):
        normalized[field] = _as_text(normalized.get(field))

    normalized["currency"] = normalized.get("currency") or "ILS"
    normalized["tax_treatment"] = normalized.get("tax_treatment") or "לא ברור"

    for field in (
        "subtotal",
        "taxable_amount",
        "exempt_amount",
        "vat_rate",
        "vat",
        "total",
    ):
        normalized[field] = _as_number(normalized.get(field))

    normalized["items"] = normalized.get("items") or []
    normalized["warnings"] = normalized.get("warnings") or []
    normalized["confidence"] = float(normalized.get("confidence") or 0.0)

    # Backward compatibility.
    if normalized["subtotal"] is None:
        taxable = normalized.get("taxable_amount")
        exempt = normalized.get("exempt_amount")
        if taxable is not None or exempt is not None:
            normalized["subtotal"] = (taxable or 0.0) + (exempt or 0.0)

    if normalized.get("taxable_amount") is None:
        treatment = normalized.get("tax_treatment")
        if treatment == "חייב במע״מ" and normalized.get("subtotal") is not None:
            normalized["taxable_amount"] = normalized["subtotal"]
        elif treatment == "מעורב" and normalized.get("subtotal") is not None:
            exempt = normalized.get("exempt_amount") or 0.0
            normalized["taxable_amount"] = normalized["subtotal"] - exempt

    if (
        normalized.get("document_type") == "ריכוז חשבון"
        and not normalized.get("statement_month")
        and normalized.get("invoice_date")
    ):
        normalized["statement_month"] = normalized["invoice_date"][:7]

    return normalized


def _legacy_to_common(parsed: dict, items: list[dict]) -> dict:
    subtotal = parsed.get("subtotal")
    vat = parsed.get("vat")

    if vat in (None, 0):
        tax_treatment = "לא ברור"
    else:
        tax_treatment = "חייב במע״מ"

    return normalize_document({
        **parsed,
        "taxable_amount": subtotal if tax_treatment == "חייב במע״מ" else None,
        "exempt_amount": None,
        "vat_rate": None,
        "tax_treatment": tax_treatment,
        "related_document_number": "",
        "statement_month": (
            parsed.get("invoice_date", "")[:7]
            if parsed.get("document_type") == "ריכוז חשבון"
            and parsed.get("invoice_date")
            else ""
        ),
        "items": [
            {
                "item_code": _as_text(item.get("קוד מוצר", "")),
                "description": _as_text(item.get("תיאור", "")),
                "quantity": item.get("כמות"),
                "unit": "",
                "unit_price": item.get("מחיר יחידה"),
                "line_total": item.get('סה"כ שורה'),
            }
            for item in items
        ],
        "warnings": [],
        "confidence": 0.0,
    })


def validate_document(document: dict) -> dict:
    document = normalize_document(document)
    document_type = document.get("document_type") or "אחר"
    rules = DOCUMENT_REQUIREMENTS.get(
        document_type,
        DOCUMENT_REQUIREMENTS["אחר"],
    )

    machine_issues = []

    for field in rules["required"]:
        value = document.get(field)
        if value is None or value == "":
            machine_issues.append(f"missing_{field}")

    if rules["items_required"] and not document.get("items"):
        machine_issues.append("missing_line_items")

    subtotal = document.get("subtotal")
    taxable = document.get("taxable_amount")
    exempt = document.get("exempt_amount")
    vat = document.get("vat")
    total = document.get("total")
    treatment = document.get("tax_treatment", "לא ברור")

    expected_total = None

    if treatment == "מעורב":
        if taxable is None:
            machine_issues.append("missing_taxable_amount")
        if exempt is None:
            machine_issues.append("missing_exempt_amount")
        if vat is None:
            machine_issues.append("missing_vat")
        if all(v is not None for v in (taxable, exempt, vat)):
            expected_total = taxable + exempt + vat

    elif treatment == "חייב במע״מ":
        base = taxable if taxable is not None else subtotal
        if base is None:
            machine_issues.append("missing_taxable_amount")
        if vat is None:
            machine_issues.append("missing_vat")
        if base is not None and vat is not None:
            expected_total = base + vat

    elif treatment == "פטור ממע״מ":
        base = exempt if exempt is not None else subtotal
        if base is None:
            machine_issues.append("missing_exempt_amount")
        if base is not None:
            expected_total = base
        if vat not in (None, 0.0):
            machine_issues.append("exempt_document_with_nonzero_vat")

    elif treatment == "לא רלוונטי":
        # Receipts and payment requests may legitimately have no VAT fields.
        expected_total = None

    elif treatment == "לא ברור":
        # Do not invent VAT. Review only if arithmetic is impossible to interpret.
        if total is not None and subtotal is not None and vat is not None:
            expected_total = subtotal + vat

    if expected_total is not None and total is not None:
        if abs(expected_total - total) > 0.05:
            machine_issues.append("amount_mismatch")

    if (
        document.get("vat_rate") is not None
        and document.get("vat") is not None
        and taxable is not None
        and taxable != 0
    ):
        calculated_vat = taxable * document["vat_rate"] / 100
        if abs(calculated_vat - document["vat"]) > 0.10:
            machine_issues.append("vat_rate_mismatch")

    if document_type == "חשבונית זיכוי":
        for field in (
            "subtotal",
            "taxable_amount",
            "exempt_amount",
            "vat",
            "total",
        ):
            value = document.get(field)
            if value is not None and float(value) > 0:
                machine_issues.append(
                    f"credit_note_{field}_must_be_negative"
                )

    if document_type == "ריכוז חשבון" and not document.get("statement_month"):
        machine_issues.append("missing_statement_month")

    model_notes = [
        str(note).strip()
        for note in document.get("warnings", [])
        if str(note).strip()
    ]

    status = "review" if machine_issues or model_notes else "pass"

    return {
        "status": status,
        "machine_issues": sorted(set(machine_issues)),
        "model_notes": model_notes,
    }


def extract_hybrid(
    path: Path,
    raw_text: str = "",
    use_ai: bool = True,
    ai_model: str | None = None,
    *,
    source_text_method: str = "",
) -> tuple[dict, str]:
    if use_ai:
        try:
            document, method = extract_with_ai(path, model=ai_model)
            document = normalize_document(document)
            document = ground_supplier_identity(
                document,
                raw_text,
                source_text_method=source_text_method,
            )
            validation = validate_document(document)
            document["machine_issues"] = validation["machine_issues"]
            document["model_notes"] = validation["model_notes"]
            document["status"] = validation["status"]
            document["warnings"] = (
                validation["machine_issues"]
                + validation["model_notes"]
            )
            return document, method
        except Exception as exc:
            log_runtime_error("Invoice extraction service", exc)
            ai_failed = True
    else:
        ai_failed = True

    parsed = parse_invoice(raw_text)
    items = extract_items(raw_text)
    document = _legacy_to_common(parsed, items)
    document = ground_supplier_identity(
        document,
        raw_text,
        source_text_method=source_text_method,
    )
    validation = validate_document(document)
    document["machine_issues"] = validation["machine_issues"]
    document["model_notes"] = (
        ["extraction_service_unavailable"] if ai_failed else []
    )
    document["status"] = "review"
    document["warnings"] = (
        document["machine_issues"] + document["model_notes"]
    )
    return document, "legacy_fallback"
