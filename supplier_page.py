
from __future__ import annotations

import pandas as pd
import streamlit as st

from database import supplier_summary, suppliers


def render_suppliers_page():
    st.subheader("ספקים")

    names = suppliers()
    if not names:
        st.info("עדיין אין ספקים במסד.")
        return

    selected = st.selectbox(
        "בחר ספק",
        options=names,
    )

    summary = supplier_summary(selected)

    cols = st.columns(5)
    cols[0].metric("חשבוניות", summary["invoice_count"])
    cols[1].metric("סה״כ קניות", f"{summary['total_spend']:,.2f} ₪")
    cols[2].metric("מע״מ", f"{summary['vat_total']:,.2f} ₪")
    cols[3].metric("ממוצע לחשבונית", f"{summary['average_invoice']:,.2f} ₪")
    cols[4].metric("חשבונית אחרונה", summary["last_invoice_date"] or "-")

    st.markdown("### כל החשבוניות")
    documents = summary["documents"]
    if not documents.empty:
        st.dataframe(
            documents[
                [
                    "invoice_date", "invoice_number", "document_type",
                    "category", "subcategory", "total", "vat", "status",
                ]
            ],
            hide_index=True,
            width="stretch",
            column_config={
                "invoice_date": "תאריך",
                "invoice_number": "מספר",
                "document_type": "סוג",
                "category": "קטגוריה",
                "subcategory": "תת־קטגוריה",
                "total": st.column_config.NumberColumn("סה״כ", format="%.2f ₪"),
                "vat": st.column_config.NumberColumn("מע״מ", format="%.2f ₪"),
                "status": "סטטוס",
            },
        )

    st.markdown("### מוצרים מספק זה")
    items = summary["items"]
    if items.empty:
        st.info("אין שורות מוצרים.")
    else:
        grouped = (
            items.groupby("description")
            .agg(
                purchases=("description", "count"),
                quantity=("quantity", "sum"),
                average_price=("unit_price", "mean"),
                total=("line_total", "sum"),
            )
            .reset_index()
            .sort_values("total", ascending=False)
        )
        st.dataframe(
            grouped,
            hide_index=True,
            width="stretch",
        )
