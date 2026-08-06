
from pathlib import Path

import streamlit as st

from business_analytics import (
    build_audit,
    build_price_alerts,
    create_accountant_package,
    dashboard_metrics,
    load_ai_results,
    supplier_comparison,
)


def render_business_dashboard():
    st.subheader("ניהול העסק")
    st.caption("ביקורת, דשבורד, התראות וחבילת רואה חשבון.")

    results_dir = st.text_input(
        "תיקיית תוצאות AI",
        value=str(Path.home() / "restaurant-invoices" / "ai-results"),
        key="business_results_dir",
    )
    dataset_dir = st.text_input(
        "תיקיית המסמכים המקוריים",
        value=str(Path.home() / "restaurant-invoices" / "dataset" / "invoices"),
        key="business_dataset_dir",
    )

    try:
        documents, items = load_ai_results(Path(results_dir))
    except Exception as exc:
        st.error(str(exc))
        return

    audit_tab, dashboard_tab, alerts_tab, accountant_tab = st.tabs(
        ["ביקורת", "דשבורד", "התראות", "רואה חשבון"]
    )

    with audit_tab:
        audit = build_audit(documents)
        c1, c2, c3 = st.columns(3)
        c1.metric("מסמכים", len(documents))
        c2.metric("עברו", int((documents["status"] == "pass").sum()))
        c3.metric("דורשים בדיקה", int((documents["status"] == "review").sum()))

        if audit.empty:
            st.success("לא נמצאו חריגות.")
        else:
            order = {"high": 0, "medium": 1, "info": 2}
            audit["_order"] = audit["severity"].map(order).fillna(3)
            audit = audit.sort_values(["_order", "invoice_date"]).drop(columns="_order")
            st.dataframe(audit, hide_index=True, width="stretch")

    with dashboard_tab:
        metrics = dashboard_metrics(documents, items)
        cols = st.columns(5)
        cols[0].metric("מסמכים", metrics["document_count"])
        cols[1].metric("חשבונאיים", metrics["accounting_document_count"])
        cols[2].metric("ספקים", metrics["supplier_count"])
        cols[3].metric("שורות מוצרים", metrics["item_rows"])
        cols[4].metric("סה״כ", f"{metrics['total_spend']:,.2f} ₪")

        st.subheader("הוצאות לפי ספק")
        supplier_spend = metrics["supplier_spend"]
        if not supplier_spend.empty:
            st.bar_chart(supplier_spend.set_index("supplier")["total"])
            st.dataframe(supplier_spend, hide_index=True, width="stretch")

        st.subheader("הוצאות לפי חודש")
        monthly = metrics["monthly_spend"]
        if not monthly.empty:
            st.line_chart(monthly.set_index("month")["total"])

        st.subheader("סוגי מסמכים")
        st.dataframe(metrics["document_types"], hide_index=True, width="stretch")

    with alerts_tab:
        price_alerts = build_price_alerts(items)
        comparisons = supplier_comparison(items)

        st.subheader("שינויי מחיר")
        if price_alerts.empty:
            st.info("עדיין אין מספיק היסטוריה לאותו מוצר.")
        else:
            threshold = st.slider("סף שינוי", 5, 50, 5, format="%d%%")
            filtered = price_alerts[
                price_alerts["change_percent"].abs() >= threshold
            ].sort_values(
                "change_percent",
                key=lambda series: series.abs(),
                ascending=False,
            )
            st.dataframe(filtered, hide_index=True, width="stretch")

        st.subheader("פערים בין ספקים")
        if comparisons.empty:
            st.info("עדיין אין מספיק מוצרים זהים בין ספקים.")
        else:
            st.dataframe(comparisons, hide_index=True, width="stretch")

    with accountant_tab:
        month = st.text_input(
            "חודש לייצוא, למשל 2026-07. השאר ריק לכל התקופה",
            value="",
        )
        if st.button("צור חבילת רואה חשבון", type="primary"):
            with st.spinner("יוצר חבילה..."):
                zip_path = create_accountant_package(
                    documents,
                    items,
                    Path(dataset_dir),
                    Path.home() / "restaurant-invoices" / "accountant-exports",
                    month.strip(),
                )
            st.success(f"החבילה נוצרה: {zip_path}")
            st.download_button(
                "הורד ZIP",
                data=zip_path.read_bytes(),
                file_name=zip_path.name,
                mime="application/zip",
            )
