from __future__ import annotations

import re
import json
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from database import connect
from knowledge_engine.line_classifier import is_product_line


def normalize_identity_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = text.replace("׳", "'").replace("״", '"')
    text = re.sub(r"[^\w\u0590-\u05ff]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def normalize_vat_id(value: Any) -> str:
    return "".join(re.findall(r"\d", str(value or "")))


_UNIT_ALIASES = {
    "kg": "kg", "kilogram": "kg", "kilograms": "kg", "קג": "kg", "קילו": "kg",
    "g": "g", "gram": "g", "grams": "g", "גרם": "g",
    "l": "l", "liter": "l", "litre": "l", "liters": "l", "litres": "l", "ליטר": "l",
    "ml": "ml", "milliliter": "ml", "millilitre": "ml", "מל": "ml",
    "unit": "unit", "units": "unit", "piece": "unit", "pieces": "unit", "pcs": "unit",
    "יח": "unit", "יחידה": "unit", "יחידות": "unit",
    "pack": "package", "package": "package", "אריזה": "package", "מארז": "package",
}


def normalize_unit(value: Any) -> str:
    normalized = normalize_identity_text(value).replace(" ", "")
    return _UNIT_ALIASES.get(normalized, normalized)


def normalize_currency(value: Any) -> str:
    compact = str(value or "").strip().casefold()
    compact = compact.replace(" ", "").replace('"', "").replace("״", "")
    aliases = {
        "ils": "ILS", "nis": "ILS", "₪": "ILS", "שח": "ILS",
        "שקל": "ILS", "שקלים": "ILS", "$": "USD", "usd": "USD",
        "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP",
    }
    return aliases.get(compact, compact.upper())


@dataclass(frozen=True)
class PackagingObservation:
    quantity: float | None = None
    unit: str = ""


_PACKAGE_PATTERN = re.compile(
    r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|ק[\"״']?ג|קילו|g|grams?|גרם|l|lit(?:er|re)s?|ליטר|ml|millilit(?:er|re)s?|מ[\"״']?ל|packs?|packages?|אריז(?:ה|ות)|מארזים?)(?!\w)",
    re.IGNORECASE,
)


def normalize_packaging(description: Any, unit: Any = "") -> PackagingObservation:
    match = _PACKAGE_PATTERN.search(str(description or ""))
    if match:
        quantity = float(match.group(1).replace(",", "."))
        package_unit = normalize_unit(match.group(2))
        if package_unit in {"packs", "packages", "אריזות", "מארזים"}:
            package_unit = "package"
        return PackagingObservation(quantity=quantity, unit=package_unit)
    normalized = normalize_unit(unit)
    return PackagingObservation(unit=normalized if normalized in {"kg", "g", "l", "ml"} else "")


@dataclass(frozen=True)
class CanonicalSupplier:
    id: int
    canonical_name: str
    vat_id: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalProduct:
    id: int
    canonical_name: str
    base_unit: str
    package_quantity: float | None
    package_unit: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class InvoiceEvidence:
    source_record_id: int | str
    invoice_id: int | None
    supplier: str
    invoice_number: str
    invoice_date: str
    total: float | None
    document_type: str
    archived_path: str

    @property
    def label(self) -> str:
        supplier = self.supplier or "Missing supplier"
        number = f"Invoice #{self.invoice_number}" if self.invoice_number else "No invoice number"
        return f"{supplier} · {number}"


class BusinessIdentityRepository:
    def __init__(
        self,
        connection_factory: Callable[[], sqlite3.Connection] = connect,
    ) -> None:
        self._connect = connection_factory

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def sync_existing_memory(self) -> dict[str, int]:
        supplier_links = 0
        product_links = 0
        with self._connect() as connection:
            invoices = connection.execute(
                """
                SELECT invoices.* FROM invoices
                LEFT JOIN invoice_identity_links
                  ON invoice_identity_links.invoice_id = invoices.id
                WHERE invoice_identity_links.invoice_id IS NULL
                ORDER BY invoices.id
                """
            ).fetchall()
            for invoice in invoices:
                self._link_supplier(connection, dict(invoice))
                supplier_links += 1

            items = connection.execute(
                """
                SELECT invoice_items.* FROM invoice_items
                LEFT JOIN invoice_item_identity_links
                  ON invoice_item_identity_links.item_id = invoice_items.id
                WHERE invoice_item_identity_links.item_id IS NULL
                ORDER BY invoice_items.invoice_id, invoice_items.id
                """
            ).fetchall()
            for item in items:
                if not is_product_line(dict(item)):
                    continue
                if not normalize_identity_text(item["description"]):
                    continue
                self._link_product(connection, dict(item))
                product_links += 1

            observations = connection.execute(
                """
                SELECT invoice_items.id, invoice_items.description, invoice_items.quantity,
                       invoice_items.unit, invoice_items.unit_price,
                       invoice_items.line_total, invoice_items.line_type,
                       links.canonical_product_id, links.normalized_unit,
                       links.package_quantity, links.package_unit,
                       products.base_unit canonical_base_unit,
                       products.package_quantity canonical_package_quantity,
                       products.package_unit canonical_package_unit
                FROM invoice_items
                JOIN invoice_item_identity_links links ON links.item_id = invoice_items.id
                JOIN canonical_products products ON products.id = links.canonical_product_id
                """
            ).fetchall()
            for row in observations:
                if not is_product_line(dict(row)):
                    continue
                normalized_unit = normalize_unit(row["unit"])
                packaging = normalize_packaging(row["description"], row["unit"])
                if (
                    normalized_unit != row["normalized_unit"]
                    or packaging.quantity != row["package_quantity"]
                    or packaging.unit != row["package_unit"]
                ):
                    connection.execute(
                        """UPDATE invoice_item_identity_links
                           SET normalized_unit = ?, package_quantity = ?, package_unit = ?, linked_at = ?
                           WHERE item_id = ?""",
                        (normalized_unit, packaging.quantity, packaging.unit, self._now(), row["id"]),
                    )
                if (
                    (not row["canonical_base_unit"] and normalized_unit)
                    or (row["canonical_package_quantity"] is None and packaging.quantity is not None)
                    or (not row["canonical_package_unit"] and packaging.unit)
                ):
                    connection.execute(
                        """UPDATE canonical_products
                           SET base_unit = CASE WHEN base_unit = '' THEN ? ELSE base_unit END,
                               package_quantity = COALESCE(package_quantity, ?),
                               package_unit = CASE WHEN package_unit = '' THEN ? ELSE package_unit END
                           WHERE id = ?""",
                        (normalized_unit, packaging.quantity, packaging.unit, row["canonical_product_id"]),
                    )

            # Preserve every raw spelling as evidence, including variants that
            # normalize to the same identity key.
            now = self._now()
            supplier_aliases = connection.execute(
                """
                SELECT invoices.id, invoices.supplier,
                       invoice_identity_links.canonical_supplier_id
                FROM invoices
                JOIN invoice_identity_links
                  ON invoice_identity_links.invoice_id = invoices.id
                """
            ).fetchall()
            for row in supplier_aliases:
                alias = str(row["supplier"] or "").strip()
                normalized = normalize_identity_text(alias)
                if normalized:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO supplier_aliases (
                            canonical_supplier_id, alias, normalized_alias,
                            source_invoice_id, confirmed, created_at
                        ) VALUES (?, ?, ?, ?, 0, ?)
                        """,
                        (row["canonical_supplier_id"], alias, normalized, row["id"], now),
                    )

            product_aliases = connection.execute(
                """
                SELECT invoice_items.id, invoice_items.description,
                       invoice_items.quantity, invoice_items.unit_price,
                       invoice_items.line_total, invoice_items.line_type,
                       invoice_item_identity_links.canonical_product_id
                FROM invoice_items
                JOIN invoice_item_identity_links
                  ON invoice_item_identity_links.item_id = invoice_items.id
                """
            ).fetchall()
            for row in product_aliases:
                if not is_product_line(dict(row)):
                    continue
                alias = str(row["description"] or "").strip()
                normalized = normalize_identity_text(alias)
                if normalized:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO product_aliases (
                            canonical_product_id, alias, normalized_alias,
                            source_item_id, confirmed, created_at
                        ) VALUES (?, ?, ?, ?, 0, ?)
                        """,
                        (row["canonical_product_id"], alias, normalized, row["id"], now),
                    )
            connection.commit()
        return {"supplier_links": supplier_links, "product_links": product_links}

    def learn_invoice(self, invoice_id: int) -> None:
        with self._connect() as connection:
            invoice = connection.execute(
                "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
            ).fetchone()
            if invoice is None:
                raise ValueError("Invoice evidence was not found.")
            self._link_supplier(connection, dict(invoice))
            items = connection.execute(
                "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id",
                (invoice_id,),
            ).fetchall()
            for item in items:
                if (
                    is_product_line(dict(item))
                    and normalize_identity_text(item["description"])
                ):
                    self._link_product(connection, dict(item))
            connection.commit()

    def _link_supplier(self, connection: sqlite3.Connection, invoice: Mapping[str, Any]) -> int:
        invoice_id = int(invoice["id"])
        name = str(invoice.get("supplier") or "").strip()
        alias_key = normalize_identity_text(name)
        vat_id = normalize_vat_id(invoice.get("supplier_id"))
        row = None
        method = "exact_alias"
        if vat_id:
            row = connection.execute(
                "SELECT * FROM canonical_suppliers WHERE vat_id = ? AND active = 1", (vat_id,)
            ).fetchone()
            method = "vat_id"
        if row is None and alias_key:
            row = connection.execute(
                """
                SELECT canonical_suppliers.* FROM supplier_aliases
                JOIN canonical_suppliers
                  ON canonical_suppliers.id = supplier_aliases.canonical_supplier_id
                WHERE supplier_aliases.normalized_alias = ?
                  AND canonical_suppliers.active = 1
                """,
                (alias_key,),
            ).fetchone()
        now = self._now()
        if row is None:
            cursor = connection.execute(
                """
                INSERT INTO canonical_suppliers (
                    canonical_name, vat_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?)
                """,
                (name or "Missing supplier", vat_id, now, now),
            )
            canonical_id = int(cursor.lastrowid)
            method = "new_identity"
        else:
            canonical_id = int(row["id"])
            if vat_id and not str(row["vat_id"] or ""):
                collision = connection.execute(
                    "SELECT id FROM canonical_suppliers WHERE vat_id = ? AND id <> ?",
                    (vat_id, canonical_id),
                ).fetchone()
                if collision is None:
                    connection.execute(
                        "UPDATE canonical_suppliers SET vat_id = ?, updated_at = ? WHERE id = ?",
                        (vat_id, now, canonical_id),
                    )
        if alias_key:
            connection.execute(
                """
                INSERT OR IGNORE INTO supplier_aliases (
                    canonical_supplier_id, alias, normalized_alias,
                    source_invoice_id, confirmed, created_at
                ) VALUES (?, ?, ?, ?, 0, ?)
                """,
                (canonical_id, name, alias_key, invoice_id, now),
            )
        connection.execute(
            """
            INSERT INTO invoice_identity_links (
                invoice_id, canonical_supplier_id, match_method, linked_at
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(invoice_id) DO UPDATE SET
                canonical_supplier_id = excluded.canonical_supplier_id,
                match_method = excluded.match_method,
                linked_at = excluded.linked_at
            """,
            (invoice_id, canonical_id, method, now),
        )
        return canonical_id

    def _link_product(self, connection: sqlite3.Connection, item: Mapping[str, Any]) -> int:
        item_id = int(item["id"])
        description = str(item.get("description") or "").strip()
        alias_key = normalize_identity_text(description)
        if not alias_key:
            raise ValueError("Cannot create a product identity without a description.")
        row = connection.execute(
            """
            SELECT canonical_products.* FROM product_aliases
            JOIN canonical_products
              ON canonical_products.id = product_aliases.canonical_product_id
            WHERE product_aliases.normalized_alias = ?
            """,
            (alias_key,),
        ).fetchone()
        normalized_unit = normalize_unit(item.get("unit"))
        packaging = normalize_packaging(description, item.get("unit"))
        now = self._now()
        if row is None:
            cursor = connection.execute(
                """
                INSERT INTO canonical_products (
                    canonical_name, base_unit, package_quantity, package_unit,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    description,
                    normalized_unit,
                    packaging.quantity,
                    packaging.unit,
                    now,
                    now,
                ),
            )
            canonical_id = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO product_aliases (
                    canonical_product_id, alias, normalized_alias,
                    source_item_id, confirmed, created_at
                ) VALUES (?, ?, ?, ?, 0, ?)
                """,
                (canonical_id, description, alias_key, item_id, now),
            )
            method = "new_identity"
        else:
            canonical_id = int(row["id"])
            method = "exact_alias"
        connection.execute(
            """
            INSERT INTO invoice_item_identity_links (
                item_id, canonical_product_id, normalized_unit,
                package_quantity, package_unit, match_method, linked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                canonical_product_id = excluded.canonical_product_id,
                normalized_unit = excluded.normalized_unit,
                package_quantity = excluded.package_quantity,
                package_unit = excluded.package_unit,
                match_method = excluded.match_method,
                linked_at = excluded.linked_at
            """,
            (
                item_id,
                canonical_id,
                normalized_unit,
                packaging.quantity,
                packaging.unit,
                method,
                now,
            ),
        )
        return canonical_id

    def suppliers(self) -> list[CanonicalSupplier]:
        self.sync_existing_memory()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM canonical_suppliers WHERE active = 1 ORDER BY canonical_name COLLATE NOCASE"
            ).fetchall()
            aliases = connection.execute(
                "SELECT canonical_supplier_id, alias FROM supplier_aliases ORDER BY alias COLLATE NOCASE"
            ).fetchall()
        grouped: dict[int, list[str]] = {}
        for alias in aliases:
            grouped.setdefault(int(alias["canonical_supplier_id"]), []).append(alias["alias"])
        return [
            CanonicalSupplier(
                id=int(row["id"]),
                canonical_name=row["canonical_name"],
                vat_id=row["vat_id"],
                aliases=tuple(grouped.get(int(row["id"]), [])),
            )
            for row in rows
        ]

    def products(self) -> list[CanonicalProduct]:
        self.sync_existing_memory()
        with self._connect() as connection:
            product_ids = self._qualifying_product_ids(connection)
            rows = connection.execute(
                "SELECT * FROM canonical_products WHERE active = 1 ORDER BY canonical_name COLLATE NOCASE"
            ).fetchall()
            aliases = connection.execute(
                "SELECT canonical_product_id, alias FROM product_aliases ORDER BY alias COLLATE NOCASE"
            ).fetchall()
        grouped: dict[int, list[str]] = {}
        for alias in aliases:
            grouped.setdefault(int(alias["canonical_product_id"]), []).append(alias["alias"])
        return [
            CanonicalProduct(
                id=int(row["id"]),
                canonical_name=row["canonical_name"],
                base_unit=row["base_unit"],
                package_quantity=row["package_quantity"],
                package_unit=row["package_unit"],
                aliases=tuple(grouped.get(int(row["id"]), [])),
            )
            for row in rows
            if int(row["id"]) in product_ids
        ]

    @staticmethod
    def _qualifying_product_rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
        rows = connection.execute(
            """SELECT links.canonical_product_id, links.normalized_unit,
                      links.package_quantity, items.id, items.description,
                      items.quantity, items.unit, items.unit_price,
                      items.line_total, items.line_type
               FROM invoice_item_identity_links links
               JOIN invoice_items items ON items.id = links.item_id
               JOIN canonical_products products
                 ON products.id = links.canonical_product_id
               WHERE products.active = 1"""
        ).fetchall()
        return [row for row in rows if is_product_line(dict(row))]

    @classmethod
    def _qualifying_product_ids(cls, connection: sqlite3.Connection) -> set[int]:
        return {
            int(row["canonical_product_id"])
            for row in cls._qualifying_product_rows(connection)
        }

    def supplier_identity(
        self,
        supplier_name: str,
        vat_id: str = "",
        *,
        ensure: bool = True,
    ) -> CanonicalSupplier | None:
        if ensure:
            self.sync_existing_memory()
        clean_vat = normalize_vat_id(vat_id)
        alias_key = normalize_identity_text(supplier_name)
        with self._connect() as connection:
            row = None
            if clean_vat:
                row = connection.execute(
                    "SELECT * FROM canonical_suppliers WHERE vat_id = ? AND active = 1",
                    (clean_vat,),
                ).fetchone()
            if row is None and alias_key:
                row = connection.execute(
                    """
                    SELECT canonical_suppliers.* FROM supplier_aliases
                    JOIN canonical_suppliers
                      ON canonical_suppliers.id = supplier_aliases.canonical_supplier_id
                    WHERE supplier_aliases.normalized_alias = ?
                      AND canonical_suppliers.active = 1
                    """,
                    (alias_key,),
                ).fetchone()
            if row is None:
                return None
            aliases = connection.execute(
                "SELECT alias FROM supplier_aliases WHERE canonical_supplier_id = ? ORDER BY alias",
                (row["id"],),
            ).fetchall()
        return CanonicalSupplier(
            id=int(row["id"]),
            canonical_name=row["canonical_name"],
            vat_id=row["vat_id"],
            aliases=tuple(alias["alias"] for alias in aliases),
        )

    def product_identity(
        self,
        description: str,
        *,
        ensure: bool = True,
    ) -> CanonicalProduct | None:
        if ensure:
            self.sync_existing_memory()
        alias_key = normalize_identity_text(description)
        if not alias_key:
            return None
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT canonical_products.* FROM product_aliases
                JOIN canonical_products
                  ON canonical_products.id = product_aliases.canonical_product_id
            WHERE product_aliases.normalized_alias = ?
              AND canonical_products.active = 1
                """,
                (alias_key,),
            ).fetchone()
            if row is None:
                return None
            aliases = connection.execute(
                "SELECT alias FROM product_aliases WHERE canonical_product_id = ? ORDER BY alias",
                (row["id"],),
            ).fetchall()
        return CanonicalProduct(
            id=int(row["id"]),
            canonical_name=row["canonical_name"],
            base_unit=row["base_unit"],
            package_quantity=row["package_quantity"],
            package_unit=row["package_unit"],
            aliases=tuple(alias["alias"] for alias in aliases),
        )

    def merge_suppliers(
        self, source_id: int, target_id: int, *, actor: str = "Barni user",
        reason: str = "Confirmed as the same supplier", evidence: Mapping[str, Any] | None = None,
    ) -> int:
        return self._merge_identity("supplier", source_id, target_id, actor, reason, evidence or {})

    def merge_products(
        self, source_id: int, target_id: int, *, actor: str = "Barni user",
        reason: str = "Confirmed as the same product", evidence: Mapping[str, Any] | None = None,
    ) -> int:
        return self._merge_identity("product", source_id, target_id, actor, reason, evidence or {})

    def rename_identity(
        self, entity_type: str, canonical_id: int, name: str, *,
        actor: str = "Barni user", reason: str = "Canonical name corrected",
    ) -> int:
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("Enter a canonical name.")
        table = {
            "supplier": "canonical_suppliers",
            "product": "canonical_products",
        }.get(entity_type)
        if table is None:
            raise ValueError("Unsupported identity type.")
        now = self._now()
        with self._connect() as connection:
            current = connection.execute(
                f"SELECT canonical_name FROM {table} WHERE id = ?",
                (canonical_id,),
            ).fetchone()
            if current is None:
                raise ValueError("This identity no longer exists.")
            connection.execute(
                f"UPDATE {table} SET canonical_name = ?, updated_at = ? WHERE id = ?",
                (clean_name, now, canonical_id),
            )
            decision = connection.execute(
                """
                INSERT INTO identity_decisions (
                    entity_type, source_canonical_id, target_canonical_id,
                    decision_type, alias, decided_at, actor, reason,
                    previous_state_json, current_state_json
                ) VALUES (?, ?, ?, 'rename', ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_type, canonical_id, canonical_id, current["canonical_name"],
                    now, actor, reason,
                    json.dumps({"canonical_name": current["canonical_name"]}, ensure_ascii=False),
                    json.dumps({"canonical_name": clean_name}, ensure_ascii=False),
                ),
            )
            connection.commit()
            return int(decision.lastrowid)

    def identity_health(self) -> dict[str, int]:
        self.sync_existing_memory()
        with self._connect() as connection:
            product_rows = self._qualifying_product_rows(connection)
            product_ids = {
                int(row["canonical_product_id"])
                for row in product_rows
            }
            aliases = connection.execute(
                "SELECT canonical_product_id FROM product_aliases"
            ).fetchall()
            price_counts: dict[int, int] = {}
            for row in product_rows:
                if row["unit_price"] is not None:
                    product_id = int(row["canonical_product_id"])
                    price_counts[product_id] = price_counts.get(product_id, 0) + 1
            values = {
                "suppliers": connection.execute(
                    "SELECT COUNT(*) FROM canonical_suppliers WHERE active = 1"
                ).fetchone()[0],
                "supplier_aliases": connection.execute(
                    "SELECT COUNT(*) FROM supplier_aliases"
                ).fetchone()[0],
                "products": len(product_ids),
                "product_aliases": sum(
                    int(row["canonical_product_id"]) in product_ids
                    for row in aliases
                ),
                "normalized_units": sum(
                    bool(str(row["normalized_unit"] or ""))
                    for row in product_rows
                ),
                "packaging_observations": sum(
                    row["package_quantity"] is not None
                    for row in product_rows
                ),
                "price_points": sum(price_counts.values()),
                "covered_products": sum(
                    count >= 2 for count in price_counts.values()
                ),
            }
        return {key: int(value) for key, value in values.items()}

    def _merge_identity(
        self, entity_type: str, source_id: int, target_id: int,
        actor: str, reason: str, evidence: Mapping[str, Any],
    ) -> int:
        if source_id == target_id:
            raise ValueError("Choose two different identities.")
        config = {
            "supplier": (
                "canonical_suppliers", "supplier_aliases", "canonical_supplier_id",
                "invoice_identity_links", "canonical_supplier_id",
            ),
            "product": (
                "canonical_products", "product_aliases", "canonical_product_id",
                "invoice_item_identity_links", "canonical_product_id",
            ),
        }
        if entity_type not in config:
            raise ValueError("Unsupported identity type.")
        canonical_table, alias_table, alias_fk, link_table, link_fk = config[entity_type]
        now = self._now()
        with self._connect() as connection:
            source = connection.execute(
                f"SELECT * FROM {canonical_table} WHERE id = ?", (source_id,)
            ).fetchone()
            target = connection.execute(
                f"SELECT * FROM {canonical_table} WHERE id = ?", (target_id,)
            ).fetchone()
            if source is None or target is None:
                raise ValueError("One of the identities no longer exists.")
            if not int(source["active"] or 0) or not int(target["active"] or 0):
                raise ValueError("Choose two active identities.")
            alias_ids = [int(row[0]) for row in connection.execute(
                f"SELECT id FROM {alias_table} WHERE {alias_fk} = ?", (source_id,)
            ).fetchall()]
            alias_keys = [str(row[0]) for row in connection.execute(
                f"SELECT DISTINCT normalized_alias FROM {alias_table} WHERE {alias_fk} = ?", (source_id,)
            ).fetchall()]
            link_key = "invoice_id" if entity_type == "supplier" else "item_id"
            link_ids = [int(row[0]) for row in connection.execute(
                f"SELECT {link_key} FROM {link_table} WHERE {link_fk} = ?", (source_id,)
            ).fetchall()]
            previous_state = {
                "source": dict(source), "target": dict(target),
                "alias_ids": alias_ids, "alias_keys": alias_keys, "link_ids": link_ids,
            }
            if (
                entity_type == "supplier"
                and not str(target["vat_id"] or "")
                and str(source["vat_id"] or "")
            ):
                connection.execute(
                    "UPDATE canonical_suppliers SET vat_id = ?, updated_at = ? WHERE id = ?",
                    (source["vat_id"], now, target_id),
                )
            connection.execute(
                f"UPDATE {alias_table} SET {alias_fk} = ?, confirmed = 1 WHERE {alias_fk} = ?",
                (target_id, source_id),
            )
            connection.execute(
                f"UPDATE {link_table} SET {link_fk} = ?, match_method = 'confirmed_alias', linked_at = ? WHERE {link_fk} = ?",
                (target_id, now, source_id),
            )
            connection.execute(
                f"UPDATE {canonical_table} SET active = 0, merged_into_id = ?, updated_at = ? WHERE id = ?",
                (target_id, now, source_id),
            )
            decision = connection.execute(
                """
                INSERT INTO identity_decisions (
                    entity_type, source_canonical_id, target_canonical_id,
                    decision_type, alias, decided_at, actor, reason, evidence_json,
                    previous_state_json, current_state_json
                ) VALUES (?, ?, ?, 'merge', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_type, source_id, target_id, source["canonical_name"], now,
                    actor, reason, json.dumps(dict(evidence), ensure_ascii=False),
                    json.dumps(previous_state, ensure_ascii=False),
                    json.dumps({"source_active": 0, "merged_into_id": target_id}, ensure_ascii=False),
                ),
            )
            connection.commit()
            return int(decision.lastrowid)

    def split_identity(
        self, entity_type: str, canonical_id: int, source_record_ids: Sequence[int],
        new_name: str, *, actor: str = "Barni user", reason: str = "Records belong to a separate identity",
    ) -> int:
        clean_name = str(new_name or "").strip()
        record_ids = sorted({int(value) for value in source_record_ids})
        if not clean_name or not record_ids:
            raise ValueError("Choose evidence and enter the identity name.")
        config = {
            "supplier": ("canonical_suppliers", "invoice_identity_links", "canonical_supplier_id", "invoice_id", "supplier_aliases", "source_invoice_id", "supplier"),
            "product": ("canonical_products", "invoice_item_identity_links", "canonical_product_id", "item_id", "product_aliases", "source_item_id", "description"),
        }
        if entity_type not in config:
            raise ValueError("Unsupported identity type.")
        table, link_table, link_fk, record_key, alias_table, alias_source, raw_field = config[entity_type]
        now = self._now()
        with self._connect() as connection:
            original = connection.execute(f"SELECT * FROM {table} WHERE id = ? AND active = 1", (canonical_id,)).fetchone()
            if original is None:
                raise ValueError("This identity is no longer active.")
            placeholders = ",".join("?" for _ in record_ids)
            owned = connection.execute(
                f"SELECT {record_key} FROM {link_table} WHERE {link_fk} = ? AND {record_key} IN ({placeholders})",
                [canonical_id, *record_ids],
            ).fetchall()
            owned_ids = [int(row[0]) for row in owned]
            if not owned_ids:
                raise ValueError("The selected evidence does not belong to this identity.")
            if entity_type == "supplier":
                cursor = connection.execute(
                    "INSERT INTO canonical_suppliers(canonical_name, vat_id, created_at, updated_at) VALUES (?, '', ?, ?)",
                    (clean_name, now, now),
                )
            else:
                cursor = connection.execute(
                    """INSERT INTO canonical_products(canonical_name, base_unit, package_quantity, package_unit, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (clean_name, original["base_unit"], original["package_quantity"], original["package_unit"], now, now),
                )
            new_id = int(cursor.lastrowid)
            owned_placeholders = ",".join("?" for _ in owned_ids)
            connection.execute(
                f"UPDATE {link_table} SET {link_fk} = ?, match_method = 'confirmed_split', linked_at = ? WHERE {record_key} IN ({owned_placeholders})",
                [new_id, now, *owned_ids],
            )
            alias_ids = [int(row[0]) for row in connection.execute(
                f"SELECT id FROM {alias_table} WHERE {alias_source} IN ({owned_placeholders})",
                owned_ids,
            ).fetchall()]
            if alias_ids:
                alias_placeholders = ",".join("?" for _ in alias_ids)
                connection.execute(
                    f"UPDATE {alias_table} SET {link_fk} = ?, confirmed = 1 WHERE id IN ({alias_placeholders})",
                    [new_id, *alias_ids],
                )
            decision = connection.execute(
                """INSERT INTO identity_decisions(
                       entity_type, source_canonical_id, target_canonical_id, decision_type,
                       alias, decided_at, actor, reason, evidence_json, previous_state_json, current_state_json
                   ) VALUES (?, ?, ?, 'split', ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entity_type, canonical_id, new_id, clean_name, now, actor, reason,
                    json.dumps({"source_record_ids": owned_ids}, ensure_ascii=False),
                    json.dumps({"canonical_id": canonical_id, "link_ids": owned_ids, "alias_ids": alias_ids}, ensure_ascii=False),
                    json.dumps({"new_canonical_id": new_id, "canonical_name": clean_name}, ensure_ascii=False),
                ),
            )
            connection.commit()
            return int(decision.lastrowid)

    def undo_decision(self, decision_id: int, *, actor: str = "Barni user") -> int:
        now = self._now()
        with self._connect() as connection:
            decision = connection.execute(
                "SELECT * FROM identity_decisions WHERE id = ?", (decision_id,)
            ).fetchone()
            if decision is None or decision["reversed_at"]:
                raise ValueError("This decision cannot be undone.")
            entity_type = decision["entity_type"]
            table = "canonical_suppliers" if entity_type == "supplier" else "canonical_products"
            alias_table = "supplier_aliases" if entity_type == "supplier" else "product_aliases"
            link_table = "invoice_identity_links" if entity_type == "supplier" else "invoice_item_identity_links"
            fk = "canonical_supplier_id" if entity_type == "supplier" else "canonical_product_id"
            link_key = "invoice_id" if entity_type == "supplier" else "item_id"
            previous = json.loads(decision["previous_state_json"] or "{}")
            decision_type = decision["decision_type"]
            if decision_type == "merge":
                source_id = int(decision["source_canonical_id"])
                connection.execute(f"UPDATE {table} SET active = 1, merged_into_id = NULL, updated_at = ? WHERE id = ?", (now, source_id))
                alias_ids = list(previous.get("alias_ids", []))
                alias_keys = previous.get("alias_keys", [])
                source_column = "source_invoice_id" if entity_type == "supplier" else "source_item_id"
                future_record_ids: list[int] = []
                if alias_keys:
                    placeholders = ",".join("?" for _ in alias_keys)
                    future_aliases = connection.execute(
                        f"SELECT id, {source_column} FROM {alias_table} WHERE {fk} = ? AND normalized_alias IN ({placeholders})",
                        [decision["target_canonical_id"], *alias_keys],
                    ).fetchall()
                    alias_ids.extend(int(row["id"]) for row in future_aliases)
                    future_record_ids.extend(int(row[source_column]) for row in future_aliases if row[source_column] is not None)
                for alias_id in set(alias_ids):
                    connection.execute(f"UPDATE {alias_table} SET {fk} = ? WHERE id = ?", (source_id, alias_id))
                for record_id in set([*previous.get("link_ids", []), *future_record_ids]):
                    connection.execute(
                        f"UPDATE {link_table} SET {fk} = ?, match_method = 'undo_merge', linked_at = ? WHERE {link_key} = ?",
                        (source_id, now, record_id),
                    )
                source_vat = str(previous.get("source", {}).get("vat_id") or "")
                target_before = previous.get("target", {})
                if entity_type == "supplier" and not str(target_before.get("vat_id") or "") and source_vat:
                    connection.execute("UPDATE canonical_suppliers SET vat_id = ? WHERE id = ?", ("", decision["target_canonical_id"]))
            elif decision_type == "rename":
                connection.execute(
                    f"UPDATE {table} SET canonical_name = ?, updated_at = ? WHERE id = ?",
                    (previous["canonical_name"], now, decision["target_canonical_id"]),
                )
            elif decision_type == "split":
                original_id = int(decision["source_canonical_id"])
                new_id = int(decision["target_canonical_id"])
                for alias_id in previous.get("alias_ids", []):
                    connection.execute(f"UPDATE {alias_table} SET {fk} = ? WHERE id = ?", (original_id, alias_id))
                for record_id in previous.get("link_ids", []):
                    connection.execute(
                        f"UPDATE {link_table} SET {fk} = ?, match_method = 'undo_split', linked_at = ? WHERE {link_key} = ?",
                        (original_id, now, record_id),
                    )
                connection.execute(f"UPDATE {table} SET active = 0, merged_into_id = ?, updated_at = ? WHERE id = ?", (original_id, now, new_id))
            else:
                raise ValueError("This decision type cannot be undone.")
            reversal = connection.execute(
                """INSERT INTO identity_decisions(
                       entity_type, source_canonical_id, target_canonical_id, decision_type,
                       alias, decided_at, actor, reason, previous_state_json, current_state_json
                   ) VALUES (?, ?, ?, 'undo', ?, ?, ?, ?, ?, ?)""",
                (
                    entity_type, decision["source_canonical_id"], decision["target_canonical_id"],
                    decision["alias"], now, actor, f"Undid decision #{decision_id}",
                    decision["current_state_json"], decision["previous_state_json"],
                ),
            )
            reversal_id = int(reversal.lastrowid)
            connection.execute(
                "UPDATE identity_decisions SET reversed_at = ?, reversal_decision_id = ? WHERE id = ?",
                (now, reversal_id, decision_id),
            )
            connection.commit()
            return reversal_id

    def resolve_evidence(
        self,
        source_record_ids: Sequence[int | str],
    ) -> tuple[InvoiceEvidence, ...]:
        sqlite_integer_max = (2 ** 63) - 1

        def stored_invoice_id(value: int | str) -> int | None:
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                return None
            return numeric if 0 < numeric <= sqlite_integer_max else None

        numeric_ids = []
        for value in source_record_ids:
            numeric = stored_invoice_id(value)
            if numeric is not None:
                numeric_ids.append(numeric)
        stored: dict[int, sqlite3.Row] = {}
        if numeric_ids:
            placeholders = ",".join("?" for _ in numeric_ids)
            with self._connect() as connection:
                rows = connection.execute(
                    f"""
                    SELECT invoices.*, canonical_suppliers.canonical_name
                    FROM invoices
                    LEFT JOIN invoice_identity_links
                      ON invoice_identity_links.invoice_id = invoices.id
                    LEFT JOIN canonical_suppliers
                      ON canonical_suppliers.id = invoice_identity_links.canonical_supplier_id
                    WHERE invoices.id IN ({placeholders})
                    """,
                    numeric_ids,
                ).fetchall()
                stored = {int(row["id"]): row for row in rows}
        evidence = []
        for source_id in source_record_ids:
            numeric = stored_invoice_id(source_id)
            if numeric is None:
                evidence.append(
                    InvoiceEvidence(source_id, None, "Current invoice", "", "", None, "", "")
                )
                continue
            row = stored.get(numeric)
            if row is None:
                continue
            evidence.append(
                InvoiceEvidence(
                    source_record_id=source_id,
                    invoice_id=numeric,
                    supplier=row["canonical_name"] or row["supplier"],
                    invoice_number=row["invoice_number"],
                    invoice_date=row["invoice_date"],
                    total=row["total"],
                    document_type=row["document_type"],
                    archived_path=row["archived_path"],
                )
            )
        return tuple(evidence)


def ensure_canonical_memory() -> dict[str, int]:
    return BusinessIdentityRepository().sync_existing_memory()
