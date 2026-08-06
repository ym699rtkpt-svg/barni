
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

from parser_engine import parse_invoice, extract_items

SUPPORTED_PDF = {".pdf"}
SUPPORTED_IMAGE = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}

def find_command(name: str) -> str:
    for candidate in (
        shutil.which(name),
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"לא נמצאה הפקודה {name}")

def run_command(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

def extract_pdf_text_fast(path: Path) -> tuple[str, str]:
    pdftotext = find_command("pdftotext")
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp:
        result = run_command(
            [pdftotext, "-layout", str(path), temp.name],
            timeout=12,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "pdftotext failed")
        text = Path(temp.name).read_text(encoding="utf-8", errors="ignore")

    if len("".join(text.split())) >= 40:
        return text, "pdf_text"

    return "", "needs_ocr"

def extract_image_fast(path: Path) -> tuple[str, str]:
    return "", "needs_ocr"

def extract_text_fast(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_PDF:
        return extract_pdf_text_fast(path)
    if suffix in SUPPORTED_IMAGE:
        return extract_image_fast(path)
    raise ValueError(f"סוג קובץ לא נתמך: {suffix}")

def safe_number(value):
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None

def validate(parsed: dict, items: list[dict], method: str) -> dict:
    issues = []

    if method == "needs_ocr":
        issues.append("needs_ocr")

    if not parsed.get("document_type") or parsed.get("document_type") == "אחר":
        issues.append("unknown_document_type")
    if not parsed.get("supplier"):
        issues.append("missing_supplier")
    if not parsed.get("supplier_id"):
        issues.append("missing_supplier_id")
    if not parsed.get("invoice_number"):
        issues.append("missing_invoice_number")
    if not parsed.get("invoice_date"):
        issues.append("missing_invoice_date")

    subtotal = safe_number(parsed.get("subtotal"))
    vat = safe_number(parsed.get("vat"))
    total = safe_number(parsed.get("total"))

    if subtotal is None:
        issues.append("missing_subtotal")
    if vat is None:
        issues.append("missing_vat")
    if total is None:
        issues.append("missing_total")
    if subtotal is not None and vat is not None and total is not None:
        if abs((subtotal + vat) - total) > 0.05:
            issues.append("amount_mismatch")
    if not items:
        issues.append("missing_line_items")

    fields = [
        parsed.get("document_type") not in ("", None, "אחר"),
        bool(parsed.get("supplier")),
        bool(parsed.get("supplier_id")),
        bool(parsed.get("invoice_number")),
        bool(parsed.get("invoice_date")),
        subtotal is not None,
        vat is not None,
        total is not None,
    ]
    completeness = round(100 * sum(fields) / len(fields), 1)

    if method == "needs_ocr":
        status = "ocr_queue"
    elif not issues:
        status = "pass"
    elif completeness >= 75 and "amount_mismatch" not in issues:
        status = "review"
    else:
        status = "fail"

    return {
        "status": status,
        "issues": issues,
        "completeness_percent": completeness,
    }

def discover_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "__MACOSX" in path.parts or path.name.startswith("._"):
            continue
        if path.suffix.lower() in SUPPORTED_PDF | SUPPORTED_IMAGE:
            files.append(path)
    return sorted(files, key=lambda x: str(x).lower())

def detail_name(path: Path) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:10]
    return f"{path.stem[:60]}_{digest}.json"

def analyze(path: Path, root: Path, detail_dir: Path) -> dict:
    record = {
        "file_name": path.name,
        "relative_path": str(path.relative_to(root)),
        "extension": path.suffix.lower(),
        "status": "error",
        "extraction_method": "",
        "document_type": "",
        "supplier": "",
        "supplier_id": "",
        "invoice_number": "",
        "invoice_date": "",
        "due_date": "",
        "subtotal": None,
        "vat": None,
        "total": None,
        "line_items_count": 0,
        "completeness_percent": 0.0,
        "issues": [],
        "error": "",
        "detail_file": "",
    }

    try:
        text, method = extract_text_fast(path)
        record["extraction_method"] = method

        if method == "needs_ocr":
            parsed = {
                "document_type": "",
                "supplier": "",
                "supplier_id": "",
                "invoice_number": "",
                "invoice_date": "",
                "due_date": "",
                "subtotal": None,
                "vat": None,
                "total": None,
            }
            items = []
        else:
            parsed = parse_invoice(text)
            items = extract_items(text)

        check = validate(parsed, items, method)

        record.update({
            "status": check["status"],
            "issues": check["issues"],
            "completeness_percent": check["completeness_percent"],
            "document_type": parsed.get("document_type", ""),
            "supplier": parsed.get("supplier", ""),
            "supplier_id": parsed.get("supplier_id", ""),
            "invoice_number": parsed.get("invoice_number", ""),
            "invoice_date": parsed.get("invoice_date", ""),
            "due_date": parsed.get("due_date", ""),
            "subtotal": safe_number(parsed.get("subtotal")),
            "vat": safe_number(parsed.get("vat")),
            "total": safe_number(parsed.get("total")),
            "line_items_count": len(items),
        })

        detail_path = detail_dir / detail_name(path)
        detail_path.write_text(
            json.dumps(
                {"record": record, "parsed": parsed, "items": items, "raw_text": text},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        record["detail_file"] = detail_path.name

    except subprocess.TimeoutExpired:
        record["status"] = "timeout"
        record["issues"] = ["processing_timeout"]
        record["error"] = "processing timeout"
    except Exception as exc:
        record["status"] = "error"
        record["issues"] = ["processing_error"]
        record["error"] = str(exc)

    return record

def summarize(records: list[dict]) -> dict:
    total = len(records)
    status_counts = Counter(r["status"] for r in records)
    issue_counts = Counter(i for r in records for i in r.get("issues", []))
    doc_types = Counter(r["document_type"] or "לא זוהה" for r in records)

    fields = [
        "document_type", "supplier", "supplier_id", "invoice_number",
        "invoice_date", "subtotal", "vat", "total",
    ]
    field_completion = {}
    for field in fields:
        count = sum(1 for r in records if r.get(field) not in ("", None, "אחר"))
        field_completion[field] = {
            "count": count,
            "percent": round(100 * count / total, 1) if total else 0.0,
        }

    with_items = sum(1 for r in records if r["line_items_count"] > 0)
    text_docs = [r for r in records if r["extraction_method"] == "pdf_text"]

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "files_tested": total,
        "status_counts": dict(status_counts),
        "issue_counts": dict(issue_counts),
        "document_types": dict(doc_types),
        "field_completion": field_completion,
        "documents_with_line_items": {
            "count": with_items,
            "percent": round(100 * with_items / total, 1) if total else 0.0,
        },
        "pdf_text_documents": len(text_docs),
        "ocr_queue_documents": status_counts.get("ocr_queue", 0),
        "average_completeness_percent": round(
            sum(r["completeness_percent"] for r in records) / total, 1
        ) if total else 0.0,
    }

def write_csv(records: list[dict], path: Path) -> None:
    columns = [
        "file_name", "relative_path", "extension", "status", "extraction_method",
        "document_type", "supplier", "supplier_id", "invoice_number",
        "invoice_date", "due_date", "subtotal", "vat", "total",
        "line_items_count", "completeness_percent", "issues", "error",
        "detail_file",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["issues"] = " | ".join(record.get("issues", []))
            writer.writerow({c: row.get(c, "") for c in columns})

def run_dataset(dataset: Path, output: Path) -> dict:
    dataset = dataset.expanduser().resolve()
    output = output.expanduser().resolve()
    detail_dir = output / "documents"
    detail_dir.mkdir(parents=True, exist_ok=True)

    files = discover_files(dataset)
    records = []

    print(f"נמצאו {len(files)} מסמכים")
    for index, file in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] {file.name}")
        record = analyze(file, dataset, detail_dir)
        records.append(record)

        # Save checkpoint after every file.
        checkpoint = {
            "summary": summarize(records),
            "documents": records,
        }
        (output / "report.partial.json").write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    result = {"summary": summarize(records), "documents": records}
    (output / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(records, output / "report.csv")

    s = result["summary"]
    print("\n========== דוח מהיר ==========")
    print(f"מסמכים: {s['files_tested']}")
    print(f"עברו: {s['status_counts'].get('pass', 0)}")
    print(f"לבדיקה: {s['status_counts'].get('review', 0)}")
    print(f"נכשלו: {s['status_counts'].get('fail', 0)}")
    print(f"תור OCR: {s['status_counts'].get('ocr_queue', 0)}")
    print(f"Timeout: {s['status_counts'].get('timeout', 0)}")
    print(f"שגיאות: {s['status_counts'].get('error', 0)}")
    print(f"שלמות ממוצעת: {s['average_completeness_percent']}%")
    print(f"הדוח נשמר ב: {output}")

    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument(
        "--output",
        default=str(Path.home() / "restaurant-invoices" / "batch-results"),
    )
    args = parser.parse_args()
    run_dataset(Path(args.dataset), Path(args.output))

if __name__ == "__main__":
    main()
