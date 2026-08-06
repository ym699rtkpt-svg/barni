from __future__ import annotations

from datetime import datetime
from typing import Any

from database import connect


class KnowledgeRepository:
    """Central database access layer for business knowledge."""

    def ensure_schema(self) -> None:
        with connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS supplier_memory (
                    supplier_key TEXT PRIMARY KEY,
                    supplier_name TEXT NOT NULL DEFAULT '',
                    supplier_id TEXT NOT NULL DEFAULT '',
                    invoice_count INTEGER NOT NULL DEFAULT 0,
                    total_spend REAL NOT NULL DEFAULT 0,
                    first_purchase TEXT NOT NULL DEFAULT '',
                    last_purchase TEXT NOT NULL DEFAULT '',
                    last_invoice_id INTEGER,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def upsert_supplier_memory(
        self,
        *,
        supplier_name: str,
        supplier_id: str,
        invoice_id: int | None,
        invoice_date: str,
        total: float | None,
    ) -> None:
        self.ensure_schema()

        supplier_name = str(supplier_name or "").strip()
        supplier_id = str(supplier_id or "").strip()
        supplier_key = supplier_id or supplier_name.lower()

        if not supplier_key:
            raise ValueError("Cannot update supplier memory without supplier identity.")

        amount = float(total or 0)
        now = datetime.now().isoformat(timespec="seconds")

        with connect() as connection:
            connection.execute(
                """
                INSERT INTO supplier_memory (
                    supplier_key,
                    supplier_name,
                    supplier_id,
                    invoice_count,
                    total_spend,
                    first_purchase,
                    last_purchase,
                    last_invoice_id,
                    updated_at
                )
                VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)
                ON CONFLICT(supplier_key) DO UPDATE SET
                    supplier_name = excluded.supplier_name,
                    supplier_id = excluded.supplier_id,
                    invoice_count = supplier_memory.invoice_count + 1,
                    total_spend = supplier_memory.total_spend + excluded.total_spend,
                    first_purchase = CASE
                        WHEN supplier_memory.first_purchase = ''
                        THEN excluded.first_purchase
                        WHEN excluded.first_purchase = ''
                        THEN supplier_memory.first_purchase
                        WHEN excluded.first_purchase < supplier_memory.first_purchase
                        THEN excluded.first_purchase
                        ELSE supplier_memory.first_purchase
                    END,
                    last_purchase = CASE
                        WHEN excluded.last_purchase > supplier_memory.last_purchase
                        THEN excluded.last_purchase
                        ELSE supplier_memory.last_purchase
                    END,
                    last_invoice_id = excluded.last_invoice_id,
                    updated_at = excluded.updated_at
                """,
                (
                    supplier_key,
                    supplier_name,
                    supplier_id,
                    amount,
                    invoice_date,
                    invoice_date,
                    invoice_id,
                    now,
                ),
            )
            connection.commit()

    def get_supplier_memory(self, supplier_key: str) -> dict[str, Any] | None:
        self.ensure_schema()

        with connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM supplier_memory
                WHERE supplier_key = ?
                """,
                (supplier_key,),
            ).fetchone()

        return dict(row) if row else None
