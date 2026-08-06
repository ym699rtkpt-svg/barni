
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from ai_batch_runner import run as run_ai_batch


def render_ai_dashboard():
    st.subheader("חילוץ AI")
    st.caption(
        "המסמכים נשלחים ל-OpenAI API. מומלץ להתחיל בניסוי של 3 מסמכים."
    )

    dataset = st.text_input(
        "תיקיית המאגר",
        value=str(Path.home() / "restaurant-invoices" / "dataset" / "invoices"),
        key="ai_dataset",
    )
    output = st.text_input(
        "תיקיית תוצאות AI",
        value=str(Path.home() / "restaurant-invoices" / "ai-results"),
        key="ai_output",
    )
    model = st.text_input(
        "מודל",
        value=os.environ.get("INVOICE_AI_MODEL", "gpt-5.6"),
    )
    limit = st.number_input(
        "מספר מסמכים בניסוי",
        min_value=1,
        max_value=500,
        value=3,
    )

    if not os.environ.get("OPENAI_API_KEY"):
        st.warning("לא מוגדר OPENAI_API_KEY במחשב.")

    if st.button("הרץ ניסוי AI", type="primary"):
        os.environ["INVOICE_AI_MODEL"] = model
        with st.spinner("מריץ חילוץ AI..."):
            result = run_ai_batch(
                Path(dataset),
                Path(output),
                limit=int(limit),
            )
        st.session_state["ai_batch_result"] = result
        st.success("הניסוי הסתיים.")

    report = Path(output).expanduser() / "report.json"
    result = st.session_state.get("ai_batch_result")

    if result is None and report.exists():
        result = json.loads(report.read_text(encoding="utf-8"))

    if not result:
        return

    summary = result["summary"]
    columns = st.columns(4)
    columns[0].metric("מסמכים", summary["files_tested"])
    columns[1].metric("עברו", summary["status_counts"].get("pass", 0))
    columns[2].metric("לבדיקה", summary["status_counts"].get("review", 0))
    columns[3].metric("שגיאות", summary["status_counts"].get("error", 0))

    st.metric("מסמכים עם שורות", summary["documents_with_items"])
    st.metric("ביטחון ממוצע", summary["average_confidence"])

    table = pd.DataFrame(result["documents"])
    if not table.empty:
        st.dataframe(table, hide_index=True, width="stretch")
