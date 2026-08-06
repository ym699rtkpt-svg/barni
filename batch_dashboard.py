
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from batch_runner import run_dataset

def render_batch_dashboard():
    st.subheader("בדיקת מאגר")
    dataset = st.text_input(
        "תיקיית חשבוניות",
        value=str(Path.home() / "restaurant-invoices" / "dataset"),
    )
    output = st.text_input(
        "תיקיית תוצאות",
        value=str(Path.home() / "restaurant-invoices" / "batch-results"),
    )

    if st.button("הרץ סריקה מהירה", type="primary"):
        source = Path(dataset).expanduser()
        if not source.exists():
            st.error(f"התיקייה לא נמצאה: {source}")
        else:
            with st.spinner("סורק את המאגר..."):
                result = run_dataset(source, Path(output))
            st.session_state["batch_result"] = result
            st.success("הסריקה הסתיימה.")

    result = st.session_state.get("batch_result")
    report = Path(output).expanduser() / "report.json"

    if result is None and report.exists():
        result = json.loads(report.read_text(encoding="utf-8"))

    if not result:
        st.info("אין עדיין דוח.")
        return

    summary = result["summary"]
    docs = result["documents"]

    cols = st.columns(5)
    cols[0].metric("מסמכים", summary["files_tested"])
    cols[1].metric("עברו", summary["status_counts"].get("pass", 0))
    cols[2].metric("לבדיקה", summary["status_counts"].get("review", 0))
    cols[3].metric("נכשלו", summary["status_counts"].get("fail", 0))
    cols[4].metric("תור OCR", summary["status_counts"].get("ocr_queue", 0))

    st.metric("שלמות ממוצעת", f"{summary['average_completeness_percent']}%")

    table = pd.DataFrame([{
        "קובץ": d["file_name"],
        "סטטוס": d["status"],
        "שיטה": d["extraction_method"],
        "סוג": d["document_type"],
        "ספק": d["supplier"],
        "מספר": d["invoice_number"],
        "תאריך": d["invoice_date"],
        "סה״כ": d["total"],
        "שורות": d["line_items_count"],
        "בעיות": ", ".join(d["issues"]),
    } for d in docs])
    st.dataframe(table, hide_index=True, width="stretch")
