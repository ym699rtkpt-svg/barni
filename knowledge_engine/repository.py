from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import sqlite3

from database import connect


class KnowledgeRepository:
    """Central database access layer for business knowledge."""

    def __init__(
        self,
        connection_factory: Callable[[], sqlite3.Connection] = connect,
    ) -> None:
        self._connect = connection_factory

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
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
                );

                CREATE TABLE IF NOT EXISTS supplier_memory_events (
                    invoice_id INTEGER PRIMARY KEY,
                    supplier_key TEXT NOT NULL,
                    processed_at TEXT NOT NULL
                );
                """
            )
            connection.commit()

    @staticmethod
    def supplier_key(
        supplier_name: str,
        supplier_id: str,
    ) -> str:
        clean_name = str(supplier_name or "").strip()
        clean_id = str(supplier_id or "").strip()
        return clean_id or clean_name.casefold()

    def upsert_supplier_memory(
        self,
        *,
        supplier_name: str,
        supplier_id: str,
        invoice_id: int,
        invoice_date: str,
        total: float | None,
    ) -> bool:
        self.ensure_schema()

        key = self.supplier_key(supplier_name, supplier_id)
        if not key:
            raise ValueError(
                "Cannot update supplier memory without supplier identity."
            )

        if invoice_id is None:
            raise ValueError(
                "Cannot update supplier memory without invoice_id."
            )

        clean_name = str(supplier_name or "").strip()
        clean_id = str(supplier_id or "").strip()
        clean_date = str(invoice_date or "").strip()
        amount = float(total or 0)
        now = datetime.now().isoformat(timespec="seconds")

        with self._connect() as connection:
            event_cursor = connection.execute(
                """
                INSERT OR IGNORE INTO supplier_memory_events (
                    invoice_id,
                    supplier_key,
                    processed_at
                )
                VALUES (?, ?, ?)
                """,
                (invoice_id, key, now),
            )

            if event_cursor.rowcount == 0:
                return False

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
                    total_spend = (
                        supplier_memory.total_spend
                        + excluded.total_spend
                    ),
                    first_purchase = CASE
                        WHEN supplier_memory.first_purchase = ''
                        THEN excluded.first_purchase
                        WHEN excluded.first_purchase = ''
                        THEN supplier_memory.first_purchase
                        WHEN (
                            excluded.first_purchase
                            < supplier_memory.first_purchase
                        )
                        THEN excluded.first_purchase
                        ELSE supplier_memory.first_purchase
                    END,
                    last_purchase = CASE
                        WHEN (
                            excluded.last_purchase
                            > supplier_memory.last_purchase
                        )
                        THEN excluded.last_purchase
                        ELSE supplier_memory.last_purchase
                    END,
                    last_invoice_id = excluded.last_invoice_id,
                    updated_at = excluded.updated_at
                """,
                (
                    key,
                    clean_name,
                    clean_id,
                    amount,
                    clean_date,
                    clean_date,
                    invoice_id,
                    now,
                ),
            )
            connection.commit()

        return True

    def get_supplier_memory(
        self,
        supplier_key: str,
    ) -> dict[str, Any] | None:
        self.ensure_schema()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM supplier_memory
                WHERE supplier_key = ?
                """,
                (supplier_key,),
            ).fetchone()

        return dict(row) if row else None
