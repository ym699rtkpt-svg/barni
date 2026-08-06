
from __future__ import annotations

import json
import re
import shutil
import statistics
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ACCOUNTING_TYPES = {
    "חשבונית מס",
    "חשבונית מס/קבלה",
    "חשבונית זיכוי",
    "קבלה",
}


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _canonical_product(value: str) -> str:
    text = _text(value).lower()
    text = re.sub(r"[^0-9a-zא-ת\s]", " ", text)
    text = re.sub(
        r"\b(?:קג|ק\"ג|יחידה|יחידות|חבילה|ליטר|גרם|מארז|קרטון|שק|בקבוק)\b",
        " ",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def load_ai_results(results_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    results_dir = Path(results_dir).expanduser()
    report_path = results_dir / "report.json"
    documents_dir = results_dir / "documents"

    if not report_path.exists():
        raise FileNotFoundError(f"לא נמצא report.json בתוך {results_dir}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    document_rows = []

    for index, record in enumerate(report.get("documents", []), start=1):
        row = dict(record)
        row["document_id"] = index
        for field in (
            "supplier",
            "supplier_id",
            "invoice_number",
            "document_type",
            "invoice_date",
            "due_date",
        ):
            row[field] = _text(row.get(field))
        for field in ("subtotal", "vat", "total", "confidence"):
            row[field] = _number(row.get(field))
        row["items_count"] = int(float(row.get("items_count") or 0))
        document_rows.append(row)

    documents = pd.DataFrame(document_rows)

    item_rows = []
    if documents_dir.exists():
        for detail_path in sorted(documents_dir.glob("*.json")):
            try:
                detail = json.loads(detail_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            record = detail.get("record", {})
            document = detail.get("document", {})
            items = document.get("items", []) or []

            common = {
                "detail_file": detail_path.name,
                "file_name": _text(record.get("file_name")),
                "supplier": _text(document.get("supplier") or record.get("supplier")),
                "supplier_id": _text(document.get("supplier_id") or record.get("supplier_id")),
                "invoice_number": _text(document.get("invoice_number") or record.get("invoice_number")),
                "invoice_date": _text(document.get("invoice_date") or record.get("invoice_date")),
                "document_type": _text(document.get("document_type") or record.get("document_type")),
            }

            for item_index, item in enumerate(items, start=1):
                description = _text(item.get("description"))
                item_rows.append({
                    **common,
                    "item_index": item_index,
                    "item_code": _text(item.get("item_code")),
                    "description": description,
                    "canonical_product": _canonical_product(description),
                    "quantity": _number(item.get("quantity")),
                    "unit": _text(item.get("unit")),
                    "unit_price": _number(item.get("unit_price")),
                    "line_total": _number(item.get("line_total")),
                })

    return documents, pd.DataFrame(item_rows)


def build_audit(documents: pd.DataFrame) -> pd.DataFrame:
    if documents.empty:
        return pd.DataFrame()

    alerts = []
    docs = documents.copy()
    duplicate_keys = (
        docs.assign(
            _key=docs["supplier_id"].fillna("").astype(str)
            + "|"
            + docs["invoice_number"].fillna("").astype(str)
        )["_key"]
        .value_counts()
    )

    nonnegative_totals = [
        float(value)
        for value in pd.to_numeric(docs["total"], errors="coerce").dropna()
        if float(value) >= 0
    ]
    median = statistics.median(nonnegative_totals) if nonnegative_totals else 0
    mad = (
        statistics.median([abs(x - median) for x in nonnegative_totals])
        if len(nonnegative_totals) >= 3
        else 0
    ) or 1

    for _, row in docs.iterrows():
        issues = []
        severity = "info"

        supplier_id = _text(row.get("supplier_id"))
        invoice_number = _text(row.get("invoice_number"))
        key = f"{supplier_id}|{invoice_number}"

        if invoice_number and duplicate_keys.get(key, 0) > 1:
            issues.append("כפילות לפי ספק ומספר מסמך")
            severity = "high"

        subtotal = _number(row.get("subtotal"))
        vat = _number(row.get("vat"))
        total = _number(row.get("total"))
        if all(v is not None for v in (subtotal, vat, total)):
            delta = round(subtotal + vat - total, 2)
            if abs(delta) > 0.05:
                issues.append(f"אי התאמת סכומים: {delta:+,.2f} ₪")
                severity = "high"

        if row.get("document_type") == "חשבונית זיכוי" and total is not None and total > 0:
            issues.append("זיכוי עם סכום חיובי")
            severity = "high"

        if row.get("status") == "review":
            machine = _text(row.get("machine_issues"))
            notes = _text(row.get("model_notes"))
            issues.append(machine or notes or "סומן לבדיקה")
            if severity != "high":
                severity = "medium"

        if row.get("document_type") in ACCOUNTING_TYPES and not supplier_id:
            issues.append("חסר ח.פ./עוסק מורשה")
            if severity != "high":
                severity = "medium"

        if not _text(row.get("invoice_date")):
            issues.append("חסר תאריך")
            severity = "high"

        if total is not None and total >= 0 and total > median + 6 * mad:
            issues.append(f"סכום חריג ביחס למאגר: {total:,.2f} ₪")
            if severity != "high":
                severity = "medium"

        if issues:
            alerts.append({
                "severity": severity,
                "file_name": _text(row.get("file_name")),
                "supplier": _text(row.get("supplier")),
                "invoice_number": invoice_number,
                "invoice_date": _text(row.get("invoice_date")),
                "total": total,
                "message": " | ".join(dict.fromkeys(issues)),
            })

    return pd.DataFrame(alerts)


def build_price_alerts(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame()

    work = items.copy()
    work["_date"] = pd.to_datetime(work["invoice_date"], errors="coerce")
    work = work[
        work["canonical_product"].astype(str).str.len().gt(2)
        & work["unit_price"].notna()
        & work["_date"].notna()
    ].sort_values(["canonical_product", "_date"])

    alerts = []
    for product, group in work.groupby("canonical_product"):
        previous = None
        for _, row in group.iterrows():
            price = float(row["unit_price"])
            if previous is not None and previous["price"] > 0:
                change = (price - previous["price"]) / previous["price"] * 100
                if abs(change) >= 5:
                    alerts.append({
                        "severity": "high" if change >= 15 else "medium",
                        "product": row["description"],
                        "supplier": row["supplier"],
                        "invoice_date": row["invoice_date"],
                        "previous_date": previous["date"],
                        "previous_price": previous["price"],
                        "current_price": price,
                        "change_percent": round(change, 1),
                        "message": (
                            f"{row['description']}: "
                            f"{previous['price']:,.2f} → {price:,.2f} ₪ "
                            f"({change:+.1f}%)"
                        ),
                    })
            previous = {"price": price, "date": row["invoice_date"]}

    return pd.DataFrame(alerts)


def supplier_comparison(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame()

    work = items[
        items["canonical_product"].astype(str).str.len().gt(2)
        & items["unit_price"].notna()
        & items["supplier"].astype(str).str.len().gt(0)
    ]

    rows = []
    for _, group in work.groupby("canonical_product"):
        prices = group.groupby("supplier")["unit_price"].median().dropna().sort_values()
        if len(prices) < 2 or float(prices.iloc[0]) <= 0:
            continue
        low, high = float(prices.iloc[0]), float(prices.iloc[-1])
        rows.append({
            "product": group.iloc[-1]["description"],
            "cheapest_supplier": prices.index[0],
            "cheapest_price": low,
            "highest_supplier": prices.index[-1],
            "highest_price": high,
            "gap_percent": round((high - low) / low * 100, 1),
        })

    return (
        pd.DataFrame(rows).sort_values("gap_percent", ascending=False)
        if rows else pd.DataFrame()
    )


def dashboard_metrics(documents: pd.DataFrame, items: pd.DataFrame) -> dict:
    docs = documents.copy()
    docs["_date"] = pd.to_datetime(docs["invoice_date"], errors="coerce")
    accounting = docs[docs["document_type"].isin(ACCOUNTING_TYPES)].copy()
    accounting["total"] = pd.to_numeric(accounting["total"], errors="coerce")

    accounting["month"] = accounting["_date"].dt.to_period("M").astype(str)

    return {
        "document_count": len(docs),
        "accounting_document_count": len(accounting),
        "supplier_count": int(accounting["supplier"].replace("", pd.NA).nunique()),
        "total_spend": float(accounting["total"].fillna(0).sum()),
        "item_rows": len(items),
        "review_count": int((docs["status"] == "review").sum()),
        "supplier_spend": (
            accounting.groupby("supplier")["total"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        ),
        "monthly_spend": (
            accounting.groupby("month")["total"]
            .sum()
            .reset_index()
            .sort_values("month")
        ),
        "document_types": (
            docs["document_type"]
            .replace("", "לא זוהה")
            .value_counts()
            .rename_axis("document_type")
            .reset_index(name="count")
        ),
    }


def create_accountant_package(
    documents: pd.DataFrame,
    items: pd.DataFrame,
    dataset_dir: Path,
    output_dir: Path,
    month: str = "",
) -> Path:
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = Path(dataset_dir).expanduser()

    docs = documents.copy()
    if month:
        docs = docs[docs["invoice_date"].astype(str).str.startswith(month)]
    docs = docs[docs["document_type"].isin(ACCOUNTING_TYPES)]

    selected_files = set(docs["file_name"].astype(str))
    selected_items = items[items["file_name"].astype(str).isin(selected_files)]

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = output_dir / f"accountant_package_{stamp}"
    package_dir.mkdir(parents=True, exist_ok=True)

    doc_columns = [
        "file_name", "document_type", "supplier", "supplier_id",
        "invoice_number", "invoice_date", "due_date",
        "subtotal", "vat", "total", "status", "confidence",
    ]
    docs[[c for c in doc_columns if c in docs.columns]].to_csv(
        package_dir / "documents.csv",
        index=False,
        encoding="utf-8-sig",
        quoting=1,
    )

    item_columns = [
        "file_name", "supplier", "invoice_number", "invoice_date",
        "item_code", "description", "quantity", "unit",
        "unit_price", "line_total",
    ]
    selected_items[[c for c in item_columns if c in selected_items.columns]].to_csv(
        package_dir / "line_items.csv",
        index=False,
        encoding="utf-8-sig",
        quoting=1,
    )

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "month_filter": month,
        "documents_count": len(docs),
        "items_count": len(selected_items),
        "total": float(pd.to_numeric(docs["total"], errors="coerce").fillna(0).sum()),
        "review_required": int((docs["status"] == "review").sum()),
    }
    (package_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    originals = package_dir / "original_documents"
    originals.mkdir(exist_ok=True)
    for file_name in selected_files:
        matches = list(dataset_dir.rglob(file_name))
        if matches:
            shutil.copy2(matches[0], originals / file_name)

    zip_path = output_dir / f"accountant_package_{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in package_dir.rglob("*"):
            if file.is_file():
                archive.write(file, arcname=file.relative_to(package_dir))

    return zip_path
