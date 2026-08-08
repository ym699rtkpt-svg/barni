from __future__ import annotations

import json
import platform
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


APP_VERSION = "Alpha 0.3"


def _pilot_dir() -> Path:
    path = Path.home() / "restaurant-invoices" / "pilot"
    path.mkdir(parents=True, exist_ok=True)
    return path


def feedback_path() -> Path:
    return _pilot_dir() / "feedback.jsonl"


def runtime_log_path() -> Path:
    return _pilot_dir() / "runtime-errors.jsonl"


def pilot_event_path() -> Path:
    return _pilot_dir() / "events.jsonl"


def _append_json_line(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def save_feedback(
    feedback_type: str,
    message: str,
    current_page: str,
    contact: str = "",
    *,
    path: Path | None = None,
) -> None:
    clean_message = message.strip()
    if not clean_message:
        raise ValueError("Please describe what happened or what could be improved.")
    _append_json_line(
        path or feedback_path(),
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "type": feedback_type,
            "message": clean_message,
            "page": current_page,
            "contact": contact.strip(),
            "version": APP_VERSION,
        },
    )


def log_runtime_error(
    page: str,
    error: BaseException,
    *,
    path: Path | None = None,
) -> None:
    """Log operational metadata without serializing invoices or session state."""
    try:
        _append_json_line(
            path or runtime_log_path(),
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "page": page,
                "error_type": type(error).__name__,
                "message": str(error)[:1000],
                "traceback": traceback.format_exc()[-6000:],
                "version": APP_VERSION,
            },
        )
    except Exception:
        # Error reporting must never cause a second application failure.
        pass


def log_pilot_event(
    event_type: str,
    *,
    metadata: dict[str, Any] | None = None,
    path: Path | None = None,
) -> None:
    """Record non-sensitive pilot telemetry without changing business behavior."""
    try:
        _append_json_line(
            path or pilot_event_path(),
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "event_type": event_type,
                "metadata": metadata or {},
                "version": APP_VERSION,
            },
        )
    except Exception:
        pass


def _recent_errors(path: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _queue_records(path: Path | None = None) -> list[dict[str, Any]]:
    queue_path = path or (
        Path.home() / "restaurant-invoices" / "daily-intake" / "queue.json"
    )
    if not queue_path.exists():
        return []
    try:
        data = json.loads(queue_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _confidence_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    distribution = {
        "Below 60%": 0,
        "60–79%": 0,
        "80–89%": 0,
        "90% and above": 0,
        "Unavailable": 0,
    }
    for record in records:
        document = record.get("document") or {}
        raw_value = document.get("confidence")
        try:
            confidence = float(raw_value)
        except (TypeError, ValueError):
            distribution["Unavailable"] += 1
            continue
        if not 0.0 <= confidence <= 1.0:
            distribution["Unavailable"] += 1
        elif confidence < 0.60:
            distribution["Below 60%"] += 1
        elif confidence < 0.80:
            distribution["60–79%"] += 1
        elif confidence < 0.90:
            distribution["80–89%"] += 1
        else:
            distribution["90% and above"] += 1
    return distribution


def pilot_dashboard_data(
    *,
    queue_path: Path | None = None,
    error_path: Path | None = None,
    event_path: Path | None = None,
) -> dict[str, Any]:
    """Build read-only pilot metrics from existing queue, memory, and health services."""
    from database import control_center_data, database_health
    from services.business_memory import business_memory_data

    records = _queue_records(queue_path)
    statuses = [str(record.get("queue_status") or "") for record in records]
    successfully_processed = sum(
        bool(record.get("document")) and status != "error"
        for record, status in zip(records, statuses)
    )
    events = _json_lines(event_path or pilot_event_path())
    duplicate_detections = sum(
        event.get("event_type") == "duplicate_detected" for event in events
    )
    memory = business_memory_data()
    database_status = database_health()
    control = control_center_data()
    errors = _recent_errors(error_path or runtime_log_path(), limit=10)

    failed = statuses.count("error")
    needs_review = statuses.count("review")
    system_healthy = bool(database_status.get("healthy")) and not errors
    data_needs_attention = bool(failed or needs_review)

    return {
        "uploaded_invoices": len(records),
        "successfully_processed": successfully_processed,
        "failed_invoices": failed,
        "needs_review": needs_review,
        "new_suppliers_learned": memory["supplier_count"],
        "new_products_learned": memory["product_count"],
        "new_price_points": memory["price_point_count"],
        "duplicate_invoices_detected": duplicate_detections,
        "stored_duplicate_groups": control["duplicates"],
        "confidence_distribution": _confidence_distribution(records),
        "recent_errors": errors,
        "health": {
            "system": "Healthy" if system_healthy else "Needs attention",
            "data_quality": (
                "Needs attention" if data_needs_attention else "No open issues"
            ),
            "business_memory": (
                "Growing" if memory["invoice_count"] else "Waiting for first invoice"
            ),
            "database_healthy": bool(database_status.get("healthy")),
            "schema_version": database_status.get("schema_version"),
            "invoice_count": memory["invoice_count"],
            "price_history_coverage": (
                f"{memory['covered_product_count']:,} / {memory['product_count']:,}"
            ),
        },
    }


def debug_information(*, error_path: Path | None = None) -> dict[str, Any]:
    database_status: dict[str, Any]
    try:
        from database import database_health

        health = database_health()
        database_status = {
            "healthy": health.get("healthy"),
            "schema_version": health.get("schema_version"),
            "invoice_count": health.get("invoice_count"),
            "missing_required_columns": health.get("missing_required_columns", []),
        }
    except Exception as exc:
        database_status = {
            "healthy": False,
            "health_check_error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "barni_version": APP_VERSION,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "database": database_status,
        "recent_runtime_errors": _recent_errors(error_path or runtime_log_path()),
        "privacy_note": "Invoice contents, uploaded files, and credentials are excluded.",
    }


def debug_export_bytes(*, error_path: Path | None = None) -> bytes:
    return json.dumps(
        debug_information(error_path=error_path),
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
