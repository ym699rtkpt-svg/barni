
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from hybrid_engine import extract_hybrid


SUPPORTED = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def native_text(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return ""

    command = "/opt/homebrew/bin/pdftotext"
    if not Path(command).exists():
        command = "pdftotext"

    with tempfile.NamedTemporaryFile(suffix=".txt") as temp:
        subprocess.run(
            [command, "-layout", str(path), temp.name],
            check=False,
            timeout=20,
        )
        return Path(temp.name).read_text(encoding="utf-8", errors="ignore")


def discover(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED
        and "__MACOSX" not in path.parts
        and not path.name.startswith("._")
    )


def _text(value) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    if value.endswith(".0") and value[:-2].isdigit():
        value = value[:-2]
    return value


def run(root: Path, output: Path, limit: int | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    details = output / "documents"
    details.mkdir(exist_ok=True)

    files = discover(root)
    if limit:
        files = files[:limit]

    records = []

    for index, path in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] {path.name}")
        record = {
            "file_name": path.name,
            "relative_path": str(path.relative_to(root)),
            "status": "error",
            "method": "",
            "error": "",
        }

        try:
            text = native_text(path)
            document, method = extract_hybrid(
                path,
                raw_text=text,
                source_text_method="local_pdf_text" if text else "",
                use_ai=True,
                ai_model=os.environ.get("INVOICE_AI_MODEL", "gpt-5.6"),
            )

            machine_issues = document.get("machine_issues", [])
            model_notes = document.get("model_notes", [])

            record.update({
                "status": document.get("status", "review"),
                "method": method,
                "document_type": _text(document.get("document_type")),
                "supplier": _text(document.get("supplier")),
                "supplier_id": _text(document.get("supplier_id")),
                "invoice_number": _text(document.get("invoice_number")),
                "invoice_date": _text(document.get("invoice_date")),
                "due_date": _text(document.get("due_date")),
                "statement_month": _text(document.get("statement_month")),
                "subtotal": document.get("subtotal"),
                "taxable_amount": document.get("taxable_amount"),
                "exempt_amount": document.get("exempt_amount"),
                "vat_rate": document.get("vat_rate"),
                "vat": document.get("vat"),
                "total": document.get("total"),
                "tax_treatment": document.get("tax_treatment", "לא ברור"),
                "items_count": len(document.get("items", [])),
                "confidence": document.get("confidence", 0.0),
                "machine_issues": machine_issues,
                "model_notes": model_notes,
                "warnings": machine_issues + model_notes,
            })

            (details / f"{index:03d}.json").write_text(
                json.dumps(
                    {"record": record, "document": document},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            record["error"] = str(exc)

        records.append(record)

        (output / "report.partial.json").write_text(
            json.dumps({"documents": records}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    status_counts = Counter(record["status"] for record in records)
    method_counts = Counter(record.get("method", "") for record in records)
    issue_counts = Counter(
        issue
        for record in records
        for issue in record.get("machine_issues", [])
    )

    summary = {
        "files_tested": len(records),
        "status_counts": dict(status_counts),
        "method_counts": dict(method_counts),
        "machine_issue_counts": dict(issue_counts),
        "documents_with_items": sum(
            1 for record in records if record.get("items_count", 0) > 0
        ),
        "average_confidence": round(
            sum(record.get("confidence", 0.0) for record in records)
            / len(records),
            3,
        ) if records else 0.0,
    }

    result = {"summary": summary, "documents": records}
    (output / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    columns = [
        "file_name", "relative_path", "status", "method",
        "document_type", "supplier", "supplier_id", "invoice_number",
        "invoice_date", "due_date", "statement_month",
        "subtotal", "taxable_amount", "exempt_amount",
        "vat_rate", "vat", "total", "tax_treatment", "items_count",
        "confidence", "machine_issues", "model_notes", "error",
    ]

    with (output / "report.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()

        for record in records:
            row = dict(record)
            row["machine_issues"] = " | ".join(
                record.get("machine_issues", [])
            )
            row["model_notes"] = " | ".join(
                record.get("model_notes", [])
            )

            # CSV is a convenience view. JSON remains the canonical typed result.
            writer.writerow({
                key: row.get(key, "")
                for key in columns
            })

    print("\n========== AI Batch Report v09.1 ==========")
    print(f"מסמכים: {summary['files_tested']}")
    print(f"עברו: {status_counts.get('pass', 0)}")
    print(f"לבדיקה: {status_counts.get('review', 0)}")
    print(f"שגיאות: {status_counts.get('error', 0)}")
    print(f"עם שורות מוצרים: {summary['documents_with_items']}")
    print(f"ביטחון ממוצע: {summary['average_confidence']}")
    print(f"דוח: {output}")

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument(
        "--output",
        default=str(Path.home() / "restaurant-invoices" / "ai-results"),
    )
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    run(
        Path(args.dataset).expanduser().resolve(),
        Path(args.output).expanduser().resolve(),
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
