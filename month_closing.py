
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

from database import close_month, month_summary, search_invoices


def build_month_package(month: str) -> bytes:
    documents = search_invoices(
        start_date=f"{month}-01",
        end_date=f"{month}-31",
        statuses=["approved"],
        min_total=0.0,
        max_total=10_000_000.0,
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "documents.csv",
            documents.to_csv(index=False, encoding="utf-8-sig"),
        )
        summary = {
            "month": month,
            "documents_count": len(documents),
            "total": float(pd.to_numeric(
                documents.get("total"), errors="coerce"
            ).fillna(0).sum()) if not documents.empty else 0.0,
        }
        archive.writestr(
            "summary.json",
            json.dumps(summary, ensure_ascii=False, indent=2),
        )

        for _, row in documents.iterrows():
            path = Path(row["archived_path"])
            if path.exists():
                archive.write(path, arcname=f"original_documents/{path.name}")

    buffer.seek(0)
    return buffer.read()


def render_month_closing():
    st.subheader("סגירת חודש")
    month = st.text_input("חודש", value="2026-07", placeholder="YYYY-MM")
    note = st.text_area("הערה לסגירה", value="")

    if len(month) == 7:
        summary = month_summary(month)
        cols = st.columns(3)
        cols[0].metric("מסמכים", summary["documents_count"])
        cols[1].metric("סה״כ", f"{summary['total']:,.2f} ₪")
        cols[2].metric("סטטוס", "סגור" if summary["closed"] else "פתוח")

        package = build_month_package(month)
        st.download_button(
            "הורד חבילת חודש",
            data=package,
            file_name=f"month_{month}.zip",
            mime="application/zip",
        )

        if not summary["closed"]:
            if st.button("סגור את החודש", type="primary"):
                close_month(month, note)
                st.success("החודש נסגר.")
                st.rerun()
        else:
            st.info(
                f"החודש נסגר ב־{summary['closed_at']}. "
                f"הערה: {summary['note']}"
            )
