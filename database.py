
from __future__ import annotations

import json
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def root_dir() -> Path:
    root = Path.home() / "restaurant-invoices"
    root.mkdir(parents=True, exist_ok=True)
    return root


def database_path() -> Path:
    path = root_dir() / "invoice_archive.db"
    init_database(path)
    return path


def archive_root() -> Path:
    path = root_dir() / "archive"
    path.mkdir(parents=True, exist_ok=True)
    return path


def connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or database_path()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _backup_database(db_path: Path) -> Path | None:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None

    backup_dir = root_dir() / "database-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}_{stamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _ensure_column(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = _column_names(connection, table)
    if column not in columns:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def _current_schema_version(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT MAX(version) FROM schema_migrations"
    ).fetchone()
    return int(row[0] or 0)


def _record_schema_version(
    connection: sqlite3.Connection,
    version: int,
    description: str,
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO schema_migrations (
            version, applied_at, description
        ) VALUES (?, ?, ?)
        """,
        (
            version,
            datetime.now().isoformat(timespec="seconds"),
            description,
        ),
    )


def _run_migrations(connection: sqlite3.Connection) -> None:
    current = _current_schema_version(connection)

    if current < 1:
        _record_schema_version(
            connection,
            1,
            "Initial invoice archive schema",
        )

    if current < 2:
        _ensure_column(
            connection,
            "invoices",
            "taxable_amount",
            "REAL",
        )
        _ensure_column(
            connection,
            "invoices",
            "exempt_amount",
            "REAL",
        )
        _ensure_column(
            connection,
            "invoices",
            "vat_rate",
            "REAL",
        )
        _ensure_column(
            connection,
            "invoices",
            "tax_treatment",
            "TEXT NOT NULL DEFAULT 'לא ברור'",
        )
        _record_schema_version(
            connection,
            2,
            "Extended VAT structure",
        )

    if current < 3:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS invoice_tags (
                invoice_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY(invoice_id, tag_id),
                FOREIGN KEY(invoice_id)
                    REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id)
                    REFERENCES tags(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS invoice_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                changed_at TEXT NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                FOREIGN KEY(invoice_id)
                    REFERENCES invoices(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS month_closures (
                month TEXT PRIMARY KEY,
                closed_at TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                documents_count INTEGER NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0
            );
            """
        )
        _record_schema_version(
            connection,
            3,
            "Tags, history and month closures",
        )

    if current < 4:
        _ensure_column(
            connection,
            "invoices",
            "category",
            "TEXT NOT NULL DEFAULT 'לא מסווג'",
        )
        _ensure_column(
            connection,
            "invoices",
            "subcategory",
            "TEXT NOT NULL DEFAULT ''",
        )
        _record_schema_version(
            connection,
            4,
            "Expense categories",
        )


def init_database(path: Path | None = None) -> None:
    db_path = path or (root_dir() / "invoice_archive.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # First open: ensure the base schema exists and inspect the version.
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                archived_path TEXT NOT NULL,
                document_type TEXT NOT NULL DEFAULT '',
                supplier TEXT NOT NULL DEFAULT '',
                supplier_id TEXT NOT NULL DEFAULT '',
                invoice_number TEXT NOT NULL DEFAULT '',
                invoice_date TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL DEFAULT '',
                subtotal REAL,
                taxable_amount REAL,
                exempt_amount REAL,
                vat_rate REAL,
                vat REAL,
                total REAL,
                tax_treatment TEXT NOT NULL DEFAULT 'לא ברור',
                currency TEXT NOT NULL DEFAULT 'ILS',
                status TEXT NOT NULL DEFAULT 'approved',
                confidence REAL NOT NULL DEFAULT 0,
                machine_issues TEXT NOT NULL DEFAULT '[]',
                model_notes TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                approved_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(
                    supplier_id,
                    invoice_number,
                    document_type
                )
            );

            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                item_code TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                quantity REAL,
                unit TEXT NOT NULL DEFAULT '',
                unit_price REAL,
                line_total REAL,
                FOREIGN KEY(invoice_id)
                    REFERENCES invoices(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_invoices_supplier
            ON invoices(supplier);

            CREATE INDEX IF NOT EXISTS idx_invoices_date
            ON invoices(invoice_date);

            CREATE INDEX IF NOT EXISTS idx_invoices_number
            ON invoices(invoice_number);

            CREATE INDEX IF NOT EXISTS idx_items_description
            ON invoice_items(description);
            """
        )
        connection.commit()

        current_version = _current_schema_version(connection)
    finally:
        connection.close()

    # Back up only when a structural upgrade is actually needed.
    if current_version < 3 and db_path.exists() and db_path.stat().st_size > 0:
        _backup_database(db_path)

    # Second open: run the migration in one explicit transaction.
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")
        _run_migrations(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def database_health() -> dict:
    db_path = database_path()

    with sqlite3.connect(db_path) as connection:
        version = _current_schema_version(connection)
        columns = sorted(_column_names(connection, "invoices"))
        invoice_count = connection.execute(
            "SELECT COUNT(*) FROM invoices"
        ).fetchone()[0]

    required = {
        "tax_treatment",
        "taxable_amount",
        "exempt_amount",
        "vat_rate",
    }

    return {
        "database_path": str(db_path),
        "schema_version": version,
        "invoice_count": int(invoice_count),
        "missing_required_columns": sorted(required - set(columns)),
        "healthy": required.issubset(columns),
    }


def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _number(value: Any):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def archive_destination(source: Path, invoice_date: str) -> Path:
    try:
        parsed = datetime.strptime(invoice_date, "%Y-%m-%d")
        year, month = f"{parsed.year:04d}", f"{parsed.month:02d}"
    except ValueError:
        year, month = "unknown-year", "unknown-month"

    directory = archive_root() / year / month
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / source.name

    if destination.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = destination.with_name(
            f"{destination.stem}_{stamp}{destination.suffix}"
        )
    return destination


def duplicate_exists(supplier_id: str, invoice_number: str, document_type: str) -> bool:
    if not invoice_number:
        return False
    with connect() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count FROM invoices
            WHERE supplier_id = ? AND invoice_number = ? AND document_type = ?
            """,
            (_text(supplier_id), _text(invoice_number), _text(document_type)),
        ).fetchone()
    return bool(row["count"])


def insert_invoice(source_file: Path, document: dict, move_source: bool = False) -> int:
    init_database()
    now = datetime.now().isoformat(timespec="seconds")
    destination = archive_destination(source_file, _text(document.get("invoice_date")))

    if move_source:
        shutil.move(str(source_file), str(destination))
    else:
        shutil.copy2(source_file, destination)

    values = {
        "file_name": destination.name,
        "archived_path": str(destination),
        "document_type": _text(document.get("document_type")),
        "supplier": _text(document.get("supplier")),
        "supplier_id": _text(document.get("supplier_id")),
        "invoice_number": _text(document.get("invoice_number")),
        "invoice_date": _text(document.get("invoice_date")),
        "due_date": _text(document.get("due_date")),
        "subtotal": _number(document.get("subtotal")),
        "taxable_amount": _number(document.get("taxable_amount")),
        "exempt_amount": _number(document.get("exempt_amount")),
        "vat_rate": _number(document.get("vat_rate")),
        "vat": _number(document.get("vat")),
        "total": _number(document.get("total")),
        "tax_treatment": _text(document.get("tax_treatment")) or "לא ברור",
        "category": _text(document.get("category")) or "לא מסווג",
        "subcategory": _text(document.get("subcategory")),
        "currency": _text(document.get("currency")) or "ILS",
        "status": "approved",
        "confidence": _number(document.get("confidence")) or 0.0,
        "machine_issues": json.dumps(document.get("machine_issues", []), ensure_ascii=False),
        "model_notes": json.dumps(document.get("model_notes", []), ensure_ascii=False),
        "created_at": now,
        "approved_at": now,
        "updated_at": now,
    }

    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO invoices (
                file_name, archived_path, document_type, supplier, supplier_id,
                invoice_number, invoice_date, due_date, subtotal,
                taxable_amount, exempt_amount, vat_rate, vat, total,
                tax_treatment, category, subcategory, currency, status, confidence, machine_issues,
                model_notes, created_at, approved_at, updated_at
            ) VALUES (
                :file_name, :archived_path, :document_type, :supplier, :supplier_id,
                :invoice_number, :invoice_date, :due_date, :subtotal,
                :taxable_amount, :exempt_amount, :vat_rate, :vat, :total,
                :tax_treatment, :category, :subcategory, :currency, :status, :confidence, :machine_issues,
                :model_notes, :created_at, :approved_at, :updated_at
            )
            """,
            values,
        )
        invoice_id = int(cursor.lastrowid)

        for item in document.get("items", []) or []:
            connection.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id, item_code, description, quantity,
                    unit, unit_price, line_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    _text(item.get("item_code")),
                    _text(item.get("description")),
                    _number(item.get("quantity")),
                    _text(item.get("unit")),
                    _number(item.get("unit_price")),
                    _number(item.get("line_total")),
                ),
            )
        connection.commit()
    return invoice_id


def update_invoice(invoice_id: int, values: dict) -> None:
    allowed = {
        "document_type", "supplier", "supplier_id", "invoice_number",
        "invoice_date", "due_date", "subtotal", "taxable_amount",
        "exempt_amount", "vat_rate", "vat", "total", "tax_treatment",
        "currency", "status", "confidence", "category", "subcategory",
    }
    with connect() as connection:
        current = connection.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()
        if current is None:
            raise ValueError("החשבונית לא נמצאה.")

        assignments, params = [], []
        changed_at = datetime.now().isoformat(timespec="seconds")

        for field, value in values.items():
            if field not in allowed:
                continue
            new_value = (
                _number(value)
                if field in {
                    "subtotal", "taxable_amount", "exempt_amount",
                    "vat_rate", "vat", "total", "confidence"
                }
                else _text(value)
            )
            old_value = current[field]

            if str(old_value) != str(new_value):
                assignments.append(f"{field} = ?")
                params.append(new_value)
                connection.execute(
                    """
                    INSERT INTO invoice_history (
                        invoice_id, changed_at, field_name, old_value, new_value
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (invoice_id, changed_at, field, _text(old_value), _text(new_value)),
                )

        if assignments:
            assignments.append("updated_at = ?")
            params.append(changed_at)
            params.append(invoice_id)
            connection.execute(
                f"UPDATE invoices SET {', '.join(assignments)} WHERE id = ?",
                params,
            )
        connection.commit()


def replace_items(invoice_id: int, items: list[dict]) -> None:
    with connect() as connection:
        connection.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        for item in items:
            connection.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id, item_code, description, quantity,
                    unit, unit_price, line_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    _text(item.get("item_code")),
                    _text(item.get("description")),
                    _number(item.get("quantity")),
                    _text(item.get("unit")),
                    _number(item.get("unit_price")),
                    _number(item.get("line_total")),
                ),
            )
        connection.commit()


def suppliers() -> list[str]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT supplier FROM invoices
            WHERE supplier <> '' ORDER BY supplier COLLATE NOCASE
            """
        ).fetchall()
    return [row["supplier"] for row in rows]


def supplier_suggestions(query: str, limit: int = 12) -> list[str]:
    query = _text(query)
    all_suppliers = suppliers()
    if not query:
        return all_suppliers[:limit]

    lowered = query.lower()
    if len(query) == 1:
        return [
            supplier for supplier in all_suppliers
            if supplier.lower().startswith(lowered)
        ][:limit]

    starts = [
        supplier for supplier in all_suppliers
        if supplier.lower().startswith(lowered)
    ]
    contains = [
        supplier for supplier in all_suppliers
        if lowered in supplier.lower() and supplier not in starts
    ]
    return (starts + contains)[:limit]


def all_tags() -> list[str]:
    with connect() as connection:
        rows = connection.execute("SELECT name FROM tags ORDER BY name").fetchall()
    return [row["name"] for row in rows]


def invoice_tags(invoice_id: int) -> list[str]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT tags.name FROM tags
            JOIN invoice_tags ON invoice_tags.tag_id = tags.id
            WHERE invoice_tags.invoice_id = ?
            ORDER BY tags.name
            """,
            (invoice_id,),
        ).fetchall()
    return [row["name"] for row in rows]


def set_invoice_tags(invoice_id: int, names: list[str]) -> None:
    cleaned = sorted({_text(name) for name in names if _text(name)})
    with connect() as connection:
        connection.execute("DELETE FROM invoice_tags WHERE invoice_id = ?", (invoice_id,))
        for name in cleaned:
            connection.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (name,))
            tag_id = connection.execute(
                "SELECT id FROM tags WHERE name = ?", (name,)
            ).fetchone()["id"]
            connection.execute(
                "INSERT OR IGNORE INTO invoice_tags(invoice_id, tag_id) VALUES (?, ?)",
                (invoice_id, tag_id),
            )
        connection.commit()


def search_invoices(
    free_text: str = "",
    supplier_query: str = "",
    invoice_number: str = "",
    document_types: list[str] | None = None,
    statuses: list[str] | None = None,
    tags: list[str] | None = None,
    start_date: str = "",
    end_date: str = "",
    min_total: float | None = None,
    max_total: float | None = None,
    sort_by: str = "invoice_date",
    descending: bool = True,
) -> pd.DataFrame:
    clauses, params = ["1 = 1"], []

    if free_text:
        clauses.append(
            """
            (
                invoices.supplier LIKE ?
                OR invoices.invoice_number LIKE ?
                OR invoices.supplier_id LIKE ?
                OR EXISTS (
                    SELECT 1 FROM invoice_items
                    WHERE invoice_items.invoice_id = invoices.id
                    AND (
                        invoice_items.description LIKE ?
                        OR invoice_items.item_code LIKE ?
                    )
                )
            )
            """
        )
        token = f"%{free_text}%"
        params.extend([token] * 5)

    if supplier_query:
        clauses.append("invoices.supplier LIKE ?")
        params.append(f"%{supplier_query}%")

    if invoice_number:
        clauses.append("invoices.invoice_number LIKE ?")
        params.append(f"%{invoice_number}%")

    if document_types:
        placeholders = ",".join("?" for _ in document_types)
        clauses.append(f"invoices.document_type IN ({placeholders})")
        params.extend(document_types)

    if statuses:
        placeholders = ",".join("?" for _ in statuses)
        clauses.append(f"invoices.status IN ({placeholders})")
        params.extend(statuses)

    if tags:
        placeholders = ",".join("?" for _ in tags)
        clauses.append(
            f"""
            EXISTS (
                SELECT 1 FROM invoice_tags
                JOIN tags ON tags.id = invoice_tags.tag_id
                WHERE invoice_tags.invoice_id = invoices.id
                AND tags.name IN ({placeholders})
            )
            """
        )
        params.extend(tags)

    if start_date:
        clauses.append("invoices.invoice_date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("invoices.invoice_date <= ?")
        params.append(end_date)
    if min_total is not None:
        clauses.append("(invoices.total IS NULL OR invoices.total >= ?)")
        params.append(min_total)
    if max_total is not None:
        clauses.append("(invoices.total IS NULL OR invoices.total <= ?)")
        params.append(max_total)

    sort_map = {
        "invoice_date": "invoices.invoice_date",
        "supplier": "invoices.supplier",
        "total": "invoices.total",
        "invoice_number": "invoices.invoice_number",
    }
    order_column = sort_map.get(sort_by, "invoices.invoice_date")
    direction = "DESC" if descending else "ASC"

    sql = f"""
        SELECT invoices.*
        FROM invoices
        WHERE {' AND '.join(clauses)}
        ORDER BY {order_column} {direction}, invoices.supplier ASC
    """
    with connect() as connection:
        return pd.read_sql_query(sql, connection, params=params)


def invoice_items(invoice_id: int) -> pd.DataFrame:
    with connect() as connection:
        return pd.read_sql_query(
            """
            SELECT item_code, description, quantity, unit, unit_price, line_total
            FROM invoice_items WHERE invoice_id = ? ORDER BY id
            """,
            connection,
            params=[invoice_id],
        )


def invoice_history(invoice_id: int) -> pd.DataFrame:
    with connect() as connection:
        return pd.read_sql_query(
            """
            SELECT changed_at, field_name, old_value, new_value
            FROM invoice_history WHERE invoice_id = ?
            ORDER BY changed_at DESC, id DESC
            """,
            connection,
            params=[invoice_id],
        )



def supplier_summary(supplier: str) -> dict:
    with connect() as connection:
        documents = pd.read_sql_query(
            """
            SELECT * FROM invoices
            WHERE supplier = ?
            ORDER BY invoice_date DESC
            """,
            connection,
            params=[supplier],
        )
        items = pd.read_sql_query(
            """
            SELECT invoice_items.*
            FROM invoice_items
            JOIN invoices ON invoices.id = invoice_items.invoice_id
            WHERE invoices.supplier = ?
            ORDER BY invoices.invoice_date DESC, invoice_items.id
            """,
            connection,
            params=[supplier],
        )

    total = pd.to_numeric(documents.get("total"), errors="coerce").fillna(0)
    vat = pd.to_numeric(documents.get("vat"), errors="coerce").fillna(0)
    return {
        "documents": documents,
        "items": items,
        "invoice_count": len(documents),
        "total_spend": float(total.sum()),
        "vat_total": float(vat.sum()),
        "average_invoice": float(total.mean()) if len(total) else 0.0,
        "last_invoice_date": (
            str(documents.iloc[0]["invoice_date"])
            if not documents.empty else ""
        ),
    }


def category_summary() -> pd.DataFrame:
    with connect() as connection:
        return pd.read_sql_query(
            """
            SELECT
                category,
                subcategory,
                COUNT(*) AS documents_count,
                COALESCE(SUM(total), 0) AS total
            FROM invoices
            GROUP BY category, subcategory
            ORDER BY total DESC
            """,
            connection,
        )


def control_center_data() -> dict:
    with connect() as connection:
        invoices = pd.read_sql_query(
            "SELECT * FROM invoices",
            connection,
        )
        duplicates = connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT supplier_id, invoice_number, document_type, COUNT(*) AS c
                FROM invoices
                WHERE invoice_number <> ''
                GROUP BY supplier_id, invoice_number, document_type
                HAVING c > 1
            )
            """
        ).fetchone()[0]

    if invoices.empty:
        return {
            "invoice_count": 0,
            "supplier_count": 0,
            "vat_total": 0.0,
            "review_count": 0,
            "duplicates": 0,
            "uncategorized": 0,
            "latest_month": "",
            "latest_month_count": 0,
        }

    invoices["invoice_date_dt"] = pd.to_datetime(
        invoices["invoice_date"],
        errors="coerce",
    )
    invoices["month"] = invoices["invoice_date_dt"].dt.to_period("M").astype(str)
    valid_months = invoices["month"].replace("NaT", pd.NA).dropna()
    latest_month = valid_months.max() if not valid_months.empty else ""

    return {
        "invoice_count": len(invoices),
        "supplier_count": int(
            invoices["supplier"].replace("", pd.NA).nunique()
        ),
        "vat_total": float(
            pd.to_numeric(invoices["vat"], errors="coerce").fillna(0).sum()
        ),
        "review_count": int((invoices["status"] == "review").sum()),
        "duplicates": int(duplicates),
        "uncategorized": int(
            (invoices["category"].fillna("לא מסווג") == "לא מסווג").sum()
        ),
        "latest_month": latest_month,
        "latest_month_count": int(
            (invoices["month"] == latest_month).sum()
        ) if latest_month else 0,
    }


def natural_language_query(query: str) -> pd.DataFrame:
    query = _text(query)
    lowered = query.lower()

    supplier = ""
    for name in suppliers():
        if name.lower() in lowered:
            supplier = name
            break

    min_total = None
    max_total = None

    amount_matches = re.findall(r"(\d[\d,]*\.?\d*)", query)
    amounts = []
    for raw in amount_matches:
        try:
            amounts.append(float(raw.replace(",", "")))
        except ValueError:
            pass

    if "מעל" in query or "יותר מ" in query:
        min_total = amounts[-1] if amounts else None
    elif "מתחת" in query or "פחות מ" in query:
        max_total = amounts[-1] if amounts else None

    start_date = ""
    end_date = ""

    year_match = re.search(r"(20\d{2})", query)
    month_map = {
        "ינואר": "01", "פברואר": "02", "מרץ": "03",
        "אפריל": "04", "מאי": "05", "יוני": "06",
        "יולי": "07", "אוגוסט": "08", "ספטמבר": "09",
        "אוקטובר": "10", "נובמבר": "11", "דצמבר": "12",
    }

    if year_match:
        year = year_match.group(1)
        selected_month = next(
            (number for name, number in month_map.items() if name in query),
            None,
        )
        if selected_month:
            start_date = f"{year}-{selected_month}-01"
            end_date = f"{year}-{selected_month}-31"
        else:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

    free_text = ""
    product_markers = ["מוצר", "קניתי", "שמן", "עגבניות", "בצל", "דגים", "בשר"]
    if any(marker in query for marker in product_markers):
        free_text = query

    return search_invoices(
        free_text=free_text,
        supplier_query=supplier,
        statuses=["approved"],
        start_date=start_date,
        end_date=end_date,
        min_total=min_total,
        max_total=max_total,
        sort_by="invoice_date",
        descending=True,
    )


def dashboard_data() -> dict:
    with connect() as connection:
        documents = pd.read_sql_query("SELECT * FROM invoices", connection)
        items = pd.read_sql_query("SELECT * FROM invoice_items", connection)

    if documents.empty:
        return {
            "documents": documents,
            "items": items,
            "supplier_spend": pd.DataFrame(),
            "monthly_spend": pd.DataFrame(),
            "document_types": pd.DataFrame(),
        }

    documents["total"] = pd.to_numeric(documents["total"], errors="coerce")
    documents["_date"] = pd.to_datetime(documents["invoice_date"], errors="coerce")
    documents["month"] = documents["_date"].dt.to_period("M").astype(str)

    return {
        "documents": documents,
        "items": items,
        "supplier_spend": (
            documents.groupby("supplier")["total"]
            .sum().sort_values(ascending=False).reset_index()
        ),
        "monthly_spend": (
            documents.groupby("month")["total"]
            .sum().reset_index().sort_values("month")
        ),
        "document_types": (
            documents["document_type"].replace("", "לא זוהה")
            .value_counts().rename_axis("document_type").reset_index(name="count")
        ),
    }


def month_summary(month: str) -> dict:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(SUM(total), 0) AS total
            FROM invoices WHERE invoice_date LIKE ?
            """,
            (f"{month}%",),
        ).fetchone()
        closure = connection.execute(
            "SELECT * FROM month_closures WHERE month = ?", (month,)
        ).fetchone()

    return {
        "month": month,
        "documents_count": row["count"],
        "total": float(row["total"] or 0),
        "closed": closure is not None,
        "closed_at": closure["closed_at"] if closure else "",
        "note": closure["note"] if closure else "",
    }


def close_month(month: str, note: str = "") -> None:
    summary = month_summary(month)
    with connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO month_closures (
                month, closed_at, note, documents_count, total
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                month,
                datetime.now().isoformat(timespec="seconds"),
                _text(note),
                summary["documents_count"],
                summary["total"],
            ),
        )
        connection.commit()
