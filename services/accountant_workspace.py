from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from database import dashboard_data, search_invoices
from services.invoice_workflow import (
    AccountingReadiness,
    build_undated_queue_snapshot,
    build_workflow_snapshot,
    database_record_lifecycle,
    load_queue_records,
)


def available_accounting_months() -> list[str]:
    documents = dashboard_data()["documents"]
    if documents.empty or "invoice_date" not in documents.columns:
        return [pd.Timestamp.now().strftime("%Y-%m")]
    dates = pd.to_datetime(documents["invoice_date"], errors="coerce").dropna()
    months = sorted(dates.dt.strftime("%Y-%m").unique(), reverse=True)
    return months or [pd.Timestamp.now().strftime("%Y-%m")]


def accountant_month_status(
    month: str,
    *,
    queue_path: Path | None = None,
) -> dict[str, Any]:
    all_documents = search_invoices(statuses=[]).copy()
    documents = search_invoices(
        start_date=f"{month}-01",
        end_date=f"{month}-31",
        statuses=["approved"],
        min_total=None,
        max_total=None,
    ).copy()
    queue_records = load_queue_records(queue_path)
    workflow = build_workflow_snapshot(
        all_documents,
        queue_records,
        month=month,
    )
    undated_workflow = build_undated_queue_snapshot(all_documents, queue_records)

    if documents.empty:
        missing_source = pd.Series(dtype=bool)
        missing_supplier = pd.Series(dtype=bool)
        ready_mask = pd.Series(dtype=bool)
    else:
        missing_source = documents["archived_path"].apply(
            lambda value: not bool(value) or not Path(str(value)).exists()
        )
        missing_supplier = (
            documents["supplier"].fillna("").astype(str).str.strip() == ""
        )
        ready_mask = documents.apply(
            lambda row: database_record_lifecycle(row.to_dict()).accounting_readiness
            == AccountingReadiness.READY,
            axis=1,
        )

    needs_review = (
        workflow.pending_review + workflow.learning + workflow.needs_attention
    )
    issues = []
    if workflow.duplicate:
        issues.append(f"{workflow.duplicate} duplicate invoice(s) need attention.")
    missing_supplier_count = int(missing_supplier.sum())
    if missing_supplier_count:
        issues.append(f"{missing_supplier_count} invoice(s) are missing supplier names.")
    if needs_review:
        issues.append(f"{needs_review} invoice(s) are awaiting review.")
    if undated_workflow.open_count:
        issues.append(
            f"{undated_workflow.open_count} open invoice(s) have no date, "
            "so their accounting month cannot be confirmed."
        )
    missing_source_count = int(missing_source.sum())
    if missing_source_count:
        issues.append(f"{missing_source_count} approved invoice source file(s) are missing.")

    total = (
        float(pd.to_numeric(documents["total"], errors="coerce").fillna(0).sum())
        if not documents.empty
        else 0.0
    )
    return {
        "month": month,
        "documents": documents,
        "uploaded": int(len(documents) + workflow.open_count),
        "missing": missing_source_count,
        "duplicate": workflow.duplicate,
        "needs_review": needs_review,
        "ready": int(ready_mask.sum()),
        "missing_supplier_names": missing_supplier_count,
        "total": total,
        "issues": issues,
        "ready_for_accountant": bool(len(documents)) and not issues,
        "workflow": workflow,
        "undated_workflow": undated_workflow,
    }


def _summary_pdf(status: dict[str, Any]) -> bytes:
    lines = [
        "Barni Accountant Summary",
        f"Month: {status['month']}",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Stored invoices: {len(status['documents'])}",
        f"Ready invoices: {status['ready']}",
        f"Missing source files: {status['missing']}",
        f"Duplicate groups: {status['duplicate']}",
        f"Awaiting review: {status['needs_review']}",
        f"Missing supplier names: {status['missing_supplier_names']}",
        f"Invoice total (ILS): {status['total']:,.2f}",
        "Ready for accountant: " + ("Yes" if status["ready_for_accountant"] else "No"),
    ]
    if status["issues"]:
        lines.append("Items requiring attention:")
        lines.extend(f"- {issue}" for issue in status["issues"])

    def escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    commands = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        commands.append(f"({escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def build_accountant_package(status: dict[str, Any]) -> bytes:
    documents = status["documents"].copy()
    summary_columns = [
        "invoice_date", "supplier", "supplier_id", "invoice_number",
        "document_type", "taxable_amount", "exempt_amount", "vat", "total",
        "currency", "status", "file_name",
    ]
    for column in summary_columns:
        if column not in documents.columns:
            documents[column] = None

    generated_at = datetime.now().isoformat(timespec="seconds")
    included_files = []
    missing_files = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "summary.csv",
            documents[summary_columns].to_csv(index=False, encoding="utf-8-sig"),
        )
        archive.writestr("summary.pdf", _summary_pdf(status))

        for _, invoice in documents.iterrows():
            source = Path(str(invoice.get("archived_path") or ""))
            if source.exists() and source.is_file():
                archive_name = f"invoices/{int(invoice['id'])}_{source.name}"
                archive.write(source, arcname=archive_name)
                included_files.append(archive_name)
            else:
                missing_files.append(int(invoice["id"]))

        metadata = {
            "package_version": 1,
            "generated_at": generated_at,
            "month": status["month"],
            "currency": "ILS",
            "invoice_count": int(len(documents)),
            "invoice_total": status["total"],
            "ready_for_accountant": status["ready_for_accountant"],
            "status": {
                "uploaded": status["uploaded"],
                "missing": status["missing"],
                "duplicate_groups": status["duplicate"],
                "needs_review": status["needs_review"],
                "ready": status["ready"],
                "missing_supplier_names": status["missing_supplier_names"],
            },
            "issues": status["issues"],
            "included_invoice_files": included_files,
            "missing_source_invoice_ids": missing_files,
            "delivery": "Generated locally. Not emailed or transmitted by Barni.",
        }
        archive.writestr(
            "metadata.json",
            json.dumps(metadata, ensure_ascii=False, indent=2),
        )
    return buffer.getvalue()
