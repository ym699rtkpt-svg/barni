
from __future__ import annotations
from knowledge_engine.line_classifier import classify_invoice_line
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

    backup_dir = db_path.parent / "database-backups"
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


def _backfill_line_types(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT id, description, line_type FROM invoice_items"
    ).fetchall()

    for row in rows:
        stored = _text(row["line_type"])
        expected = classify_invoice_line(_text(row["description"]))
        if stored != expected:
            connection.execute(
                "UPDATE invoice_items SET line_type = ? WHERE id = ?",
                (expected, row["id"]),
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

    if current < 5:
        _ensure_column(
            connection,
            "invoice_items",
            "line_type",
            "TEXT NOT NULL DEFAULT 'product'",
        )
        connection.execute(
            """
            UPDATE invoice_items
            SET line_type = 'product'
            WHERE line_type IS NULL OR line_type = ''
            """
        )
        _record_schema_version(
            connection,
            5,
            "Invoice item line type column",
        )

    if current < 6:
        _backfill_line_types(connection)
        _record_schema_version(
            connection,
            6,
            "Backfill invoice item line types",
        )

    if current < 7:
        connection.executescript(
            """
            CREATE TABLE invoices_without_duplicate_constraint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL, archived_path TEXT NOT NULL,
                document_type TEXT NOT NULL DEFAULT '', supplier TEXT NOT NULL DEFAULT '',
                supplier_id TEXT NOT NULL DEFAULT '', invoice_number TEXT NOT NULL DEFAULT '',
                invoice_date TEXT NOT NULL DEFAULT '', due_date TEXT NOT NULL DEFAULT '',
                subtotal REAL, taxable_amount REAL, exempt_amount REAL, vat_rate REAL,
                vat REAL, total REAL, tax_treatment TEXT NOT NULL DEFAULT '',
                currency TEXT NOT NULL DEFAULT 'ILS', status TEXT NOT NULL DEFAULT 'approved',
                confidence REAL NOT NULL DEFAULT 0, machine_issues TEXT NOT NULL DEFAULT '[]',
                model_notes TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL,
                approved_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'לא מסווג', subcategory TEXT NOT NULL DEFAULT ''
            );
            INSERT INTO invoices_without_duplicate_constraint (
                id, file_name, archived_path, document_type, supplier, supplier_id,
                invoice_number, invoice_date, due_date, subtotal, taxable_amount,
                exempt_amount, vat_rate, vat, total, tax_treatment, currency, status,
                confidence, machine_issues, model_notes, created_at, approved_at,
                updated_at, category, subcategory
            )
            SELECT
                id, COALESCE(file_name, ''), COALESCE(archived_path, ''),
                COALESCE(document_type, ''), COALESCE(supplier, ''),
                COALESCE(supplier_id, ''), COALESCE(invoice_number, ''),
                COALESCE(invoice_date, ''), COALESCE(due_date, ''), subtotal,
                taxable_amount, exempt_amount, vat_rate, vat, total,
                COALESCE(tax_treatment, 'לא ברור'), COALESCE(currency, 'ILS'),
                COALESCE(status, 'approved'), COALESCE(confidence, 0),
                COALESCE(machine_issues, '[]'), COALESCE(model_notes, '[]'),
                COALESCE(created_at, ''), COALESCE(approved_at, ''),
                COALESCE(updated_at, ''), COALESCE(category, 'לא מסווג'),
                COALESCE(subcategory, '')
            FROM invoices;
            DROP TABLE invoices;
            ALTER TABLE invoices_without_duplicate_constraint RENAME TO invoices;
            CREATE INDEX idx_invoices_supplier ON invoices(supplier);
            CREATE INDEX idx_invoices_date ON invoices(invoice_date);
            CREATE INDEX idx_invoices_number ON invoices(invoice_number);
            """
        )
        _record_schema_version(
            connection,
            7,
            "Allow explicitly approved duplicate invoices",
        )

    if current < 8:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS canonical_suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name TEXT NOT NULL,
                vat_id TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_supplier_vat
            ON canonical_suppliers(vat_id)
            WHERE vat_id <> '';

            CREATE TABLE IF NOT EXISTS supplier_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_supplier_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                normalized_alias TEXT NOT NULL,
                source_invoice_id INTEGER,
                confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(canonical_supplier_id)
                    REFERENCES canonical_suppliers(id) ON DELETE CASCADE,
                FOREIGN KEY(source_invoice_id)
                    REFERENCES invoices(id) ON DELETE SET NULL,
                UNIQUE(canonical_supplier_id, alias)
            );

            CREATE TABLE IF NOT EXISTS canonical_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name TEXT NOT NULL,
                base_unit TEXT NOT NULL DEFAULT '',
                package_quantity REAL,
                package_unit TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS product_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_product_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                normalized_alias TEXT NOT NULL,
                source_item_id INTEGER,
                confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(canonical_product_id)
                    REFERENCES canonical_products(id) ON DELETE CASCADE,
                FOREIGN KEY(source_item_id)
                    REFERENCES invoice_items(id) ON DELETE SET NULL,
                UNIQUE(canonical_product_id, alias)
            );

            CREATE TABLE IF NOT EXISTS invoice_identity_links (
                invoice_id INTEGER PRIMARY KEY,
                canonical_supplier_id INTEGER NOT NULL,
                match_method TEXT NOT NULL,
                linked_at TEXT NOT NULL,
                FOREIGN KEY(invoice_id)
                    REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY(canonical_supplier_id)
                    REFERENCES canonical_suppliers(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS invoice_item_identity_links (
                item_id INTEGER PRIMARY KEY,
                canonical_product_id INTEGER NOT NULL,
                normalized_unit TEXT NOT NULL DEFAULT '',
                package_quantity REAL,
                package_unit TEXT NOT NULL DEFAULT '',
                match_method TEXT NOT NULL,
                linked_at TEXT NOT NULL,
                FOREIGN KEY(item_id)
                    REFERENCES invoice_items(id) ON DELETE CASCADE,
                FOREIGN KEY(canonical_product_id)
                    REFERENCES canonical_products(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS identity_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                source_canonical_id INTEGER,
                target_canonical_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,
                alias TEXT NOT NULL DEFAULT '',
                decided_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_supplier_alias_canonical
            ON supplier_aliases(canonical_supplier_id);

            CREATE INDEX IF NOT EXISTS idx_supplier_alias_normalized
            ON supplier_aliases(normalized_alias);

            CREATE INDEX IF NOT EXISTS idx_product_alias_canonical
            ON product_aliases(canonical_product_id);

            CREATE INDEX IF NOT EXISTS idx_product_alias_normalized
            ON product_aliases(normalized_alias);

            CREATE INDEX IF NOT EXISTS idx_invoice_supplier_identity
            ON invoice_identity_links(canonical_supplier_id);

            CREATE INDEX IF NOT EXISTS idx_item_product_identity
            ON invoice_item_identity_links(canonical_product_id);
            """
        )
        _record_schema_version(
            connection,
            8,
            "Canonical business identities and evidence links",
        )

    if current < 9:
        connection.executescript(
            """
            CREATE TABLE supplier_aliases_v9 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_supplier_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                normalized_alias TEXT NOT NULL,
                source_invoice_id INTEGER,
                confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(canonical_supplier_id)
                    REFERENCES canonical_suppliers(id) ON DELETE CASCADE,
                FOREIGN KEY(source_invoice_id)
                    REFERENCES invoices(id) ON DELETE SET NULL,
                UNIQUE(canonical_supplier_id, alias)
            );
            INSERT INTO supplier_aliases_v9
            SELECT * FROM supplier_aliases;
            DROP TABLE supplier_aliases;
            ALTER TABLE supplier_aliases_v9 RENAME TO supplier_aliases;

            CREATE TABLE product_aliases_v9 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_product_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                normalized_alias TEXT NOT NULL,
                source_item_id INTEGER,
                confirmed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(canonical_product_id)
                    REFERENCES canonical_products(id) ON DELETE CASCADE,
                FOREIGN KEY(source_item_id)
                    REFERENCES invoice_items(id) ON DELETE SET NULL,
                UNIQUE(canonical_product_id, alias)
            );
            INSERT INTO product_aliases_v9
            SELECT * FROM product_aliases;
            DROP TABLE product_aliases;
            ALTER TABLE product_aliases_v9 RENAME TO product_aliases;

            CREATE INDEX idx_supplier_alias_canonical
            ON supplier_aliases(canonical_supplier_id);
            CREATE INDEX idx_supplier_alias_normalized
            ON supplier_aliases(normalized_alias);
            CREATE INDEX idx_product_alias_canonical
            ON product_aliases(canonical_product_id);
            CREATE INDEX idx_product_alias_normalized
            ON product_aliases(normalized_alias);
            """
        )
        _record_schema_version(
            connection,
            9,
            "Preserve every observed supplier and product alias",
        )

    if current < 10:
        connection.executescript(
            """
            ALTER TABLE canonical_suppliers ADD COLUMN active INTEGER NOT NULL DEFAULT 1;
            ALTER TABLE canonical_suppliers ADD COLUMN merged_into_id INTEGER;
            ALTER TABLE canonical_products ADD COLUMN active INTEGER NOT NULL DEFAULT 1;
            ALTER TABLE canonical_products ADD COLUMN merged_into_id INTEGER;

            ALTER TABLE identity_decisions ADD COLUMN actor TEXT NOT NULL DEFAULT 'Barni user';
            ALTER TABLE identity_decisions ADD COLUMN reason TEXT NOT NULL DEFAULT '';
            ALTER TABLE identity_decisions ADD COLUMN evidence_json TEXT NOT NULL DEFAULT '{}';
            ALTER TABLE identity_decisions ADD COLUMN previous_state_json TEXT NOT NULL DEFAULT '{}';
            ALTER TABLE identity_decisions ADD COLUMN current_state_json TEXT NOT NULL DEFAULT '{}';
            ALTER TABLE identity_decisions ADD COLUMN reversed_at TEXT;
            ALTER TABLE identity_decisions ADD COLUMN reversal_decision_id INTEGER;

            CREATE TABLE identity_review_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_key TEXT NOT NULL UNIQUE,
                entity_type TEXT NOT NULL,
                review_type TEXT NOT NULL,
                source_canonical_id INTEGER NOT NULL,
                target_canonical_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                explanation TEXT NOT NULL,
                confidence REAL NOT NULL,
                priority INTEGER NOT NULL,
                reasons_json TEXT NOT NULL DEFAULT '[]',
                evidence_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                resolution_decision_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT,
                CHECK(status IN ('pending', 'confirmed', 'rejected', 'superseded'))
            );

            CREATE INDEX idx_identity_review_queue
            ON identity_review_candidates(status, priority DESC, confidence DESC);
            CREATE INDEX idx_identity_decision_reversible
            ON identity_decisions(reversed_at, decided_at DESC);
            """
        )
        _record_schema_version(
            connection,
            10,
            "Reversible identity decisions and evidence-backed review queue",
        )

    if current < 11:
        connection.executescript(
            """
            CREATE TABLE business_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_type TEXT NOT NULL,
                fingerprint TEXT NOT NULL UNIQUE,
                source_type TEXT NOT NULL,
                source_record_id INTEGER NOT NULL,
                trust_status TEXT NOT NULL,
                business_confidence REAL NOT NULL,
                status_explanation TEXT NOT NULL,
                confidence_json TEXT NOT NULL DEFAULT '{}',
                evidence_json TEXT NOT NULL DEFAULT '{}',
                payload_json TEXT NOT NULL DEFAULT '{}',
                observed_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK(trust_status IN (
                    'TRUSTED', 'PARTIALLY TRUSTED', 'INSUFFICIENT DATA',
                    'IDENTITY CONFLICT', 'UNIT CONFLICT', 'PACKAGE CONFLICT',
                    'VAT CONFLICT', 'CURRENCY CONFLICT', 'NOT COMPARABLE'
                ))
            );

            CREATE TABLE comparable_price_facts (
                fact_id INTEGER PRIMARY KEY,
                canonical_product_id INTEGER,
                canonical_supplier_id INTEGER,
                invoice_id INTEGER NOT NULL,
                invoice_item_id INTEGER NOT NULL UNIQUE,
                observed_price REAL,
                normalized_price REAL,
                normalized_unit TEXT NOT NULL DEFAULT '',
                package_quantity REAL,
                package_unit TEXT NOT NULL DEFAULT '',
                quantity REAL,
                vat_basis TEXT NOT NULL DEFAULT '',
                currency TEXT NOT NULL DEFAULT '',
                observation_date TEXT NOT NULL DEFAULT '',
                document_type TEXT NOT NULL DEFAULT '',
                is_credit INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(fact_id) REFERENCES business_facts(id) ON DELETE CASCADE,
                FOREIGN KEY(canonical_product_id) REFERENCES canonical_products(id) ON DELETE RESTRICT,
                FOREIGN KEY(canonical_supplier_id) REFERENCES canonical_suppliers(id) ON DELETE RESTRICT,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY(invoice_item_id) REFERENCES invoice_items(id) ON DELETE CASCADE
            );

            CREATE INDEX idx_business_facts_type_status
            ON business_facts(fact_type, trust_status, observed_at);
            CREATE INDEX idx_price_facts_product_date
            ON comparable_price_facts(canonical_product_id, observation_date, invoice_id);
            CREATE INDEX idx_price_facts_supplier
            ON comparable_price_facts(canonical_supplier_id, observation_date);
            """
        )
        _record_schema_version(
            connection,
            11,
            "Trusted Business Facts Engine and comparable price ledger",
        )


def init_database(path: Path | None = None) -> None:
    db_path = path or (root_dir() / "invoice_archive.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    had_existing_database = db_path.exists() and db_path.stat().st_size > 0

    # First open: ensure the base schema exists and inspect the version.
    connection = connect(db_path)
    try:
        connection.commit()
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
                tax_treatment TEXT NOT NULL DEFAULT '',
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
                line_type TEXT NOT NULL DEFAULT 'product',
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

        current_version = _current_schema_version(connection)
    finally:
        connection.close()

    # Back up only when a structural upgrade is actually needed.
    if current_version < 11 and had_existing_database:
        _backup_database(db_path)

    # Second open: run the migration in one explicit transaction.
    connection = connect(db_path)
    try:
        if current_version < 11:
            connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN")
        _run_migrations(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")
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


def duplicate_invoice(
    supplier_id: str,
    invoice_number: str,
    document_type: str,
) -> dict | None:
    if not invoice_number:
        return None
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id, supplier, supplier_id, invoice_number, document_type,
                   invoice_date, total, archived_path
            FROM invoices
            WHERE supplier_id = ? AND invoice_number = ? AND document_type = ?
            ORDER BY id DESC LIMIT 1
            """,
            (_text(supplier_id), _text(invoice_number), _text(document_type)),
        ).fetchone()
    return dict(row) if row else None


def replace_duplicate_invoice(
    invoice_id: int,
    source_file: Path,
    document: dict,
) -> int:
    """Replace an approved invoice while retaining its ID and audit history."""
    destination = archive_destination(source_file, _text(document.get("invoice_date")))
    shutil.copy2(source_file, destination)
    now = datetime.now().isoformat(timespec="seconds")
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
        "confidence": _number(document.get("confidence")) or 0.0,
        "machine_issues": json.dumps(document.get("machine_issues", []), ensure_ascii=False),
        "model_notes": json.dumps(document.get("model_notes", []), ensure_ascii=False),
        "updated_at": now,
    }
    try:
        with connect() as connection:
            current = connection.execute(
                "SELECT id FROM invoices WHERE id = ?", (invoice_id,)
            ).fetchone()
            if current is None:
                raise ValueError("החשבונית הקיימת לא נמצאה.")
            assignments = ", ".join(f"{field} = :{field}" for field in values)
            connection.execute(
                f"UPDATE invoices SET {assignments} WHERE id = :invoice_id",
                {**values, "invoice_id": invoice_id},
            )
            connection.execute(
                """
                INSERT INTO invoice_history (
                    invoice_id, changed_at, field_name, old_value, new_value
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (invoice_id, now, "duplicate_resolution", "existing", "replaced"),
            )
            connection.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            for item in document.get("items", []) or []:
                connection.execute(
                    """
                    INSERT INTO invoice_items (
                        invoice_id, item_code, description, quantity, unit,
                        unit_price, line_total, line_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id, _text(item.get("item_code")),
                        _text(item.get("description")), _number(item.get("quantity")),
                        _text(item.get("unit")), _number(item.get("unit_price")),
                        _number(item.get("line_total")),
                        classify_invoice_line(_text(item.get("description"))),
                    ),
                )
            connection.commit()
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    source_file.unlink(missing_ok=True)
    return invoice_id


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
                    invoice_id,
                    item_code,
                    description,
                    quantity,
                    unit,
                    unit_price,
                    line_total,
                    line_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    _text(item.get("item_code")),
                    _text(item.get("description")),
                    _number(item.get("quantity")),
                    _text(item.get("unit")),
                    _number(item.get("unit_price")),
                    _number(item.get("line_total")),
                    classify_invoice_line(_text(item.get("description"))),
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
                    unit, unit_price, line_total, line_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    _text(item.get("item_code")),
                    _text(item.get("description")),
                    _number(item.get("quantity")),
                    _text(item.get("unit")),
                    _number(item.get("unit_price")),
                    _number(item.get("line_total")),
                    classify_invoice_line(_text(item.get("description"))),
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
                OR canonical_suppliers.canonical_name LIKE ?
                OR EXISTS (
                    SELECT 1 FROM supplier_aliases
                    WHERE supplier_aliases.canonical_supplier_id = canonical_suppliers.id
                      AND supplier_aliases.alias LIKE ?
                )
                OR invoices.invoice_number LIKE ?
                OR invoices.supplier_id LIKE ?
                OR EXISTS (
                    SELECT 1 FROM invoice_items
                    LEFT JOIN invoice_item_identity_links
                      ON invoice_item_identity_links.item_id = invoice_items.id
                    LEFT JOIN canonical_products
                      ON canonical_products.id = invoice_item_identity_links.canonical_product_id
                    WHERE invoice_items.invoice_id = invoices.id
                    AND (
                        invoice_items.description LIKE ?
                        OR invoice_items.item_code LIKE ?
                        OR canonical_products.canonical_name LIKE ?
                        OR EXISTS (
                            SELECT 1 FROM product_aliases
                            WHERE product_aliases.canonical_product_id = canonical_products.id
                              AND product_aliases.alias LIKE ?
                        )
                    )
                )
            )
            """
        )
        token = f"%{free_text}%"
        params.extend([token] * 9)

    if supplier_query:
        clauses.append(
            """
            (
                invoices.supplier LIKE ?
                OR canonical_suppliers.canonical_name LIKE ?
                OR EXISTS (
                    SELECT 1 FROM supplier_aliases
                    WHERE supplier_aliases.canonical_supplier_id = canonical_suppliers.id
                      AND supplier_aliases.alias LIKE ?
                )
            )
            """
        )
        params.extend([f"%{supplier_query}%"] * 3)

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
        SELECT invoices.*,
               invoice_identity_links.canonical_supplier_id,
               canonical_suppliers.canonical_name AS canonical_supplier_name
        FROM invoices
        LEFT JOIN invoice_identity_links
          ON invoice_identity_links.invoice_id = invoices.id
        LEFT JOIN canonical_suppliers
          ON canonical_suppliers.id = invoice_identity_links.canonical_supplier_id
        WHERE {' AND '.join(clauses)}
        ORDER BY {order_column} {direction}, invoices.supplier ASC
    """
    with connect() as connection:
        return pd.read_sql_query(sql, connection, params=params)


def invoice_items(invoice_id: int) -> pd.DataFrame:
    with connect() as connection:
        return pd.read_sql_query(
            """
            SELECT invoice_items.id, invoice_items.invoice_id,
                   invoice_items.item_code, invoice_items.description,
                   invoice_items.quantity, invoice_items.unit,
                   invoice_items.unit_price, invoice_items.line_total,
                   invoice_items.line_type,
                   invoice_item_identity_links.canonical_product_id,
                   canonical_products.canonical_name AS canonical_product_name,
                   invoice_item_identity_links.normalized_unit,
                   invoice_item_identity_links.package_quantity,
                   invoice_item_identity_links.package_unit
            FROM invoice_items
            LEFT JOIN invoice_item_identity_links
              ON invoice_item_identity_links.item_id = invoice_items.id
            LEFT JOIN canonical_products
              ON canonical_products.id = invoice_item_identity_links.canonical_product_id
            WHERE invoice_items.invoice_id = ?
            ORDER BY invoice_items.id
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


def _normalize_description(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value).lower()).strip()


def product_price_history(
    description: str,
    path: Path | None = None,
    supplier: str | None = None,
) -> pd.DataFrame:
    normalized = _normalize_description(description)
    if not normalized:
        return pd.DataFrame(
            columns=[
                "invoice_date",
                "supplier",
                "invoice_number",
                "description",
                "unit_price",
                "quantity",
                "unit",
                "line_total",
                "invoice_id",
                "item_id",
                "previous_price",
                "price_difference",
                "price_change_pct",
            ]
        )

    with connect(path) as connection:
        identity = connection.execute(
            """SELECT canonical_products.id
               FROM canonical_products
               LEFT JOIN product_aliases ON product_aliases.canonical_product_id = canonical_products.id
               WHERE canonical_products.active = 1
                 AND (lower(trim(canonical_products.canonical_name)) = lower(trim(?))
                      OR lower(trim(product_aliases.alias)) = lower(trim(?)))
               LIMIT 1""",
            (_text(description), _text(description)),
        ).fetchone()
    if identity is None:
        return pd.DataFrame()
    return canonical_product_price_history(int(identity["id"]), path, supplier=supplier)


def canonical_product_price_history(
    canonical_product_id: int,
    path: Path | None = None,
    supplier: str | None = None,
) -> pd.DataFrame:
    from services.business_facts import ComparablePriceLedger

    factory = (lambda: connect(path)) if path is not None else connect
    ledger = ComparablePriceLedger(factory)
    ledger.sync()
    facts = ledger.history(canonical_product_id, trusted_only=True, ensure=False)
    if supplier:
        needle = _text(supplier).casefold()
        facts = [value for value in facts if value.canonical_supplier_name.casefold() == needle]
    rows = []
    for index, fact in enumerate(facts):
        previous = next(
            (
                candidate for candidate in reversed(facts[:index])
                if ledger.compare(fact, candidate).comparable
            ),
            None,
        )
        comparison = ledger.compare(fact, previous) if previous is not None else None
        rows.append({
            "invoice_date": fact.observation_date,
            "supplier": fact.canonical_supplier_name,
            "canonical_supplier_id": fact.canonical_supplier_id,
            "canonical_supplier_name": fact.canonical_supplier_name,
            "invoice_number": "",
            "description": fact.canonical_product_name,
            "canonical_product_id": fact.canonical_product_id,
            "canonical_product_name": fact.canonical_product_name,
            "unit_price": fact.normalized_price,
            "observed_price": fact.observed_price,
            "quantity": fact.quantity,
            "unit": fact.normalized_unit,
            "normalized_unit": fact.normalized_unit,
            "package_quantity": fact.package_quantity,
            "package_unit": fact.package_unit,
            "vat_basis": fact.vat_basis,
            "currency": fact.currency,
            "fact_status": fact.fact.trust_status,
            "business_confidence": fact.fact.business_confidence,
            "status_explanation": fact.fact.status_explanation,
            "line_total": None,
            "invoice_id": fact.invoice_id,
            "item_id": fact.invoice_item_id,
            "previous_price": previous.normalized_price if previous else None,
            "price_difference": comparison.change_amount if comparison else None,
            "price_change_pct": round(comparison.change_pct, 2) if comparison else None,
        })
    return pd.DataFrame(rows)


def product_price_change_summary(
    description: str,
    path: Path | None = None,
    supplier: str | None = None,
) -> dict[str, Any]:
    history = product_price_history(description, path=path, supplier=supplier)
    if history.empty:
        return {
            "description": _text(description),
            "purchase_count": 0,
            "current_price": None,
            "previous_price": None,
            "price_difference": None,
            "price_change_pct": None,
            "latest_quantity": None,
            "savings_extra_cost": None,
            "latest_purchase_date": None,
            "previous_purchase_date": None,
        }

    latest = history.iloc[-1]
    previous = history.iloc[-2] if len(history) > 1 else None
    latest_quantity = (
        None if pd.isna(latest["quantity"]) else float(latest["quantity"])
    )
    price_difference = (
        None
        if pd.isna(latest["price_difference"])
        else float(latest["price_difference"])
    )

    return {
        "description": _text(description),
        "purchase_count": int(len(history)),
        "current_price": None if pd.isna(latest["unit_price"]) else float(latest["unit_price"]),
        "previous_price": None if previous is None or pd.isna(previous["unit_price"]) else float(previous["unit_price"]),
        "price_difference": price_difference,
        "price_change_pct": None if pd.isna(latest["price_change_pct"]) else float(latest["price_change_pct"]),
        "latest_quantity": latest_quantity,
        "savings_extra_cost": (
            None
            if price_difference is None or latest_quantity is None
            else price_difference * latest_quantity
        ),
        "latest_purchase_date": None if pd.isna(latest["invoice_date"]) else str(latest["invoice_date"]),
        "previous_purchase_date": None if previous is None or pd.isna(previous["invoice_date"]) else str(previous["invoice_date"]),
    }


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
              AND invoice_items.line_type = 'product'
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

    parsed = any(
        [supplier, min_total is not None, max_total is not None, start_date, free_text]
    )
    if not parsed:
        return pd.DataFrame()

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
