
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.business_questions import answer_business_question


def _apply_suggested_question(query_key: str, question: str) -> None:
    st.session_state[query_key] = question


def render_ai_accountant(
    compact: bool = False,
    *,
    query_key: str = "ai_accountant_query",
    suggested_questions: list[str] | None = None,
    input_label: str = "מה תרצה לדעת?",
    input_placeholder: str = "למשל: כל החשבוניות מעל 10,000",
    helper_text: str | None = None,
    hide_input_label: bool = False,
):
    if not compact:
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
    if not compact:
        st.write("דוגמאות:", " · ".join(examples))

    query = st.text_input(
        input_label,
        placeholder=input_placeholder,
        key=query_key,
        label_visibility="collapsed" if hide_input_label else "visible",
    )

    if helper_text:
        st.caption(helper_text)

    if suggested_questions:
        suggestion_columns = st.columns(len(suggested_questions), gap="small")
        for index, (column, question) in enumerate(
            zip(suggestion_columns, suggested_questions)
        ):
            with column:
                st.button(
                    question,
                    key=f"{query_key}_suggestion_{index}",
                    on_click=_apply_suggested_question,
                    args=(query_key, question),
                    width="stretch",
                )

    if not query:
        return

    answer = answer_business_question(query)

    if answer["route"] != "invoice_search":
        st.write(answer["message"])
        return

    results = answer["results"]

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
