
from __future__ import annotations

import argparse
import json
from pathlib import Path

from database import duplicate_exists, insert_invoice


def find_source(dataset_dir: Path, file_name: str) -> Path | None:
    matches = list(dataset_dir.rglob(file_name))
    return matches[0] if matches else None


def migrate(results_dir: Path, dataset_dir: Path) -> dict:
    documents_dir = results_dir / "documents"
    detail_files = sorted(documents_dir.glob("*.json"))

    imported = skipped_duplicate = missing_source = errors = 0
    error_details = []

    for index, detail_path in enumerate(detail_files, start=1):
        print(f"[{index}/{len(detail_files)}] {detail_path.name}")
        try:
            detail = json.loads(detail_path.read_text(encoding="utf-8"))
            record = detail.get("record", {})
            document = detail.get("document", {})
            file_name = str(record.get("file_name", "")).strip()

            if duplicate_exists(
                document.get("supplier_id", ""),
                document.get("invoice_number", ""),
                document.get("document_type", ""),
            ):
                skipped_duplicate += 1
                continue

            source = find_source(dataset_dir, file_name)
            if source is None:
                missing_source += 1
                continue

            insert_invoice(source, document, move_source=False)
            imported += 1
        except Exception as exc:
            errors += 1
            error_details.append({"file": detail_path.name, "error": str(exc)})

    return {
        "files_seen": len(detail_files),
        "imported": imported,
        "skipped_duplicate": skipped_duplicate,
        "missing_source": missing_source,
        "errors": errors,
        "error_details": error_details,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        default=str(Path.home() / "restaurant-invoices" / "ai-results"),
    )
    parser.add_argument(
        "--dataset",
        default=str(Path.home() / "restaurant-invoices" / "dataset" / "invoices"),
    )
    args = parser.parse_args()

    result = migrate(
        Path(args.results).expanduser(),
        Path(args.dataset).expanduser(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
