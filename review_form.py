
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from database import duplicate_exists, insert_invoice

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


def document_review_form(record: dict, form_key: str) -> tuple[dict, list[dict], bool]:
    document = record.get("document", {})

    with st.form(form_key):
        col1, col2 = st.columns(2)

        document_type = col1.selectbox(
            "סוג מסמך",
            DOCUMENT_TYPES,
            index=(
                DOCUMENT_TYPES.index(document.get("document_type"))
                if document.get("document_type") in DOCUMENT_TYPES
                else len(DOCUMENT_TYPES) - 1
            ),
        )
        supplier = col2.text_input(
            "ספק",
            value=str(document.get("supplier", "")),
        )

        supplier_id = col1.text_input(
            "ח.פ./עוסק מורשה",
            value=str(document.get("supplier_id", "")),
        )
        invoice_number = col2.text_input(
            "מספר מסמך",
            value=str(document.get("invoice_number", "")),
        )

        invoice_date = col1.text_input(
            "תאריך חשבונית YYYY-MM-DD",
            value=str(document.get("invoice_date", "")),
        )
        due_date = col2.text_input(
            "תאריך פירעון YYYY-MM-DD",
            value=str(document.get("due_date", "")),
        )

        tax_treatment = col1.selectbox(
            "מצב מע״מ",
            TAX_TREATMENTS,
            index=(
                TAX_TREATMENTS.index(document.get("tax_treatment"))
                if document.get("tax_treatment") in TAX_TREATMENTS
                else TAX_TREATMENTS.index("לא ברור")
            ),
        )
        vat_rate = col2.number_input(
            "שיעור מע״מ %",
            value=float(document.get("vat_rate") or 0.0),
            step=0.1,
        )

        taxable_amount = col1.number_input(
            "סכום חייב במע״מ",
            value=float(document.get("taxable_amount") or 0.0),
            step=0.01,
        )
        exempt_amount = col2.number_input(
            "סכום פטור ממע״מ",
            value=float(document.get("exempt_amount") or 0.0),
            step=0.01,
        )

        subtotal = col1.number_input(
            "סה״כ לפני מע״מ",
            value=float(document.get("subtotal") or 0.0),
            step=0.01,
        )
        vat = col2.number_input(
            "סכום מע״מ",
            value=float(document.get("vat") or 0.0),
            step=0.01,
        )
        total = col1.number_input(
            "סה״כ לתשלום",
            value=float(document.get("total") or 0.0),
            step=0.01,
        )
        currency = col2.text_input(
            "מטבע",
            value=str(document.get("currency", "ILS")),
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

        st.markdown("#### שורות מוצרים")
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
                "item_code": "קוד מוצר",
                "description": "תיאור",
                "quantity": st.column_config.NumberColumn("כמות"),
                "unit": "יחידה",
                "unit_price": st.column_config.NumberColumn(
                    "מחיר יחידה",
                    format="%.2f ₪",
                ),
                "line_total": st.column_config.NumberColumn(
                    "סה״כ שורה",
                    format="%.2f ₪",
                ),
            },
        )

        submitted = st.form_submit_button(
            "שמור את העריכות",
            type="primary",
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


def approve_to_database(record: dict, updated_document: dict) -> tuple[bool, str]:
    source = Path(record["stored_file"])

    if duplicate_exists(
        updated_document.get("supplier_id", ""),
        updated_document.get("invoice_number", ""),
        updated_document.get("document_type", ""),
    ):
        return False, "כבר קיים מסמך עם אותו ספק, מספר וסוג."

    try:
        invoice_id = insert_invoice(
            source_file=source,
            document=updated_document,
            move_source=True,
        )
    except Exception as exc:
        return False, str(exc)

    event = KnowledgeEvent(
        event_type="invoice_approved",
        payload={
            **updated_document,
            "invoice_id": invoice_id,
        },
        created_at=datetime.now(),
    )

    knowledge_engine.handle_event(event)

    return True, f"המסמך נשמר במסד ובארכיון. מזהה: {invoice_id}"
