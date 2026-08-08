
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st

from database import duplicate_invoice, insert_invoice, replace_duplicate_invoice

from knowledge_engine.engine import KnowledgeEngine
from knowledge_engine.events import KnowledgeEvent


knowledge_engine = KnowledgeEngine()

TAX_TREATMENTS = [
    "חייב במע״מ",
    "פטור ממע״מ",
    "מעורב",
    "לא רלוונטי",
    "לא ברור",
]

DOCUMENT_TYPES = [
    "חשבונית מס",
    "חשבונית מס/קבלה",
    "קבלה",
    "חשבונית זיכוי",
    "תעודת משלוח",
    "ריכוז חשבון",
    "דרישת תשלום",
    "אחר",
]


def _field_needs_review(issues: set[str], field: str) -> bool:
    if f"missing_{field}" in issues:
        return True
    if field in {"subtotal", "taxable_amount", "exempt_amount", "vat", "total"}:
        if "amount_mismatch" in issues:
            return True
        if f"credit_note_{field}_must_be_negative" in issues:
            return True
    if field in {"vat_rate", "vat", "taxable_amount"} and "vat_rate_mismatch" in issues:
        return True
    return field == "items" and "missing_line_items" in issues


def _review_label(label: str, issues: set[str], field: str) -> str:
    return f"{label} · Needs attention" if _field_needs_review(issues, field) else label


def document_review_form(
    record: dict,
    form_key: str,
    *,
    compact: bool = False,
) -> tuple[dict, list[dict], bool]:
    document = record.get("document", {})
    issues = set(document.get("machine_issues") or [])

    with st.form(form_key):
        col1, col2 = st.columns(2, gap="medium")

        supplier = col1.text_input(
            _review_label("Supplier", issues, "supplier"),
            value=str(document.get("supplier", "")),
        )
        invoice_number = col2.text_input(
            _review_label("Invoice number", issues, "invoice_number"),
            value=str(document.get("invoice_number", "")),
        )
        invoice_date = col1.text_input(
            _review_label("Invoice date", issues, "invoice_date"),
            value=str(document.get("invoice_date", "")),
            placeholder="YYYY-MM-DD",
        )
        total = col2.number_input(
            _review_label("Total", issues, "total"),
            value=float(document.get("total") or 0.0),
            step=0.01,
        )

        details_context = st.expander("More invoice details") if compact else st.container()
        with details_context:
            detail1, detail2 = st.columns(2, gap="medium")
            document_type = detail1.selectbox(
                _review_label("Document type", issues, "document_type"),
                DOCUMENT_TYPES,
                index=(
                    DOCUMENT_TYPES.index(document.get("document_type"))
                    if document.get("document_type") in DOCUMENT_TYPES
                    else len(DOCUMENT_TYPES) - 1
                ),
            )
            supplier_id = detail2.text_input(
                _review_label("Supplier ID", issues, "supplier_id"),
                value=str(document.get("supplier_id", "")),
            )
            due_date = detail1.text_input(
                _review_label("Due date", issues, "due_date"),
                value=str(document.get("due_date", "")),
                placeholder="YYYY-MM-DD",
            )
            tax_treatment = detail2.selectbox(
                _review_label("VAT treatment", issues, "tax_treatment"),
                TAX_TREATMENTS,
                index=(
                    TAX_TREATMENTS.index(document.get("tax_treatment"))
                    if document.get("tax_treatment") in TAX_TREATMENTS
                    else TAX_TREATMENTS.index("לא ברור")
                ),
            )
            vat_rate = detail1.number_input(
                _review_label("VAT rate %", issues, "vat_rate"),
                value=float(document.get("vat_rate") or 0.0),
                step=0.1,
            )
            currency = detail2.text_input(
                "Currency",
                value=str(document.get("currency", "ILS")),
            )
            taxable_amount = detail1.number_input(
                _review_label("Taxable amount", issues, "taxable_amount"),
                value=float(document.get("taxable_amount") or 0.0),
                step=0.01,
            )
            exempt_amount = detail2.number_input(
                _review_label("Exempt amount", issues, "exempt_amount"),
                value=float(document.get("exempt_amount") or 0.0),
                step=0.01,
            )
            subtotal = detail1.number_input(
                _review_label("Subtotal", issues, "subtotal"),
                value=float(document.get("subtotal") or 0.0),
                step=0.01,
            )
            vat = detail2.number_input(
                _review_label("VAT", issues, "vat"),
                value=float(document.get("vat") or 0.0),
                step=0.01,
            )

        expected_total = (
            taxable_amount + exempt_amount + vat
            if tax_treatment == "מעורב"
            else taxable_amount + vat
            if tax_treatment == "חייב במע״מ"
            else exempt_amount
            if tax_treatment == "פטור ממע״מ"
            else None
        )
        if expected_total is not None:
            delta = round(expected_total - total, 2)
            if abs(delta) <= 0.05:
                st.success("בדיקת סכומים תקינה")
            else:
                st.warning(
                    f"בדיקת סכומים: צפוי {expected_total:,.2f} ₪, "
                    f"בפועל {total:,.2f} ₪, הפרש {delta:+,.2f} ₪"
                )

        st.markdown("#### " + _review_label("Products", issues, "items"))
        items = document.get("items", []) or []
        items_df = pd.DataFrame(items)

        if items_df.empty:
            items_df = pd.DataFrame([{
                "item_code": "",
                "description": "",
                "quantity": 1.0,
                "unit": "",
                "unit_price": 0.0,
                "line_total": 0.0,
            }])

        edited_items = st.data_editor(
            items_df,
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            key=f"{form_key}_items",
            column_config={
                "item_code": "Product code",
                "description": "Product",
                "quantity": st.column_config.NumberColumn("Quantity"),
                "unit": "Unit",
                "unit_price": st.column_config.NumberColumn(
                    "Unit price",
                    format="₪%.2f",
                ),
                "line_total": st.column_config.NumberColumn(
                    "Total",
                    format="₪%.2f",
                ),
            },
            column_order=(
                ["description", "quantity", "unit_price", "line_total"]
                if compact
                else None
            ),
        )

        submitted = st.form_submit_button(
            "Save changes",
            type="secondary" if compact else "primary",
            width="stretch",
        )

    updated = {
        **document,
        "document_type": document_type,
        "supplier": supplier.strip(),
        "supplier_id": supplier_id.strip(),
        "invoice_number": invoice_number.strip(),
        "invoice_date": invoice_date.strip(),
        "due_date": due_date.strip(),
        "subtotal": subtotal,
        "taxable_amount": taxable_amount,
        "exempt_amount": exempt_amount,
        "vat_rate": vat_rate if vat_rate != 0 else None,
        "vat": vat,
        "total": total,
        "tax_treatment": tax_treatment,
        "currency": currency.strip() or "ILS",
    }
    items_list = edited_items.fillna("").to_dict(orient="records")
    updated["items"] = items_list

    return updated, items_list, submitted


def approve_to_database_detailed(
    record: dict,
    updated_document: dict,
    on_progress: Callable[[str], None] | None = None,
    duplicate_resolution: str = "ask",
) -> tuple[bool, str, dict]:
    source = Path(record["stored_file"])
    notify = on_progress or (lambda stage: None)

    notify("duplicate_check")
    existing = duplicate_invoice(
        updated_document.get("supplier_id", ""),
        updated_document.get("invoice_number", ""),
        updated_document.get("document_type", ""),
    )
    if existing and duplicate_resolution == "ask":
        return (
            False,
            "כבר קיים מסמך עם אותו ספק, מספר וסוג.",
            {"outcome": "duplicate", "invoice_id": existing["id"], "existing": existing},
        )

    if existing and duplicate_resolution == "skip":
        return True, "החשבונית החדשה דולגה לפי בחירתך.", {
            "outcome": "skipped", "invoice_id": existing["id"], "existing": existing,
        }

    notify("saving")
    try:
        if existing and duplicate_resolution == "replace":
            invoice_id = replace_duplicate_invoice(
                existing["id"], source, updated_document
            )
            saved_outcome = "replaced"
        else:
            invoice_id = insert_invoice(
                source_file=source,
                document=updated_document,
                move_source=True,
            )
            saved_outcome = "kept_both" if existing else "saved"
    except Exception as exc:
        return False, str(exc), {"outcome": "error", "invoice_id": None}

    notify("learning")
    event = KnowledgeEvent(
        event_type="invoice_approved",
        payload={
            **updated_document,
            "invoice_id": invoice_id,
        },
        created_at=datetime.now(),
    )

    knowledge_engine.handle_event(event)

    return (
        True,
        f"המסמך נשמר במסד ובארכיון. מזהה: {invoice_id}",
        {"outcome": saved_outcome, "invoice_id": invoice_id},
    )


def approve_to_database(record: dict, updated_document: dict) -> tuple[bool, str]:
    success, message, _ = approve_to_database_detailed(
        record,
        updated_document,
    )
    return success, message
