
from __future__ import annotations

import pandas as pd
import streamlit as st

from database import natural_language_query


def render_ai_accountant():
    st.subheader("AI Accountant")
    st.caption(
        "שאל בשפה חופשית. כרגע המנוע מבין ספקים, שנים, חודשים, "
        "סכומים ומוצרים מתוך מסד הנתונים."
    )

    examples = [
        "תראה לי את כל החשבוניות של מפגש הדייגים",
        "כל החשבוניות מעל 5000",
        "כל החשבוניות מיולי 2026",
        "כמה שילמנו בשנת 2026",
        "תראה לי חשבוניות עם שמן",
    ]
    st.write("דוגמאות:", " · ".join(examples))

    query = st.text_input(
        "מה תרצה לדעת?",
        placeholder="למשל: כל החשבוניות מעל 10,000",
    )

    if not query:
        return

    results = natural_language_query(query)

    if results.empty:
        st.info("לא נמצאו תוצאות לשאלה הזאת.")
        return

    total = pd.to_numeric(
        results["total"],
        errors="coerce",
    ).fillna(0).sum()

    cols = st.columns(3)
    cols[0].metric("מסמכים", len(results))
    cols[1].metric("סה״כ", f"{total:,.2f} ₪")
    cols[2].metric("ספקים", results["supplier"].nunique())

    st.dataframe(
        results[
            [
                "supplier", "invoice_number", "invoice_date",
                "document_type", "category", "subcategory", "total",
            ]
        ],
        hide_index=True,
        width="stretch",
        column_config={
            "supplier": "ספק",
            "invoice_number": "מספר",
            "invoice_date": "תאריך",
            "document_type": "סוג",
            "category": "קטגוריה",
            "subcategory": "תת־קטגוריה",
            "total": st.column_config.NumberColumn(
                "סה״כ",
                format="%.2f ₪",
            ),
        },
    )

    st.success(
        f"נמצאו {len(results)} מסמכים בסכום כולל של {total:,.2f} ₪."
    )
