
from __future__ import annotations

import streamlit as st

from database import dashboard_data


def render_database_dashboard():
    st.subheader("דשבורד מסד הנתונים")
    data = dashboard_data()
    documents = data["documents"]
    items = data["items"]

    if documents.empty:
        st.info("עדיין אין מסמכים מאושרים במסד.")
        return

    cols = st.columns(5)
    cols[0].metric("מסמכים", len(documents))
    cols[1].metric("ספקים", documents["supplier"].nunique())
    cols[2].metric("שורות מוצרים", len(items))
    cols[3].metric(
        "סה״כ הוצאות",
        f"{documents['total'].fillna(0).sum():,.2f} ₪",
    )
    cols[4].metric(
        "דורשים בדיקה",
        int((documents["status"] == "review").sum()),
    )

    st.markdown("### הוצאות לפי ספק")
    supplier_spend = data["supplier_spend"]
    if not supplier_spend.empty:
        st.bar_chart(
            supplier_spend.set_index("supplier")["total"],
        )
        st.dataframe(
            supplier_spend,
            hide_index=True,
            width="stretch",
        )

    st.markdown("### הוצאות לפי חודש")
    monthly = data["monthly_spend"]
    if not monthly.empty:
        st.line_chart(monthly.set_index("month")["total"])

    st.markdown("### סוגי מסמכים")
    st.dataframe(
        data["document_types"],
        hide_index=True,
        width="stretch",
    )
