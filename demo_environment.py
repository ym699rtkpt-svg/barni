from __future__ import annotations

import argparse
import calendar
import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parent
DEMO_ROOT = PROJECT_ROOT / ".barni-demo"
DEMO_BUSINESS_NAME = "Cedar Table Demo Restaurant"


@contextmanager
def _using_data_root(root: Path) -> Iterator[None]:
    previous = os.environ.get("BARNI_DATA_ROOT")
    os.environ["BARNI_DATA_ROOT"] = str(root.resolve())
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("BARNI_DATA_ROOT", None)
        else:
            os.environ["BARNI_DATA_ROOT"] = previous


def _month_dates(today: date | None = None) -> list[str]:
    current = today or date.today()
    last_day = calendar.monthrange(current.year, current.month)[1]
    days = [1, 2, 4, 6, min(8, last_day)]
    return [date(current.year, current.month, day).isoformat() for day in days]


def _pdf_bytes(title: str, lines: list[str]) -> bytes:
    def escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    commands = ["BT", "/F1 12 Tf", "50 790 Td", "18 TL"]
    for index, line in enumerate([title, *lines]):
        if index:
            commands.append("T*")
        commands.append(f"({escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode()
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, value in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + value + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def _document(
    *,
    supplier: str,
    supplier_id: str,
    invoice_number: str,
    invoice_date: str,
    items: list[dict[str, Any]],
    category: str,
) -> dict[str, Any]:
    subtotal = round(sum(float(item["line_total"]) for item in items), 2)
    vat = round(subtotal * 0.18, 2)
    return {
        "document_type": "חשבונית מס",
        "supplier": supplier,
        "supplier_id": supplier_id,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": "",
        "subtotal": subtotal,
        "taxable_amount": subtotal,
        "exempt_amount": 0.0,
        "vat_rate": 18.0,
        "vat": vat,
        "total": round(subtotal + vat, 2),
        "tax_treatment": "חייב במע״מ",
        "currency": "ILS",
        "category": category,
        "subcategory": "",
        "confidence": 0.99,
        "machine_issues": [],
        "model_notes": [],
        "items": items,
    }


def _item(
    code: str,
    description: str,
    quantity: float,
    unit: str,
    unit_price: float,
) -> dict[str, Any]:
    return {
        "item_code": code,
        "description": description,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "line_total": round(quantity * unit_price, 2),
    }


def _demo_documents(today: date | None = None) -> list[dict[str, Any]]:
    dates = _month_dates(today)
    return [
        _document(
            supplier="Fresh Fields Produce",
            supplier_id="515000101",
            invoice_number="FF-1001",
            invoice_date=dates[0],
            category="Food & Ingredients",
            items=[
                _item("OIL-5L", "Olive Oil", 10, "unit", 42.0),
                _item("TOMATO", "Tomatoes", 20, "kg", 7.2),
            ],
        ),
        _document(
            supplier="Carmel Dairy",
            supplier_id="515000202",
            invoice_number="CD-841",
            invoice_date=dates[1],
            category="Food & Ingredients",
            items=[
                _item("MILK-3", "Milk 3%", 24, "unit", 7.9),
                _item("YOGURT", "Greek Yogurt", 12, "unit", 5.5),
            ],
        ),
        _document(
            supplier="Fresh Fields Produce",
            supplier_id="515000101",
            invoice_number="FF-1002",
            invoice_date=dates[2],
            category="Food & Ingredients",
            items=[
                _item("OIL-5L", "Olive Oil", 10, "unit", 48.0),
                _item("TOMATO", "Tomatoes", 25, "kg", 7.4),
            ],
        ),
        _document(
            supplier="Carmel Dairy",
            supplier_id="515000202",
            invoice_number="CD-842",
            invoice_date=dates[3],
            category="Food & Ingredients",
            items=[
                _item("MILK-3", "Milk 3%", 24, "unit", 8.3),
                _item("BUTTER", "Butter", 8, "unit", 13.5),
            ],
        ),
        _document(
            supplier="Galilee Kitchen Supply",
            supplier_id="515000303",
            invoice_number="GK-77",
            invoice_date=dates[4],
            category="Kitchen & Operations",
            items=[
                _item("TOWEL", "Chef Towels", 10, "unit", 18.0),
                _item("CONTAINER", "Storage Container", 6, "unit", 35.0),
            ],
        ),
    ]


def _write_source(path: Path, document: dict[str, Any]) -> None:
    lines = [
        f"Supplier: {document['supplier']}",
        f"Invoice: {document['invoice_number']}",
        f"Date: {document['invoice_date']}",
        *[
            f"{item['description']} | {item['quantity']} {item['unit']} | "
            f"{item['unit_price']:.2f} ILS"
            for item in document["items"]
        ],
        f"Subtotal: {document['subtotal']:.2f} ILS",
        f"VAT: {document['vat']:.2f} ILS",
        f"Total: {document['total']:.2f} ILS",
    ]
    path.write_bytes(_pdf_bytes(DEMO_BUSINESS_NAME, lines))


def seed_demo(root: Path, *, today: date | None = None) -> dict[str, Any]:
    root = root.resolve()
    database_file = root / "invoice_archive.db"
    if database_file.exists():
        raise RuntimeError(f"Demo data already exists at {root}. Reset it first.")

    incoming = root / "daily-intake" / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)
    documents = _demo_documents(today)

    with _using_data_root(root):
        from database import init_database
        from services.invoice_workflow import InvoiceWorkflowService

        init_database(database_file)
        workflow = InvoiceWorkflowService()
        invoice_ids: list[int] = []
        for index, document in enumerate(documents, start=1):
            source = incoming / f"approved-{index}.pdf"
            _write_source(source, document)
            result = workflow.approve(
                {
                    "id": f"demo-approved-{index}",
                    "stored_file": str(source),
                },
                document,
            )
            if not result.success or result.invoice_id is None:
                raise RuntimeError(
                    f"Could not seed {document['invoice_number']}: {result.message}"
                )
            invoice_ids.append(result.invoice_id)

        duplicate_document = dict(documents[1])
        duplicate_source = incoming / "duplicate-carmel-dairy.pdf"
        _write_source(duplicate_source, duplicate_document)

        failed_source = incoming / "failed-reading-example.pdf"
        failed_source.write_bytes(
            _pdf_bytes(DEMO_BUSINESS_NAME, ["Unreadable scan example"])
        )
        queue = [
            {
                "id": "demo-duplicate-carmel-dairy",
                "file_name": duplicate_source.name,
                "stored_file": str(duplicate_source),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                # A duplicate enters normal review first. The canonical lifecycle
                # classifies it from the matching approved identity and the real
                # approval flow then asks for the duplicate decision.
                "queue_status": "review",
                "error": "",
                "document": duplicate_document,
                "method": "demo_evidence",
            },
            {
                "id": "demo-failed-reading",
                "file_name": failed_source.name,
                "stored_file": str(failed_source),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "queue_status": "error",
                "error": (
                    "I couldn't read this invoice. Try uploading a clearer copy, "
                    "or enter the details during review."
                ),
                "technical_error": "Demo fixture: document text unavailable",
                "document": {
                    "document_type": "חשבונית מס",
                    "supplier": "",
                    "supplier_id": "",
                    "invoice_number": "",
                    "invoice_date": "",
                    "total": None,
                    "currency": "ILS",
                    "items": [],
                    "confidence": 0.0,
                    "machine_issues": ["missing_supplier", "missing_invoice_date"],
                    "model_notes": [],
                },
                "method": "failed_local_reading",
            },
        ]
        queue_path = root / "daily-intake" / "queue.json"
        queue_payload = json.dumps(queue, ensure_ascii=False, indent=2)
        queue_path.write_text(queue_payload, encoding="utf-8")
        queue_path.with_suffix(".json.backup").write_text(
            queue_payload,
            encoding="utf-8",
        )

    manifest = {
        "business_name": DEMO_BUSINESS_NAME,
        "seeded_at": datetime.now().isoformat(timespec="seconds"),
        "accounting_month": documents[0]["invoice_date"][:7],
        "approved_invoice_ids": invoice_ids,
        "approved_invoices": len(documents),
        "open_duplicate_examples": 1,
        "failed_reading_examples": 1,
    }
    (root / "demo-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def verify_demo(root: Path = DEMO_ROOT) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / "demo-manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("Demo data is missing. Run the reset command first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    with _using_data_root(root):
        from database import search_invoices
        from services.accountant_workspace import (
            accountant_month_status,
            build_accountant_package,
        )
        from services.business_facts import ComparablePriceLedger
        from services.business_memory import business_memory_data
        from services.invoice_workflow import invoice_workflow_snapshot

        approved = search_invoices(statuses=["approved"])
        memory = business_memory_data()
        workflow = invoice_workflow_snapshot()
        olive_invoices = search_invoices(
            free_text="Olive Oil",
            statuses=["approved"],
        )
        supplier_invoices = search_invoices(
            free_text="Fresh Fields Produce",
            statuses=["approved"],
        )
        ledger = ComparablePriceLedger()
        olive_facts = [
            fact
            for fact in ledger.trusted_observations()
            if fact.canonical_product_name == "Olive Oil"
        ]
        comparisons = [
            ledger.previous_comparable(fact)
            for fact in olive_facts
        ]
        price_change = next(
            (value for value in comparisons if value and value.comparable),
            None,
        )
        month_status = accountant_month_status(manifest["accounting_month"])
        package = build_accountant_package(month_status)

    checks = {
        "approved_invoices": len(approved) == 5,
        "suppliers": int(memory["supplier_count"]) == 3,
        "products": int(memory["product_count"]) >= 7,
        "duplicate": workflow.duplicate == 1,
        "failed_reading": workflow.needs_attention == 1,
        "product_search": len(olive_invoices) == 2,
        "supplier_search": len(supplier_invoices) == 2,
        "trusted_price_change": bool(
            price_change
            and round(float(price_change.change_pct or 0), 1) == 14.3
        ),
        "accountant_month": len(month_status["documents"]) == 5,
        "accountant_export": len(package) > 0,
        "evidence_files": bool(approved["archived_path"].map(Path).map(Path.exists).all()),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError("Demo verification failed: " + ", ".join(failed))
    return {
        "business_name": manifest["business_name"],
        "accounting_month": manifest["accounting_month"],
        "checks": checks,
    }


def reset_demo() -> dict[str, Any]:
    target = DEMO_ROOT.resolve()
    project = PROJECT_ROOT.resolve()
    if target.parent != project or target.name != ".barni-demo":
        raise RuntimeError(f"Refusing to reset unexpected path: {target}")
    if target.exists():
        shutil.rmtree(target)
    manifest = seed_demo(target)
    verify_demo(target)
    return manifest


def start_demo(port: int) -> int:
    if not (DEMO_ROOT / "demo-manifest.json").exists():
        reset_demo()
    else:
        verify_demo(DEMO_ROOT)
    environment = os.environ.copy()
    environment["BARNI_DATA_ROOT"] = str(DEMO_ROOT.resolve())
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(PROJECT_ROOT / "app.py"),
        "--server.port",
        str(port),
    ]
    try:
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=environment,
            check=False,
        ).returncode
    except KeyboardInterrupt:
        print("\nDemo stopped.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproducible Barni demo environment")
    parser.add_argument("command", choices=("reset", "verify", "start"))
    parser.add_argument("--port", type=int, default=8501)
    arguments = parser.parse_args()

    try:
        if arguments.command == "reset":
            result = reset_demo()
            print(
                f"Demo reset complete: {result['business_name']} "
                f"({result['approved_invoices']} approved invoices)."
            )
        elif arguments.command == "verify":
            result = verify_demo(DEMO_ROOT)
            print(
                f"Demo verified: {result['business_name']} "
                f"for {result['accounting_month']}."
            )
            for name in result["checks"]:
                print(f"  ✓ {name.replace('_', ' ')}")
        else:
            return start_demo(arguments.port)
    except Exception as exc:
        print(f"Demo environment error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
