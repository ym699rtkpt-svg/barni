
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from ai_extractor import extract_with_ai
from hybrid_engine import normalize_document, validate_document
from review_form import approve_to_database, document_review_form


def _safe_name(name: str) -> str:
    return "".join(
        char if char.isalnum() or char in " ._-()[]אבגדהוזחטיכלמנסעפצקרשת"
        else "_"
        for char in name
    ).strip() or "document"


def _paths() -> dict[str, Path]:
    root = Path.home() / "restaurant-invoices"
    paths = {
        "incoming": root / "daily-intake" / "incoming",
        "processed": root / "daily-intake" / "processed",
        "rejected": root / "daily-intake" / "rejected",
        "queue": root / "daily-intake" / "queue.json",
    }
    for key in ("incoming", "processed", "rejected"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def _load_queue(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_queue(path: Path, queue: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _record_id(file_name: str) -> str:
    return (
        datetime.now().strftime("%Y%m%d%H%M%S%f")
        + "_"
        + Path(file_name).stem
    )


def _status_for(document: dict) -> str:
    validation = validate_document(document)
    confidence = float(document.get("confidence") or 0.0)

    if validation["machine_issues"]:
        return "review"
    if validation["model_notes"] or confidence < 0.90:
        return "review"
    return "ready"


def process_files(uploaded_files, model: str) -> None:
    paths = _paths()
    queue = _load_queue(paths["queue"])

    for uploaded in uploaded_files:
        safe_name = _safe_name(uploaded.name)
        record_id = _record_id(safe_name)
        stored = paths["incoming"] / f"{record_id}_{safe_name}"
        stored.write_bytes(uploaded.getbuffer())

        record = {
            "id": record_id,
            "file_name": safe_name,
            "stored_file": str(stored),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "queue_status": "processing",
            "error": "",
            "document": {},
        }

        try:
            document, method = extract_with_ai(stored, model=model)
            document = normalize_document(document)
            validation = validate_document(document)
            document["machine_issues"] = validation["machine_issues"]
            document["model_notes"] = validation["model_notes"]
            document["warnings"] = (
                validation["machine_issues"]
                + validation["model_notes"]
            )

            record["document"] = document
            record["method"] = method
            record["queue_status"] = _status_for(document)

            detail = paths["processed"] / f"{record_id}.json"
            detail.write_text(
                json.dumps(record, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            record["detail_file"] = str(detail)

        except Exception as exc:
            record["queue_status"] = "error"
            record["error"] = str(exc)

        queue.append(record)
        _save_queue(paths["queue"], queue)


def _remove_from_active_queue(record_id: str, new_status: str) -> None:
    paths = _paths()
    queue = _load_queue(paths["queue"])
    for record in queue:
        if record["id"] == record_id:
            record["queue_status"] = new_status
            record[f"{new_status}_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            break
    _save_queue(paths["queue"], queue)


def reject_record(record_id: str) -> None:
    paths = _paths()
    queue = _load_queue(paths["queue"])

    for record in queue:
        if record["id"] == record_id:
            source = Path(record["stored_file"])
            if source.exists():
                target = paths["rejected"] / source.name
                shutil.move(str(source), str(target))
                record["stored_file"] = str(target)
            record["queue_status"] = "rejected"
            record["rejected_at"] = datetime.now().isoformat(
                timespec="seconds"
            )
            break
    _save_queue(paths["queue"], queue)


def render_daily_intake():
    st.subheader("קליטה יומית")
    st.caption(
        "העלאה מרובה, עריכת נתונים, אישור למסד הנתונים וארכיון לפי שנה וחודש."
    )

    paths = _paths()
    model = st.text_input(
        "מודל AI",
        value="gpt-5.6",
        key="daily_intake_model",
    )

    uploaded = st.file_uploader(
        "בחר כמה חשבוניות או תמונות",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="daily_intake_upload",
    )

    if uploaded and st.button("עבד את כל הקבצים", type="primary"):
        with st.spinner("מעבד את הקבצים..."):
            process_files(uploaded, model)
        st.success("העיבוד הסתיים.")
        st.rerun()

    queue = _load_queue(paths["queue"])
    active = [
        record for record in queue
        if record.get("queue_status") in {"ready", "review", "error"}
    ]

    cols = st.columns(4)
    cols[0].metric("בתור", len(active))
    cols[1].metric(
        "מוכנים",
        sum(record.get("queue_status") == "ready" for record in active),
    )
    cols[2].metric(
        "דורשים בדיקה",
        sum(record.get("queue_status") == "review" for record in active),
    )
    cols[3].metric(
        "שגיאות",
        sum(record.get("queue_status") == "error" for record in active),
    )

    if not active:
        st.info("אין כרגע מסמכים בתור.")
        return

    rows = []
    for record in active:
        document = record.get("document", {})
        rows.append({
            "id": record["id"],
            "קובץ": record.get("file_name", ""),
            "סטטוס": record.get("queue_status", ""),
            "ספק": document.get("supplier", ""),
            "מספר": document.get("invoice_number", ""),
            "תאריך": document.get("invoice_date", ""),
            "סוג": document.get("document_type", ""),
            "מצב מע״מ": document.get("tax_treatment", ""),
            "חייב": document.get("taxable_amount"),
            "פטור": document.get("exempt_amount"),
            "מע״מ": document.get("vat"),
            "סה״כ": document.get("total"),
            "ביטחון": document.get("confidence", 0.0),
            "בעיות": " | ".join(document.get("machine_issues", [])),
            "הערות": " | ".join(document.get("model_notes", [])),
        })

    table = pd.DataFrame(rows)
    st.dataframe(
        table.drop(columns=["id"]),
        hide_index=True,
        width="stretch",
        column_config={
            "סה״כ": st.column_config.NumberColumn(format="%.2f ₪"),
            "ביטחון": st.column_config.NumberColumn(format="%.1%"),
        },
    )

    option_map = {
        f"{row['סטטוס']} | {row['ספק']} | {row['מספר']} | {row['קובץ']}":
        row["id"]
        for row in rows
    }
    selected_label = st.selectbox(
        "בחר מסמך לבדיקה",
        options=list(option_map.keys()),
    )
    selected_id = option_map[selected_label]
    record = next(
        record for record in active
        if record["id"] == selected_id
    )

    left, right = st.columns([1.0, 1.3])

    with left:
        st.markdown("### המסמך")
        source = Path(record["stored_file"])
        if source.exists() and source.suffix.lower() == ".pdf":
            st.download_button(
                "פתח / הורד PDF",
                data=source.read_bytes(),
                file_name=record["file_name"],
                mime="application/pdf",
            )
        elif source.exists():
            st.image(str(source), width="stretch")

        if record.get("error"):
            st.error(record["error"])

    with right:
        updated_document, _, saved = document_review_form(
            record,
            form_key=f"review_{selected_id}",
        )

        if saved:
            record["document"] = updated_document
            queue = _load_queue(paths["queue"])
            for item in queue:
                if item["id"] == selected_id:
                    item["document"] = updated_document
                    item["queue_status"] = "ready"
                    break
            _save_queue(paths["queue"], queue)
            st.success("העריכות נשמרו בתור.")
            st.rerun()

    action1, action2 = st.columns(2)

    if action1.button(
        "אשר ושמור במסד",
        type="primary",
        width="stretch",
    ):
        success, message = approve_to_database(
            record,
            record.get("document", {}),
        )
        if success:
            _remove_from_active_queue(selected_id, "approved")
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    if action2.button("דחה", width="stretch"):
        reject_record(selected_id)
        st.warning("המסמך נדחה.")
        st.rerun()
