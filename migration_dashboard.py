
from pathlib import Path

import streamlit as st

from migrate_ai_results import migrate


def render_migration_dashboard():
    st.subheader("הגירת מאגר קיים")
    st.caption("העברה חד־פעמית של תוצאות ה־AI למסד SQLite, בלי לשכפל מסמכים.")

    results = st.text_input(
        "תיקיית תוצאות AI",
        value=str(Path.home() / "restaurant-invoices" / "ai-results"),
        key="migration_results",
    )
    dataset = st.text_input(
        "תיקיית המסמכים",
        value=str(Path.home() / "restaurant-invoices" / "dataset" / "invoices"),
        key="migration_dataset",
    )

    if st.button("העבר את המאגר למסד", type="primary"):
        with st.spinner("מעביר מסמכים..."):
            result = migrate(Path(results), Path(dataset))
        st.success("ההגירה הסתיימה.")
        st.json(result)
