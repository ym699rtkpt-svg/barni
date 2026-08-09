
from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st

from database import duplicate_invoice, root_dir
from hybrid_engine import extract_hybrid, normalize_document, validate_document
from knowledge_engine.line_classifier import classify_invoice_line
from review_form import approve_to_database_detailed, document_review_form
from services.barni_thinking import think_about_invoice
from services.business_memory import business_memory_data
from services.business_stories import BusinessStoryEngine, StoryContext
from services.invoice_workflow import invoice_workflow_snapshot, load_queue_records
from services.invoice_intelligence_adapter import analyze_invoice_record
from services.pilot_support import log_pilot_event, log_runtime_error
from services.document_text import extract_document_text
from services.invoice_reuse import approved_document_for_identical_source
from services.feed_journal import FeedJournalCursor
from ui.barni_thinking import render_barni_thinking
from ui.business_story import render_business_story
from ui.workflow_status import render_workflow_status


def _render_feed_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-feed_intro {
            text-align: center;
            padding: 0.8rem 1rem 1.2rem;
        }
        .barni-feed-egg {
            display: inline-block;
            font-size: 4.6rem;
            line-height: 1;
            margin-bottom: 0.55rem;
            transform-origin: 50% 86%;
            filter: drop-shadow(0 5px 7px rgba(45, 70, 53, 0.10));
        }
        .barni-hatch-moment {
            min-height: 16rem;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .barni-hatch-scene {
            width: 13rem;
            filter: drop-shadow(0 9px 11px rgba(45, 70, 53, 0.12));
            transform-origin: 50% 82%;
            animation: barni-hatch-wobble 2.3s ease-in-out both;
        }
        .barni-hatch-crack {
            opacity: 0;
            stroke-dasharray: 42;
            stroke-dashoffset: 42;
            animation: barni-crack-open 2.3s ease-out both;
        }
        .barni-hatch-top {
            transform-origin: 91px 84px;
            animation: barni-shell-open 2.3s ease-in-out both;
        }
        .barni-hatch-bottom {
            transform-origin: 91px 126px;
            animation: barni-shell-bottom-open 2.3s ease-in-out both;
        }
        .barni-hatchling {
            opacity: 0;
            transform: translateY(25px);
            transform-origin: center;
            animation: barni-hatchling-rise 2.3s ease-out both;
        }
        @keyframes barni-hatch-wobble {
            0%, 14%, 32%, 100% { transform: rotate(0deg) scale(1, 1); }
            18% { transform: rotate(-4deg) scale(1.025, 0.975); }
            22% { transform: rotate(4.2deg) scale(0.98, 1.025); }
            26% { transform: rotate(-2.5deg) scale(1.015, 0.988); }
            30% { transform: rotate(1.5deg) scale(0.995, 1.01); }
        }
        @keyframes barni-crack-open {
            0%, 27% { opacity: 0; stroke-dashoffset: 42; }
            35%, 44% { opacity: 0.85; stroke-dashoffset: 19; }
            51%, 100% { opacity: 1; stroke-dashoffset: 0; }
        }
        @keyframes barni-shell-open {
            0%, 50% { transform: translate(0, 0) rotate(0deg); }
            65%, 100% { transform: translate(-14px, -18px) rotate(-16deg); }
        }
        @keyframes barni-shell-bottom-open {
            0%, 50% { transform: translate(0, 0) rotate(0deg); }
            65%, 100% { transform: translate(5px, 5px) rotate(2.5deg); }
        }
        @keyframes barni-hatchling-rise {
            0%, 58% { opacity: 0; transform: translateY(25px); }
            70% { opacity: 1; transform: translateY(-3px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .barni-feed-egg--awake {
            animation: feed-egg-awake 3s ease-in-out infinite;
        }
        .barni-feed-egg--learning {
            animation: feed-egg-learning 1.6s ease-in-out infinite;
        }
        .barni-feed-egg--small {
            font-size: 2.3rem;
            margin: 0.25rem 0 0.45rem;
        }
        @keyframes feed-egg-awake {
            0%, 68%, 84%, 100% { transform: rotate(0deg) scale(1, 1); }
            74% { transform: rotate(-1.8deg) scale(1.012, 0.992); }
            79% { transform: rotate(1.7deg) scale(0.995, 1.012); }
            89% { transform: rotate(-1deg) scale(1.006, 0.997); }
            94% { transform: rotate(0.9deg) scale(0.998, 1.007); }
        }
        @keyframes feed-egg-learning {
            0%, 55%, 100% {
                transform: rotate(0deg) scale(1, 1);
                filter: drop-shadow(0 5px 7px rgba(45, 70, 53, 0.10));
            }
            66% {
                transform: rotate(-2.4deg) scale(1.018, 0.986);
                filter: drop-shadow(2px 7px 8px rgba(45, 70, 53, 0.15));
            }
            76% {
                transform: rotate(2.5deg) scale(0.988, 1.020);
                filter: drop-shadow(-2px 7px 8px rgba(45, 70, 53, 0.15));
            }
            86% { transform: rotate(-1.2deg) scale(1.008, 0.996); }
        }
        .st-key-feed_upload {
            background: #f8f4ea;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 20px;
            padding: 1.4rem 1.6rem;
        }
        .st-key-feed_upload [data-testid="stFileUploaderDropzone"] {
            min-height: 13rem;
            align-items: center;
            justify-content: center;
            background: #fcfbf7;
            border: 1px dashed rgba(45, 70, 53, 0.28);
            border-radius: 16px;
        }
        .st-key-feed_summary {
            background: #f2f5ed;
            border: 1px solid rgba(63, 91, 68, 0.14);
            border-radius: 18px;
            padding: 1.35rem 1.5rem;
        }
        .st-key-feed_completion {
            background: #eef3e8;
            border: 1px solid rgba(63, 91, 68, 0.16);
            border-radius: 20px;
            padding: 1.35rem 1.5rem;
        }
        [class*="st-key-feed_metric_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.75rem 1rem;
        }
        .st-key-feed_queue {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.35rem 0.5rem;
            color-scheme: light;
        }
        .st-key-feed_queue [data-testid="stDataFrame"] {
            background: #fcfbf7;
            border: 1px solid #dfe5dc;
        }
        .st-key-duplicate_warning {
            background: #fbf4e8;
            border: 1px solid rgba(174, 112, 42, 0.22);
            border-radius: 20px;
            padding: 1.3rem 1.5rem;
        }
        [class*="st-key-confidence_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.85rem 1rem;
        }
        .st-key-review_attention {
            background: #fbf4e8;
            border: 1px solid rgba(174, 112, 42, 0.18);
            border-radius: 16px;
            padding: 0.9rem 1.1rem;
        }
        .st-key-feed_error {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 16px;
            padding: 0.9rem 1.1rem;
        }
        .st-key-feed_review_header,
        .st-key-feed_done {
            background: #f2f5ed;
            border: 1px solid rgba(63, 91, 68, 0.14);
            border-radius: 20px;
            padding: 1.15rem 1.35rem;
        }
        .st-key-feed_review_panel {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 20px;
            padding: 1.1rem 1.25rem;
        }
        .barni-feed-status {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #eef3e8;
            color: #315b3d;
            font-size: 0.82rem;
            font-weight: 650;
        }
        .barni-feed-status--attention {
            background: #fbf4e8;
            color: #83531f;
        }
        @media (prefers-reduced-motion: reduce) {
            .barni-feed-egg--awake,
            .barni-feed-egg--learning {
                animation: none;
                transform: none;
            }
            .barni-hatch-scene { animation: none; }
            .barni-hatch-crack {
                animation: none;
                opacity: 1;
                stroke-dashoffset: 0;
            }
            .barni-hatch-top {
                animation: none;
                transform: translate(-14px, -18px) rotate(-16deg);
            }
            .barni-hatch-bottom {
                animation: none;
                transform: translate(5px, 5px) rotate(2.5deg);
            }
            .barni-hatchling {
                animation: none;
                opacity: 1;
                transform: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_feed_egg(state: str = "calm", *, small: bool = False) -> None:
    classes = ["barni-feed-egg", f"barni-feed-egg--{state}"]
    if small:
        classes.append("barni-feed-egg--small")
    st.markdown(
        f'<div class="{" ".join(classes)}" data-barni-growth-state="egg" '
        'aria-label="Barni egg">🥚</div>',
        unsafe_allow_html=True,
    )


def _render_hatch_moment() -> None:
    """Render Barni's temporary, asset-free hatchling transition."""
    st.markdown(
        """
        <div class="barni-hatch-moment" data-barni-growth-state="hatchling">
          <svg class="barni-hatch-scene" viewBox="0 0 182 176"
               role="img" aria-label="Barni hatching">
            <ellipse cx="91" cy="158" rx="47" ry="7" fill="#dfe5dc" opacity="0.55"/>
            <g class="barni-hatchling">
              <path d="M59 112c0-28 14-47 32-47s32 19 32 47v28H59z"
                    fill="#315b3d"/>
              <ellipse cx="79" cy="99" rx="4" ry="5" fill="#fcfbf7"/>
              <ellipse cx="103" cy="99" rx="4" ry="5" fill="#fcfbf7"/>
              <circle cx="80" cy="100" r="1.5" fill="#24362b"/>
              <circle cx="102" cy="100" r="1.5" fill="#24362b"/>
              <path d="M83 112c5 4 11 4 16 0" fill="none" stroke="#fcfbf7"
                    stroke-width="2.3" stroke-linecap="round"/>
            </g>
            <path class="barni-hatch-bottom" d="M44 103l13-7 10 9 12-9 12 10 12-10 11 9 13-7
                     c-1 34-15 57-36 57-23 0-40-21-47-52z"
                  fill="#f7f3e9" stroke="#78917d" stroke-width="2"/>
            <g class="barni-hatch-top">
              <path d="M44 103l13-7 10 9 12-9 12 10 12-10 11 9 13-7
                       C122 50 108 28 90 28c-22 0-39 29-46 75z"
                    fill="#fcfbf7" stroke="#78917d" stroke-width="2"/>
              <path class="barni-hatch-crack" d="M91 52l-9 17 11 8-10 20"
                    fill="none" stroke="#315b3d" stroke-width="3.3"
                    stroke-linecap="round" stroke-linejoin="round"/>
            </g>
          </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _processing_summary(records: list[dict]) -> dict[str, int]:
    documents = [record.get("document") or {} for record in records]
    suppliers = {
        str(document.get("supplier") or "").strip()
        for document in documents
        if str(document.get("supplier") or "").strip()
    }
    items = [
        item
        for document in documents
        for item in (document.get("items") or [])
        if isinstance(item, dict)
    ]
    product_items = [
        item
        for item in items
        if (
            item.get("line_type")
            or classify_invoice_line(str(item.get("description") or ""))
        ) == "product"
    ]
    return {
        "processed": sum(
            record.get("queue_status") in {"ready", "review"}
            for record in records
        ),
        "ready": sum(
            record.get("queue_status") == "ready" for record in records
        ),
        "review": sum(
            record.get("queue_status") == "review" for record in records
        ),
        "error": sum(
            record.get("queue_status") == "error" for record in records
        ),
        "suppliers": len(suppliers),
        "products": sum(
            bool(str(item.get("description") or "").strip())
            for item in product_items
        ),
        "price_points": sum(
            item.get("unit_price") not in (None, "")
            for item in product_items
        ),
    }


def _count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def _render_processing_summary(summary: dict[str, int]) -> None:
    with st.container(key="feed_summary"):
        st.markdown("### Barni prepared")
        st.write(f"✓ {_count_phrase(summary['processed'], 'document')} read")
        st.write(f"✓ {_count_phrase(summary['ready'], 'document')} ready to approve")
        if summary["review"]:
            st.write(
                f"• {_count_phrase(summary['review'], 'document')} need a quick review"
            )
        if summary["error"]:
            st.write(
                f"• {_count_phrase(summary['error'], 'document')} could not be processed"
            )
        st.caption("Business memory updates only after you review and approve a document.")


def _memory_delta(before: dict, after: dict) -> dict[str, int]:
    return {
        "invoices": max(0, after["invoice_count"] - before["invoice_count"]),
        "suppliers": max(0, after["supplier_count"] - before["supplier_count"]),
        "products": max(0, after["product_count"] - before["product_count"]),
        "price_points": max(
            0,
            after["price_point_count"] - before["price_point_count"],
        ),
    }


def _render_completion(completion: dict) -> None:
    with st.container(key="feed_completion"):
        story = completion.get("story")
        if story is not None:
            render_business_story(story, key="feed_completion_story")
        else:
            st.markdown("### 🧠 Barni learned something new")
        if completion["outcome"] == "skipped":
            return
        learned = [
            (completion.get("invoices", 0), "invoice learned", "invoices learned"),
            (completion.get("suppliers", 0), "new supplier learned", "new suppliers learned"),
            (completion.get("products", 0), "product learned", "products learned"),
            (completion.get("price_points", 0), "price point added", "price points added"),
        ]
        for count, singular, plural in learned:
            if count:
                st.write(f"✓ {_count_phrase(count, singular, plural)}")
        if not any(count for count, _, _ in learned):
            st.write("Business memory was updated from the approved invoice.")
        if completion["outcome"] == "replaced":
            st.caption("The existing invoice was replaced and business memory was updated.")
        elif completion["outcome"] == "kept_both":
            st.caption("Both invoices were kept and business memory was updated.")
        else:
            st.caption("Business memory updated successfully.")
        if completion["outcome"] != "skipped":
            st.button(
                "See it in Business Memory",
                key="feed_view_learned",
                on_click=_view_what_barni_learned,
                type="secondary",
            )


def _view_what_barni_learned() -> None:
    st.session_state.pop("daily_intake_completion", None)
    query = str(st.session_state.get("daily_intake_last_search") or "").strip()
    if query:
        st.session_state.search_query = query
    st.session_state.current_page = "חיפוש חשבוניות"


def _open_business_memory() -> None:
    st.session_state.current_page = "Business Memory"


def _open_evidence_invoice(invoice_id: int) -> None:
    st.session_state.search_selected_kind = "invoice"
    st.session_state.search_selected_value = invoice_id
    st.session_state.search_show_document = False
    st.session_state.current_page = "חיפוש חשבוניות"


def _safe_name(name: str) -> str:
    return "".join(
        char if char.isalnum() or char in " ._-()[]אבגדהוזחטיכלמנסעפצקרשת"
        else "_"
        for char in name
    ).strip() or "document"


def _paths() -> dict[str, Path]:
    root = root_dir()
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
    """Compatibility wrapper around the canonical workflow queue reader."""
    return load_queue_records(path)


def _save_queue(path: Path, queue: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(queue, ensure_ascii=False, indent=2)
    backup = path.with_suffix(path.suffix + ".backup")
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = None
        if isinstance(existing, list):
            shutil.copy2(path, backup)

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


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


def _document_recovery_message(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return "I couldn't read this PDF. Try a clearer copy, or add the invoice details during review."
    return "I couldn't read this image. Try a sharper photo, or add the invoice details during review."


def _review_reason(record: dict) -> str:
    """Return the stored evidence that explains why a document needs attention."""
    document = record.get("document") or {}
    reasons = []

    for field in ("machine_issues", "model_notes"):
        value = document.get(field) or []
        if isinstance(value, str):
            value = [value]
        reasons.extend(str(item).strip() for item in value if str(item).strip())

    if record.get("queue_status") == "error":
        reasons.append(_document_recovery_message(
            Path(record.get("stored_file") or "invoice")
        ))

    if not reasons and record.get("queue_status") == "review":
        confidence = float(document.get("confidence") or 0.0)
        if confidence < 0.90:
            reasons.append("Low extraction confidence")

    if reasons:
        return " · ".join(dict.fromkeys(reasons))
    if record.get("queue_status") == "ready":
        return "Ready for approval"
    return "Review the extracted invoice details"


def _needs_review(record: dict) -> bool:
    return record.get("queue_status") in {"review", "error"}


def _approval_blockers(document: dict) -> list[str]:
    labels = {
        "supplier": "supplier",
        "invoice_date": "invoice date",
        "total": "total",
        "document_type": "document type",
    }
    missing = [label for field, label in labels.items()
               if document.get(field) in (None, "")]
    if document.get("document_type") in {
        "חשבונית מס", "חשבונית מס/קבלה", "חשבונית זיכוי", "תעודת משלוח",
    } and not document.get("items"):
        missing.append("at least one product")
    return missing


def _queue_priority(record: dict) -> tuple[int, str]:
    priority = {"review": 0, "error": 1, "ready": 2}
    return (
        priority.get(record.get("queue_status"), 3),
        str(record.get("created_at") or ""),
    )


def _style_review_queue(table: pd.DataFrame):
    """Keep review states readable without relying on color alone."""
    row_backgrounds = {
        "ready": "#f1f5ed",
        "review": "#fbf4e8",
        "error": "#faf0ed",
    }

    def style_row(row: pd.Series) -> list[str]:
        background = row_backgrounds.get(row.get("סטטוס"), "#fcfbf7")
        rule = (
            f"background-color: {background}; color: #24362b; "
            "border-color: #dfe5dc;"
        )
        return [rule] * len(row)

    return table.style.apply(style_row, axis=1).set_table_styles([
        {
            "selector": "th",
            "props": [
                ("background-color", "#eef3e8"),
                ("color", "#24362b"),
                ("border-color", "#dfe5dc"),
            ],
        },
    ])


def _stored_confidence(document: dict, field: str) -> float | None:
    """Read a stored confidence value without deriving or estimating one."""
    if field not in document or document.get(field) in (None, ""):
        return None
    try:
        value = float(document[field])
    except (TypeError, ValueError):
        return None
    return value if 0.0 <= value <= 1.0 else None


def _render_confidence_summary(document: dict) -> None:
    confidence_fields = (
        ("OCR Confidence", "confidence"),
        ("Supplier Confidence", "supplier_confidence"),
        ("Products Confidence", "products_confidence"),
    )
    columns = st.columns(3, gap="medium")
    for index, (label, field) in enumerate(confidence_fields):
        value = _stored_confidence(document, field)
        with columns[index]:
            with st.container(key=f"confidence_{field}"):
                st.caption(label)
                st.markdown(f"### {value:.0%}" if value is not None else "### Unavailable")

    issues = document.get("machine_issues") or []
    notes = document.get("model_notes") or []
    if issues or notes:
        with st.container(key="review_attention"):
            st.markdown("**Some details need your attention**")
            st.caption(_review_reason({"document": document, "queue_status": "review"}))
    elif _stored_confidence(document, "confidence") is None:
        st.caption("OCR confidence is unavailable for this invoice.")


def process_files(
    uploaded_files,
    model: str,
    on_stage: Callable[[str, int, int, str], None] | None = None,
) -> None:
    paths = _paths()
    queue = _load_queue(paths["queue"])
    notify = on_stage or (lambda _stage, _index, _total, _name: None)

    total_files = len(uploaded_files)
    for index, uploaded in enumerate(uploaded_files, start=1):
        safe_name = _safe_name(uploaded.name)
        record_id = _record_id(safe_name)
        stored = paths["incoming"] / f"{record_id}_{safe_name}"

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
            stored.write_bytes(uploaded.getbuffer())
            notify("reading", index, total_files, safe_name)
            document = approved_document_for_identical_source(stored, safe_name)
            if document is not None:
                method = "stored_evidence_match"
                raw_text = ""
                local_method = "stored_evidence_match"
            else:
                raw_text, local_method = extract_document_text(stored)
                document, method = extract_hybrid(
                    stored,
                    raw_text=raw_text,
                    use_ai=True,
                    ai_model=model,
                )
                document["raw_text"] = raw_text
            document["local_text_method"] = local_method
            notify("supplier", index, total_files, safe_name)
            document = normalize_document(document)
            notify("products", index, total_files, safe_name)
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
            record["error"] = _document_recovery_message(stored)
            record["technical_error"] = str(exc)

        queue.append(record)
        _save_queue(paths["queue"], queue)
        notify("complete", index, total_files, safe_name)


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


def _approve_record(record: dict, duplicate_resolution: str = "ask") -> dict:
    try:
        memory_before = business_memory_data()
    except Exception:
        memory_before = None
    progress_messages = {
        "duplicate_check": "Checking for duplicates",
        "saving": "Saving the approved invoice",
    }
    with st.status("Barni is updating Business Memory...", expanded=True) as status:
        def show_progress(stage: str) -> None:
            if stage == "learning":
                st.write("Checking prices")
                _render_feed_egg("learning", small=True)
                st.write("Updating business memory")
            else:
                st.write(progress_messages[stage])

        success, message, outcome = approve_to_database_detailed(
            record,
            record.get("document", {}),
            on_progress=show_progress,
            duplicate_resolution=duplicate_resolution,
        )
        status.update(
            label="Business Memory updated" if success else "Your decision is needed",
            state="complete" if success or outcome["outcome"] == "duplicate" else "error",
            expanded=False,
        )

    if success:
        st.session_state.pop("daily_intake_recovery", None)
        if outcome["outcome"] == "skipped":
            completion = {"outcome": "skipped"}
            queue_status = "skipped"
        else:
            try:
                memory_after = business_memory_data()
                delta = (
                    _memory_delta(memory_before, memory_after)
                    if memory_before is not None
                    else {"invoices": 0, "suppliers": 0, "products": 0, "price_points": 0}
                )
            except Exception:
                delta = {"invoices": 0, "suppliers": 0, "products": 0, "price_points": 0}
            completion = {
                "outcome": outcome["outcome"],
                **delta,
            }
            queue_status = "approved"
        _remove_from_active_queue(record["id"], queue_status)
        learning_delta = (
            completion
            if outcome["outcome"] != "skipped"
            else {"invoices": 0, "suppliers": 0, "products": 0, "price_points": 0}
        )
        try:
            stories = BusinessStoryEngine().generate(
                StoryContext(
                    current_invoice_id=outcome.get("invoice_id"),
                    approval_outcome=outcome.get("outcome", ""),
                    memory_delta=learning_delta,
                ),
                max_stories=1,
            )
        except Exception:
            stories = []
        story = stories[0] if stories else None
        if story is not None:
            completion["story"] = story
            st.session_state["barni_latest_business_story"] = story
        st.session_state["daily_intake_completion"] = completion
        if outcome["outcome"] != "skipped":
            if story is not None:
                st.session_state.setdefault("daily_intake_batch_learning", []).append(story)
            document = record.get("document") or {}
            st.session_state["daily_intake_last_search"] = (
                str(document.get("supplier") or "").strip()
                or str(document.get("invoice_number") or "").strip()
            )
    elif outcome["outcome"] != "duplicate":
        st.session_state["daily_intake_recovery"] = message
        st.error(message)
    else:
        log_pilot_event(
            "duplicate_detected",
            metadata={
                "queue_record_id": record.get("id"),
                "existing_invoice_id": outcome.get("invoice_id"),
            },
        )
    return {"success": success, "message": message, **outcome}


def _render_daily_intake_console():
    _render_feed_styles()
    selected_files = st.session_state.get("daily_intake_upload") or []
    egg_state = "awake" if selected_files else "calm"
    with st.container(key="feed_intro"):
        _render_feed_egg(egg_state)
        st.markdown("## Feed Barni")
        st.caption("Every invoice teaches Barni something new.")

    paths = _paths()
    with st.container(key="feed_upload"):
        st.markdown("### Upload invoices")
        st.caption("Drag and drop PDFs or images. Nothing is learned until you approve it.")
        uploaded = st.file_uploader(
            "Choose invoice files",
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="daily_intake_upload",
        )

        with st.expander("Advanced processing settings"):
            model = st.text_input(
                "Processing model",
                value="gpt-5.6",
                key="daily_intake_model",
            )

        if uploaded and st.button(
            "Read invoices",
            type="primary",
            width="stretch",
        ):
            existing_ids = {
                record.get("id") for record in _load_queue(paths["queue"])
            }
            with st.status("Barni is reading the invoices...", expanded=True) as status:
                _render_feed_egg("learning", small=True)
                st.write(f"✓ {len(uploaded)} files uploaded")
                shown_stages: set[str] = set()
                stage_labels = {
                    "reading": "Reading invoice",
                    "supplier": "Understanding supplier",
                    "products": "Learning products",
                }

                def show_stage(stage: str, index: int, total: int, file_name: str) -> None:
                    if stage not in shown_stages:
                        st.write(stage_labels.get(stage, "Invoice processed"))
                        shown_stages.add(stage)
                    st.caption(f"{index} of {total} · {file_name}")

                process_files(uploaded, model, on_stage=show_stage)
                st.write("✓ Invoice reading complete")
                st.caption("Prices and Business Memory update after approval.")
                status.update(
                    label="Invoices are ready for review",
                    state="complete",
                    expanded=False,
                )
            new_records = [
                record
                for record in _load_queue(paths["queue"])
                if record.get("id") not in existing_ids
            ]
            st.session_state["daily_intake_last_summary"] = (
                _processing_summary(new_records)
            )
            st.rerun()

    latest_summary = st.session_state.pop("daily_intake_last_summary", None)
    if latest_summary:
        st.write("")
        _render_processing_summary(latest_summary)

    completion = st.session_state.get("daily_intake_completion")
    if completion:
        st.write("")
        _render_completion(completion)

    queue = _load_queue(paths["queue"])
    active = sorted([
        record for record in queue
        if record.get("queue_status") in {"ready", "review", "error"}
    ], key=_queue_priority)

    st.write("")
    st.markdown("### Review status")
    render_workflow_status(
        invoice_workflow_snapshot(),
        key_prefix="feed_console_workflow",
    )

    if not active:
        st.markdown(
            '<div class="barni-empty-state">No invoices are waiting. Upload a new invoice when you are ready to teach Barni.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = []
    for record in active:
        document = record.get("document", {})
        rows.append({
            "id": record["id"],
            "Needs Review": "Yes" if _needs_review(record) else "No",
            "Confidence": document.get("confidence", 0.0),
            "Supplier": document.get("supplier", "") or "Not identified",
            "Reason": _review_reason(record),
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

    st.write("")
    st.markdown("### Review Queue")
    st.caption("Uncertain invoices stay here until you approve, edit, or reject them.")
    table = pd.DataFrame(rows)
    with st.container(key="feed_queue"):
        st.dataframe(
            _style_review_queue(table.drop(columns=["id"])),
            hide_index=True,
            width="stretch",
            column_order=[
                "Needs Review",
                "Confidence",
                "Supplier",
                "Reason",
                "קובץ",
                "מספר",
                "תאריך",
                "סה״כ",
            ],
            column_config={
                "סה״כ": st.column_config.NumberColumn(format="₪%.2f"),
                "Confidence": st.column_config.NumberColumn(format="%.1%"),
            },
        )

    option_map = {
        f"{row['Needs Review']} · {row['Supplier']} · {row['מספר'] or row['קובץ']}":
        row["id"]
        for row in rows
    }
    selected_label = st.selectbox(
        "Invoice to review",
        options=list(option_map.keys()),
    )
    selected_id = option_map[selected_label]
    record = next(
        record for record in active
        if record["id"] == selected_id
    )

    review_document = {
        **(record.get("document") or {}),
        "source_record_id": selected_id,
    }
    render_barni_thinking(
        think_about_invoice(review_document, review_document.get("items") or []),
        key_prefix=f"queue_review_{selected_id}",
        on_open_evidence=_open_evidence_invoice,
    )

    st.write("")
    with st.expander("Technical confidence details"):
        _render_confidence_summary(record.get("document") or {})

    st.write("")
    left, right = st.columns([1.0, 1.3], gap="large")

    with left:
        st.markdown("#### תצוגה מקדימה")
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
            with st.container(key="feed_error"):
                st.markdown("**Barni could not read this invoice.**")
                st.caption("Review the file or remove it from the queue.")
            with st.expander("Technical details"):
                st.code(record["error"])

    with right:
        st.markdown("#### Edit invoice")
        st.caption("Correct any detail before making a decision.")
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
                    item["queue_status"] = _status_for(updated_document)
                    break
            _save_queue(paths["queue"], queue)
            st.success("Your edits were saved in the review queue.")
            st.rerun()

    st.write("")
    st.markdown("#### Decision")
    duplicate_state = st.session_state.get("daily_intake_duplicate")
    if duplicate_state and duplicate_state.get("record_id") == selected_id:
        existing = duplicate_state["existing"]
        with st.container(key="duplicate_warning"):
            st.markdown("### This invoice already looks familiar.")
            st.write(
                "Barni found the same supplier ID, invoice number, and document type."
            )
            total = existing.get("total")
            total_text = f" · ₪{total:,.2f}" if total is not None else ""
            st.caption(
                f"{existing.get('supplier') or 'Unknown supplier'} · "
                f"Invoice {existing.get('invoice_number') or 'without a number'} · "
                f"{existing.get('invoice_date') or 'Unknown date'}{total_text}"
            )
            replace_col, skip_col, both_col = st.columns(3, gap="medium")
            if replace_col.button("Replace", type="primary", width="stretch"):
                result = _approve_record(record, "replace")
                if result["success"]:
                    st.session_state.pop("daily_intake_duplicate", None)
                    st.rerun()
            if skip_col.button("Skip", width="stretch"):
                result = _approve_record(record, "skip")
                if result["success"]:
                    st.session_state.pop("daily_intake_duplicate", None)
                    st.rerun()
            if both_col.button("Keep both", width="stretch"):
                result = _approve_record(record, "keep_both")
                if result["success"]:
                    st.session_state.pop("daily_intake_duplicate", None)
                    st.rerun()
    else:
        action1, action2 = st.columns(2, gap="medium")
        if action1.button(
            "Approve and teach Barni",
            type="primary",
            width="stretch",
        ):
            result = _approve_record(record)
            if result["outcome"] == "duplicate":
                st.session_state["daily_intake_duplicate"] = {
                    "record_id": selected_id,
                    "existing": result["existing"],
                }
            st.rerun()

        if action2.button("Reject", width="stretch"):
            reject_record(selected_id)
            st.info("Invoice rejected and removed from the active review queue.")
            st.rerun()


def _active_records(record_ids: list[str] | None = None) -> list[dict]:
    queue = _load_queue(_paths()["queue"])
    active = {
        record["id"]: record
        for record in queue
        if record.get("queue_status") in {"ready", "review", "error"}
    }
    if record_ids is None:
        return sorted(active.values(), key=_queue_priority)
    return [active[record_id] for record_id in record_ids if record_id in active]


def _reset_feed_flow() -> None:
    for key in (
        "daily_intake_batch_ids",
        "daily_intake_batch_total",
        "daily_intake_batch_memory_before",
        "daily_intake_batch_learning",
        "daily_intake_duplicate",
        "daily_intake_duplicates_found",
        "daily_intake_flow",
        "daily_intake_hatch_batch_token",
        "daily_intake_hatch_consumed_token",
        "daily_intake_notice",
        "daily_intake_last_search",
        "daily_intake_review_ids",
        "daily_intake_skipped",
        "daily_intake_upload",
    ):
        st.session_state.pop(key, None)


def _begin_review(record_ids: list[str]) -> None:
    records = _active_records(record_ids)
    ordered = sorted(records, key=_queue_priority)
    st.session_state["daily_intake_review_ids"] = [
        record["id"] for record in ordered
    ]
    st.session_state["daily_intake_batch_total"] = len(ordered)
    st.session_state.setdefault(
        "daily_intake_batch_memory_before",
        business_memory_data(),
    )
    st.session_state["daily_intake_flow"] = "review"


def _finish_current_review(record_id: str, message: str | None = None) -> None:
    pending = list(st.session_state.get("daily_intake_review_ids") or [])
    st.session_state["daily_intake_review_ids"] = [
        item for item in pending if item != record_id
    ]
    st.session_state.pop("daily_intake_duplicate", None)
    if message:
        st.session_state["daily_intake_notice"] = message
    if not st.session_state["daily_intake_review_ids"]:
        st.session_state["daily_intake_flow"] = "done"


def _human_confidence(record: dict) -> tuple[str, bool]:
    document = record.get("document") or {}
    issues = set(document.get("machine_issues") or [])
    if not str(document.get("supplier") or "").strip() or "missing_supplier" in issues:
        return "Barni is unsure about this supplier", True
    if _needs_review(record):
        return "Needs attention", True
    return "High confidence", False


def _batch_is_duplicate_only(records: list[dict]) -> bool:
    """Use the existing duplicate lookup to suppress a false learning celebration."""
    successful = [
        record
        for record in records
        if record.get("queue_status") in {"ready", "review"}
    ]
    if not successful:
        return False

    for record in successful:
        document = record.get("document") or {}
        existing = duplicate_invoice(
            document.get("supplier_id", ""),
            document.get("invoice_number", ""),
            document.get("document_type", ""),
        )
        if existing is None:
            return False
    return True


def _render_batch_summary(records: list[dict]) -> None:
    summary = _processing_summary(records)
    attention = summary["review"] + summary["error"]
    with st.container(key="feed_summary"):
        st.markdown(
            "### Your invoices are ready"
            if summary["processed"]
            else "### I need your help with these invoices"
        )
        if summary["processed"]:
            st.write(f"✓ {_count_phrase(summary['processed'], 'invoice')} read")
        if summary["suppliers"]:
            st.write(f"✓ {_count_phrase(summary['suppliers'], 'supplier')} recognized")
        if summary["products"]:
            st.write(f"✓ {_count_phrase(summary['products'], 'product')} found")
        if summary["price_points"]:
            st.write(f"✓ {_count_phrase(summary['price_points'], 'price point')} found")
        if summary["error"]:
            st.write(f"• {_count_phrase(summary['error'], 'invoice')} could not be read")

        st.write("")
        if attention:
            st.markdown(
                f"**{_count_phrase(attention, 'invoice')} "
                f"{'needs' if attention == 1 else 'need'} your attention.**"
            )
        else:
            st.markdown("**Everything looks good.**")
        st.caption("Nothing enters Business Memory until you approve it.")


def _approve_ready_batch(records: list[dict]) -> None:
    pending_ids = [record["id"] for record in records]
    for record in records:
        result = _approve_record(record)
        if result["outcome"] == "duplicate":
            st.session_state["daily_intake_duplicates_found"] = (
                int(st.session_state.get("daily_intake_duplicates_found") or 0) + 1
            )
            st.session_state["daily_intake_duplicate"] = {
                "record_id": record["id"],
                "existing": result["existing"],
            }
            _begin_review(pending_ids[pending_ids.index(record["id"]):])
            return
        if not result["success"]:
            _begin_review(pending_ids[pending_ids.index(record["id"]):])
            return
    st.session_state["daily_intake_review_ids"] = []
    st.session_state["daily_intake_flow"] = "done"


def _records_requiring_review(records: list[dict]) -> list[str]:
    return [record["id"] for record in records if _needs_review(record)]


def _approve_clear_and_review_attention(records: list[dict]) -> None:
    """Approve the clear records and review only records that need a decision."""
    attention_ids = _records_requiring_review(records)
    for index, record in enumerate(records):
        if _needs_review(record):
            continue
        result = _approve_record(record)
        if result["outcome"] == "duplicate":
            st.session_state["daily_intake_duplicates_found"] = (
                int(st.session_state.get("daily_intake_duplicates_found") or 0) + 1
            )
            st.session_state["daily_intake_duplicate"] = {
                "record_id": record["id"],
                "existing": result["existing"],
            }
            attention_ids = [
                record["id"],
                *attention_ids,
                *[
                    pending["id"]
                    for pending in records[index + 1:]
                    if not _needs_review(pending)
                ],
            ]
            break
        if not result["success"]:
            attention_ids = [
                record["id"],
                *attention_ids,
                *[
                    pending["id"]
                    for pending in records[index + 1:]
                    if not _needs_review(pending)
                ],
            ]
            break

    if attention_ids:
        _begin_review(list(dict.fromkeys(attention_ids)))
    else:
        st.session_state["daily_intake_review_ids"] = []
        st.session_state["daily_intake_flow"] = "done"


def _render_upload_step() -> None:
    selected_files = st.session_state.get("daily_intake_upload") or []
    with st.container(key="feed_intro"):
        _render_feed_egg("awake" if selected_files else "calm")
        st.markdown("## Feed Barni")
        st.caption("Every invoice makes Barni smarter.")

    paths = _paths()
    active = _active_records()
    if active:
        attention = [record for record in active if _needs_review(record)]
        with st.container(key="feed_review_header"):
            st.markdown("### Finish what you started")
            waiting = len(attention) or len(active)
            st.write(
                f"{_count_phrase(waiting, 'invoice')} still "
                f"{'needs' if waiting == 1 else 'need'} your decision."
            )
            if st.button(
                "Continue review",
                type="primary",
                width="stretch",
                key="feed_continue_review",
            ):
                _begin_review([
                    record["id"] for record in (attention or active)
                ])
                st.rerun()
        st.caption("Continue this review now, or add another invoice below.")

    st.write("")
    st.markdown("### Since you last checked")
    st.caption("The latest changes supported by approved invoices and Business Memory")
    cursor = FeedJournalCursor()
    journal_since = st.session_state.setdefault(
        "feed_journal_since",
        cursor.previous_visit(),
    )
    try:
        journal = BusinessStoryEngine().generate_feed(
            StoryContext(since=journal_since),
            max_stories=5,
        )
    except Exception as exc:
        log_runtime_error("Feed Barni journal", exc)
        st.caption(
            "I couldn't prepare the latest business story. Your invoices are safe, "
            "and you can still feed Barni below."
        )
    else:
        for index, story in enumerate(journal):
            render_business_story(
                story,
                key=f"feed_journal_{index}",
                show_evidence=True,
            )
        if not st.session_state.get("feed_journal_visit_recorded"):
            try:
                cursor.mark_visited()
            except OSError as exc:
                log_runtime_error("Feed Barni visit cursor", exc)
            else:
                st.session_state["feed_journal_visit_recorded"] = True

    st.write("")
    st.markdown("### Feed today's invoices")
    with st.container(key="feed_upload"):
        uploaded = st.file_uploader(
            "Drop invoices here",
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="daily_intake_upload",
        )

        with st.expander("Advanced settings"):
            model = st.text_input(
                "Processing model",
                value="gpt-5.6",
                key="daily_intake_model",
            )
        if uploaded and st.button(
            "Read invoices",
            type="primary",
            width="stretch",
            key="feed_read_invoices",
        ):
            st.session_state["daily_intake_batch_memory_before"] = business_memory_data()
            st.session_state["daily_intake_batch_learning"] = []
            st.session_state.pop("daily_intake_last_search", None)
            st.session_state["daily_intake_flow"] = "processing"
            st.rerun()


def _render_processing_step() -> None:
    uploaded = st.session_state.get("daily_intake_upload") or []
    if not uploaded:
        st.session_state["daily_intake_flow"] = "upload"
        st.rerun()

    paths = _paths()
    existing_ids = {record.get("id") for record in _load_queue(paths["queue"])}
    with st.container(key="feed_intro"):
        _render_feed_egg("learning")
        st.markdown("## Barni is learning")
        st.caption("You can leave the details to Barni.")

    with st.status("Reading your invoices...", expanded=True) as status:
        progress = st.progress(0.0, text=f"0 of {len(uploaded)} invoices complete")
        current_file = st.empty()
        stage_labels = {
            "reading": "Reading invoices",
            "supplier": "Recognizing suppliers",
            "products": "Learning products",
            "complete": "Invoice ready",
        }

        def show_stage(stage: str, index: int, total: int, file_name: str) -> None:
            completed = index if stage == "complete" else index - 1
            progress.progress(
                completed / total,
                text=f"{completed} of {total} invoices complete",
            )
            current_file.caption(f"{stage_labels[stage]} · {file_name}")

        process_files(
            uploaded,
            st.session_state.get("daily_intake_model", "gpt-5.6"),
            on_stage=show_stage,
        )
        st.write("Checking prices")
        st.write("Business memory is ready to update after approval")
        status.update(
            label="Ready for your approval",
            state="complete",
            expanded=False,
        )

    batch_ids = [
        record["id"]
        for record in _load_queue(paths["queue"])
        if record.get("id") not in existing_ids
    ]
    st.session_state["daily_intake_batch_ids"] = batch_ids
    st.session_state["daily_intake_batch_total"] = len(batch_ids)
    st.session_state["daily_intake_skipped"] = 0
    st.session_state["daily_intake_duplicates_found"] = 0
    batch_records = _active_records(batch_ids)
    summary = _processing_summary(batch_records)
    batch_token = "|".join(batch_ids)
    st.session_state["daily_intake_hatch_batch_token"] = batch_token
    st.session_state.pop("daily_intake_hatch_consumed_token", None)
    st.session_state["daily_intake_flow"] = (
        "hatch"
        if summary["processed"] and not _batch_is_duplicate_only(batch_records)
        else "result"
    )
    st.rerun()


def _render_hatch_step() -> None:
    batch_token = st.session_state.get("daily_intake_hatch_batch_token")
    if (
        not batch_token
        or st.session_state.get("daily_intake_hatch_consumed_token") == batch_token
    ):
        st.session_state["daily_intake_flow"] = "result"
        st.rerun()

    # Consume before rendering so browser refreshes cannot replay this batch.
    st.session_state["daily_intake_hatch_consumed_token"] = batch_token
    _render_hatch_moment()
    time.sleep(2.35)
    st.session_state["daily_intake_flow"] = "result"
    st.rerun()


def _render_result_step() -> None:
    batch_ids = list(st.session_state.get("daily_intake_batch_ids") or [])
    records = _active_records(batch_ids)
    _render_batch_summary(records)
    attention = [record for record in records if _needs_review(record)]

    if not records:
        st.info("No invoices were prepared. Try another file when you are ready.")
        if st.button("Back to upload", type="primary"):
            _reset_feed_flow()
            st.rerun()
        return

    if attention:
        clear_count = len(records) - len(attention)
        label = (
            f"Approve {clear_count} clear and review {len(attention)}"
            if clear_count
            else f"Review {_count_phrase(len(attention), 'invoice')}"
        )
        if st.button(label, type="primary", width="stretch"):
            _approve_clear_and_review_attention(records)
            st.rerun()
    elif st.button("Approve & Teach Barni", type="primary", width="stretch"):
        _approve_ready_batch(records)
        st.rerun()


def _render_preview(record: dict) -> None:
    source = Path(record.get("stored_file") or "")
    with st.container(key="feed_review_panel"):
        st.markdown("#### Original invoice")
        if source.exists() and source.suffix.lower() == ".pdf":
            st.download_button(
                "Open invoice PDF",
                data=source.read_bytes(),
                file_name=record.get("file_name") or source.name,
                mime="application/pdf",
                width="stretch",
            )
            st.caption("Open the PDF beside Barni to compare the extracted details.")
        elif source.exists():
            st.image(str(source), width="stretch")
        else:
            st.caption("The original file is unavailable, but the extracted details remain.")


def _render_duplicate_decision(record: dict, duplicate_state: dict) -> None:
    existing = duplicate_state["existing"]
    with st.container(key="duplicate_warning"):
        st.markdown("### This invoice already looks familiar.")
        st.write("Barni found the same supplier ID, invoice number, and document type.")
        total = existing.get("total")
        total_text = f" · ₪{total:,.2f}" if total is not None else ""
        st.caption(
            f"{existing.get('supplier') or 'Unknown supplier'} · "
            f"Invoice {existing.get('invoice_number') or 'without a number'}{total_text}"
        )
        replace_col, keep_col = st.columns(2, gap="medium")
        if replace_col.button("Replace", type="primary", width="stretch"):
            result = _approve_record(record, "replace")
            if result["success"]:
                _finish_current_review(record["id"], "Barni remembers it.")
                st.rerun()
        if keep_col.button("Keep both", width="stretch"):
            result = _approve_record(record, "keep_both")
            if result["success"]:
                _finish_current_review(record["id"], "Barni remembers it.")
                st.rerun()
        if st.button("Skip duplicate", key="feed_skip_duplicate"):
            result = _approve_record(record, "skip")
            if result["success"]:
                _finish_current_review(record["id"])
                st.rerun()


def _render_review_step() -> None:
    pending_ids = list(st.session_state.get("daily_intake_review_ids") or [])
    records = _active_records(pending_ids)
    if not records:
        st.session_state["daily_intake_flow"] = "done"
        st.rerun()

    record = records[0]
    record_id = record["id"]
    total = int(st.session_state.get("daily_intake_batch_total") or len(records))
    position = max(1, total - len(records) + 1)
    notice = st.session_state.pop("daily_intake_notice", None)
    if notice:
        st.success(notice)

    if record.get("queue_status") == "error":
        with st.container(key="feed_error"):
            st.markdown("### I couldn't read this invoice.")
            st.write(_document_recovery_message(
                Path(record.get("stored_file") or "invoice")
            ))
            source = Path(record.get("stored_file") or "")
            if source.exists():
                st.caption(
                    "Barni kept the file in Review. Complete the details below, "
                    "or skip it and upload a clearer copy."
                )
            else:
                st.caption(
                    "The upload could not be stored. Skip this invoice, then upload "
                    "the original file again."
                )

    with st.container(key="feed_review_header"):
        st.caption(f"Invoice {position} of {total}")
        st.markdown(
            f"### {(record.get('document') or {}).get('supplier') or 'Review this invoice'}"
        )
        review_document = {
            **(record.get("document") or {}),
            "source_record_id": record_id,
        }
        render_barni_thinking(
            think_about_invoice(review_document, review_document.get("items") or []),
            key_prefix=f"feed_review_{record_id}",
            on_open_evidence=_open_evidence_invoice,
        )

    left, right = st.columns([0.9, 1.25], gap="large")
    with left:
        _render_preview(record)
    with right:
        updated_document, _, saved = document_review_form(
            record,
            form_key=f"review_{record_id}",
            compact=True,
        )
        if saved:
            queue = _load_queue(_paths()["queue"])
            for item in queue:
                if item["id"] == record_id:
                    item["document"] = updated_document
                    item["queue_status"] = _status_for(updated_document)
                    break
            _save_queue(_paths()["queue"], queue)
            st.session_state["daily_intake_notice"] = "Changes saved."
            st.rerun()

    with st.expander("Technical confidence details"):
        _render_confidence_summary(record.get("document") or {})

    duplicate_state = st.session_state.get("daily_intake_duplicate")
    if duplicate_state and duplicate_state.get("record_id") == record_id:
        _render_duplicate_decision(record, duplicate_state)
        return

    blockers = _approval_blockers(record.get("document") or {})
    if blockers:
        st.warning(
            "I need " + ", ".join(blockers) +
            " before this invoice can safely enter Business Memory."
        )
        st.caption("Add the missing details above and save your changes, or skip this invoice for now.")

    approve_col, skip_col = st.columns([1.4, 1], gap="medium")
    if approve_col.button(
        "Approve & Teach Barni",
        type="primary",
        width="stretch",
        key=f"feed_approve_{record_id}",
        disabled=bool(blockers),
    ):
        result = _approve_record(record)
        if result["outcome"] == "duplicate":
            st.session_state["daily_intake_duplicates_found"] = (
                int(st.session_state.get("daily_intake_duplicates_found") or 0) + 1
            )
            st.session_state["daily_intake_duplicate"] = {
                "record_id": record_id,
                "existing": result["existing"],
            }
        elif result["success"]:
            _finish_current_review(record_id, "Barni remembers it.")
        st.rerun()

    if skip_col.button("Skip for now", width="stretch", key=f"feed_skip_{record_id}"):
        st.session_state["daily_intake_skipped"] = (
            int(st.session_state.get("daily_intake_skipped") or 0) + 1
        )
        _finish_current_review(record_id)
        st.rerun()

    with st.expander("More actions"):
        st.caption("Reject removes this invoice from the active review flow.")
        if st.button("Reject invoice", key=f"feed_reject_{record_id}"):
            reject_record(record_id)
            _finish_current_review(record_id)
            st.rerun()


def _render_done_step() -> None:
    before = st.session_state.get("daily_intake_batch_memory_before")
    delta = _memory_delta(before, business_memory_data()) if before else None
    skipped = int(st.session_state.get("daily_intake_skipped") or 0)
    duplicates = int(st.session_state.get("daily_intake_duplicates_found") or 0)
    with st.container(key="feed_done"):
        st.markdown("## All done.")
        st.write("Everything that needed attention has been reviewed.")
        if delta and any(delta.values()):
            if delta["invoices"]:
                st.write(f"✓ {_count_phrase(delta['invoices'], 'invoice')} learned")
            if delta["suppliers"]:
                st.write(f"✓ {_count_phrase(delta['suppliers'], 'supplier')} learned")
            if delta["products"]:
                st.write(f"✓ {_count_phrase(delta['products'], 'product')} learned")
            if delta["price_points"]:
                st.write(f"✓ {_count_phrase(delta['price_points'], 'price point')} added")
        else:
            st.write("Business Memory is up to date.")
        if skipped:
            st.caption(f"{_count_phrase(skipped, 'invoice')} left for later review.")
        if duplicates:
            st.caption(f"{_count_phrase(duplicates, 'duplicate')} found and resolved.")

        learning_stories = list(
            st.session_state.get("daily_intake_batch_learning") or []
        )
        for index, story in enumerate(learning_stories[-3:]):
            render_business_story(
                story,
                key=f"feed_batch_learning_{index}",
                show_evidence=True,
            )

    view_col, memory_col, another_col = st.columns([1.25, 1, 1], gap="medium")
    if view_col.button(
        "Find it in Search",
        type="primary",
        width="stretch",
    ):
        _view_what_barni_learned()
        st.rerun()
    if memory_col.button(
        "Open Business Memory",
        width="stretch",
        on_click=_open_business_memory,
    ):
        st.rerun()
    if another_col.button("Feed another invoice", width="stretch"):
        _reset_feed_flow()
        st.rerun()


def render_daily_intake():
    _render_feed_styles()
    recovery = st.session_state.pop("daily_intake_recovery", None)
    if recovery:
        st.error(recovery)
    flow = st.session_state.get("daily_intake_flow", "upload")
    if flow == "processing":
        _render_processing_step()
    elif flow == "hatch":
        _render_hatch_step()
    elif flow == "result":
        _render_result_step()
    elif flow == "review":
        _render_review_step()
    elif flow == "done":
        _render_done_step()
    else:
        _render_upload_step()
