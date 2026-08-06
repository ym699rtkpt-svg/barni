
from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import (
    all_tags,
    invoice_history,
    invoice_items,
    invoice_tags,
    search_invoices,
    set_invoice_tags,
    supplier_suggestions,
    suppliers,
    update_invoice,
)


def show_pdf_inline(path: Path):
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    html = f"""
    <iframe
      src="data:application/pdf;base64,{encoded}"
      width="100%"
      height="760"
      style="border: 1px solid #ddd; border-radius: 8px;">
    </iframe>
    """
    components.html(html, height=780, scrolling=True)


def render_database_archive():
    st.subheader("חיפוש חשבוניות")
    st.caption(
        "חיפוש חופשי בספק, מספר מסמך ומוצרים. "
        "בחירת ספק נעשית בתיבת חיפוש פנימית, בלי השלמות מאנשי הקשר של Safari."
    )

    all_supplier_names = suppliers()
    supplier_choice = st.selectbox(
        "ספק",
        options=["כל הספקים"] + all_supplier_names,
        index=0,
        help="לחץ בשדה והתחל להקליד. תיבת הבחירה מסננת את הספקים.",
    )
    supplier_query = "" if supplier_choice == "כל הספקים" else supplier_choice

    row0 = st.columns(3)
    free_text = row0[0].text_input(
        "חיפוש חופשי",
        placeholder="ספק, מספר מסמך, מוצר או קוד מוצר",
        autocomplete="off",
    )
    invoice_query = row0[1].text_input(
        "מספר מסמך",
        placeholder="841",
        autocomplete="off",
    )
    selected_tags = row0[2].multiselect(
        "תגיות",
        options=all_tags(),
    )

    row1 = st.columns(4)
    document_types = row1[0].multiselect(
        "סוג מסמך",
        options=[
            "חשבונית מס", "חשבונית מס/קבלה", "קבלה",
            "חשבונית זיכוי", "תעודת משלוח", "ריכוז חשבון",
            "דרישת תשלום", "אחר",
        ],
    )
    statuses = row1[1].multiselect(
        "סטטוס",
        options=["approved", "review", "rejected"],
        default=["approved"],
    )
    sort_label = row1[2].selectbox(
        "מיון",
        options=["תאריך", "ספק", "סכום", "מספר מסמך"],
    )
    descending = row1[3].toggle("סדר יורד", value=True)

    sort_map = {
        "תאריך": "invoice_date",
        "ספק": "supplier",
        "סכום": "total",
        "מספר מסמך": "invoice_number",
    }

    date_mode = st.checkbox("סנן לפי תאריך")
    row2 = st.columns(4)
    start_date = row2[0].date_input("מתאריך") if date_mode else None
    end_date = row2[1].date_input("עד תאריך") if date_mode else None
    min_total = row2[2].number_input("סכום מינימום", value=0.0, step=1.0)
    max_total = row2[3].number_input(
        "סכום מקסימום", value=10_000_000.0, step=100.0
    )

    results = search_invoices(
        free_text=free_text.strip(),
        supplier_query=supplier_query,
        invoice_number=invoice_query.strip(),
        document_types=document_types,
        statuses=statuses,
        tags=selected_tags,
        start_date=start_date.isoformat() if start_date else "",
        end_date=end_date.isoformat() if end_date else "",
        min_total=min_total,
        max_total=max_total,
        sort_by=sort_map[sort_label],
        descending=descending,
    )

    metrics = st.columns(3)
    metrics[0].metric("נמצאו", len(results))
    metrics[1].metric(
        "סה״כ",
        f"{pd.to_numeric(results.get('total'), errors='coerce').fillna(0).sum():,.2f} ₪"
        if not results.empty else "0.00 ₪",
    )
    metrics[2].metric(
        "ספקים",
        int(results["supplier"].replace("", pd.NA).nunique())
        if not results.empty else 0,
    )

    if results.empty:
        st.info("לא נמצאו מסמכים.")
        return

    defaults = {
        "category": "לא מסווג",
        "subcategory": "",
        "tax_treatment": "לא ברור",
        "taxable_amount": None,
        "exempt_amount": None,
        "vat_rate": None,
    }
    for column, default in defaults.items():
        if column not in results.columns:
            results[column] = default

    display = results[
        [
            "supplier", "invoice_number", "invoice_date",
            "document_type", "category", "subcategory",
            "tax_treatment", "taxable_amount",
            "exempt_amount", "vat", "total", "status",
        ]
    ].copy()

    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "supplier": "ספק",
            "invoice_number": "מספר מסמך",
            "invoice_date": "תאריך",
            "document_type": "סוג",
            "category": "קטגוריה",
            "subcategory": "תת־קטגוריה",
            "tax_treatment": "מצב מע״מ",
            "taxable_amount": st.column_config.NumberColumn(
                "חייב במע״מ", format="%.2f ₪"
            ),
            "exempt_amount": st.column_config.NumberColumn(
                "פטור ממע״מ", format="%.2f ₪"
            ),
            "vat": st.column_config.NumberColumn("מע״מ", format="%.2f ₪"),
            "total": st.column_config.NumberColumn("סה״כ", format="%.2f ₪"),
            "status": "סטטוס",
        },
    )

    options = {}
    for _, row in results.iterrows():
        label = (
            f"{row['invoice_date']} | {row['supplier']} | "
            f"{row['invoice_number']} | {row['total'] or 0:,.2f} ₪"
        )
        options[label] = int(row["id"])

    selected_label = st.selectbox("פתח מסמך", options=list(options.keys()))
    invoice_id = options[selected_label]
    selected = results[results["id"] == invoice_id].iloc[0]
    items = invoice_items(invoice_id)

    original_tab, edit_tab, items_tab, history_tab = st.tabs(
        ["מסמך מקורי", "עריכה ותגיות", "שורות מוצרים", "היסטוריה"]
    )

    with original_tab:
        path = Path(selected["archived_path"])
        if path.exists() and path.suffix.lower() == ".pdf":
            show_pdf_inline(path)
            st.download_button(
                "הורד PDF",
                data=path.read_bytes(),
                file_name=path.name,
                mime="application/pdf",
            )
        elif path.exists():
            st.image(str(path), width="stretch")
        else:
            st.warning("הקובץ המקורי לא נמצא.")

    with edit_tab:
        with st.form(f"database_edit_{invoice_id}"):
            col1, col2 = st.columns(2)
            supplier = col1.text_input("ספק", value=str(selected["supplier"]))
            supplier_id = col2.text_input(
                "ח.פ./עוסק", value=str(selected["supplier_id"])
            )
            invoice_number = col1.text_input(
                "מספר מסמך", value=str(selected["invoice_number"])
            )
            invoice_date = col2.text_input(
                "תאריך", value=str(selected["invoice_date"])
            )
            tax_treatment = col1.selectbox(
                "מצב מע״מ",
                ["חייב במע״מ", "פטור ממע״מ", "מעורב", "לא רלוונטי", "לא ברור"],
                index=(
                    ["חייב במע״מ", "פטור ממע״מ", "מעורב", "לא רלוונטי", "לא ברור"]
                    .index(selected["tax_treatment"])
                    if selected["tax_treatment"] in [
                        "חייב במע״מ", "פטור ממע״מ", "מעורב", "לא רלוונטי", "לא ברור"
                    ] else 4
                ),
            )
            taxable_amount = col2.number_input(
                "סכום חייב במע״מ",
                value=float(selected["taxable_amount"] or 0.0),
            )
            exempt_amount = col1.number_input(
                "סכום פטור ממע״מ",
                value=float(selected["exempt_amount"] or 0.0),
            )
            vat = col2.number_input(
                "סכום מע״מ", value=float(selected["vat"] or 0.0)
            )
            total = col1.number_input(
                "סה״כ", value=float(selected["total"] or 0.0)
            )
            submitted = st.form_submit_button("שמור שינויים", type="primary")

        if submitted:
            update_invoice(
                invoice_id,
                {
                    "supplier": supplier,
                    "supplier_id": supplier_id,
                    "invoice_number": invoice_number,
                    "invoice_date": invoice_date,
                    "tax_treatment": tax_treatment,
                    "taxable_amount": taxable_amount,
                    "exempt_amount": exempt_amount,
                    "vat": vat,
                    "total": total,
                },
            )
            st.success("השינויים נשמרו.")
            st.rerun()

        current_tags = invoice_tags(invoice_id)
        tags_input = st.multiselect(
            "תגיות",
            options=sorted(set(all_tags() + [
                "מים", "חשמל", "ביטוח", "ציוד", "מזון",
                "ניקיון", "תחזוקה", "משלוחים", "ארנונה", "אחר"
            ])),
            default=current_tags,
            accept_new_options=True,
        )
        if st.button("שמור תגיות"):
            set_invoice_tags(invoice_id, tags_input)
            st.success("התגיות נשמרו.")
            st.rerun()

    with items_tab:
        if items.empty:
            st.info("אין שורות מוצרים.")
        else:
            st.dataframe(
                items,
                hide_index=True,
                width="stretch",
                column_config={
                    "item_code": "קוד מוצר",
                    "description": "תיאור",
                    "quantity": "כמות",
                    "unit": "יחידה",
                    "unit_price": st.column_config.NumberColumn(
                        "מחיר יחידה", format="%.2f ₪"
                    ),
                    "line_total": st.column_config.NumberColumn(
                        "סה״כ שורה", format="%.2f ₪"
                    ),
                },
            )

    with history_tab:
        history = invoice_history(invoice_id)
        if history.empty:
            st.info("אין עדיין שינויים מתועדים.")
        else:
            st.dataframe(history, hide_index=True, width="stretch")
