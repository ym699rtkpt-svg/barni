
from __future__ import annotations

import streamlit as st

from categorizer import classify_all
from database import category_summary, control_center_data, dashboard_data


def render_control_center():
    st.subheader("מרכז בקרה")
    data = control_center_data()

    cols = st.columns(6)
    cols[0].metric("חשבוניות", data["invoice_count"])
    cols[1].metric("ספקים", data["supplier_count"])
    cols[2].metric("מע״מ", f"{data['vat_total']:,.2f} ₪")
    cols[3].metric("דורשות בדיקה", data["review_count"])
    cols[4].metric("כפילויות", data["duplicates"])
    cols[5].metric("לא מסווגות", data["uncategorized"])

    if data["latest_month"]:
        st.info(
            f"החודש האחרון במאגר: {data['latest_month']} · "
            f"{data['latest_month_count']} מסמכים"
        )


def render_enhanced_dashboard():
    render_control_center()

    if st.button("סווג אוטומטית את כל ההוצאות"):
        with st.spinner("מסווג חשבוניות..."):
            result = classify_all()
        st.success(f"סווגו {result['processed']} מסמכים.")
        st.json(result["categories"])
        st.rerun()

    data = dashboard_data()
    documents = data["documents"]

    if documents.empty:
        st.info("אין עדיין מסמכים.")
        return

    st.markdown("### הוצאות לפי חודש")
    monthly = data["monthly_spend"]
    if not monthly.empty:
        st.line_chart(monthly.set_index("month")["total"])

    st.markdown("### ספקים מובילים")
    supplier_spend = data["supplier_spend"].head(10)
    if not supplier_spend.empty:
        st.bar_chart(supplier_spend.set_index("supplier")["total"])
        st.dataframe(supplier_spend, hide_index=True, width="stretch")

    st.markdown("### הוצאות לפי קטגוריה")
    categories = category_summary()
    if not categories.empty:
        st.bar_chart(
            categories.groupby("category")["total"].sum()
        )
        st.dataframe(categories, hide_index=True, width="stretch")

    st.markdown("### סוגי מסמכים")
    st.dataframe(data["document_types"], hide_index=True, width="stretch")
