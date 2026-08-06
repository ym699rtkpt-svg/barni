
from __future__ import annotations

from pathlib import Path

import streamlit as st

from database import database_health


def render_database_diagnostics():
    st.subheader("בריאות מסד הנתונים")
    st.caption(
        "בדיקת גרסה, עמודות חובה וגיבויים שנוצרו לפני מיגרציות."
    )

    try:
        health = database_health()
    except Exception as exc:
        st.error(f"בדיקת המסד נכשלה: {exc}")
        return

    columns = st.columns(4)
    columns[0].metric(
        "גרסת מסד",
        health["schema_version"],
    )
    columns[1].metric(
        "חשבוניות",
        health["invoice_count"],
    )
    columns[2].metric(
        "עמודות חסרות",
        len(health["missing_required_columns"]),
    )
    columns[3].metric(
        "מצב",
        "תקין" if health["healthy"] else "דורש תיקון",
    )

    st.code(health["database_path"])

    if health["healthy"]:
        st.success("מבנה מסד הנתונים תקין.")
    else:
        st.error(
            "חסרות עמודות: "
            + ", ".join(health["missing_required_columns"])
        )

    backup_dir = (
        Path.home()
        / "restaurant-invoices"
        / "database-backups"
    )
    backups = sorted(
        backup_dir.glob("*.db"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    ) if backup_dir.exists() else []

    st.markdown("### גיבויים")
    if not backups:
        st.info("עדיין לא נוצר גיבוי למסד.")
    else:
        for backup in backups[:10]:
            st.write(
                f"{backup.name} · "
                f"{backup.stat().st_size / 1024:.1f} KB"
            )
