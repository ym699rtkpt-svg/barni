from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from itertools import combinations
from statistics import median
from typing import Any, Callable, Mapping, Sequence

from database import connect
from services.business_identity import BusinessIdentityRepository, InvoiceEvidence, normalize_currency
from services.evidence import EvidenceRef, invoice_ref


@dataclass(frozen=True)
class IdentityReviewCandidate:
    id: int
    entity_type: str
    review_type: str
    source_id: int
    target_id: int
    source_name: str
    target_name: str
    title: str
    explanation: str
    confidence: float
    priority: int
    reasons: tuple[str, ...]
    evidence: tuple[InvoiceEvidence, ...]
    status: str = "pending"

    @property
    def evidence_refs(self) -> tuple[EvidenceRef, ...]:
        return tuple(invoice_ref(value.invoice_id, captured_at=value.invoice_date,
                                 location=value.archived_path,
                                 metadata={"supplier": value.supplier,
                                           "invoice_number": value.invoice_number})
                     for value in self.evidence)


@dataclass(frozen=True)
class IdentityDecision:
    id: int
    entity_type: str
    decision_type: str
    label: str
    actor: str
    reason: str
    decided_at: str
    reversible: bool


@dataclass(frozen=True)
class IdentityRecord:
    record_id: int
    label: str
    invoice_id: int


def _text(value: Any) -> str:
    return str(value or "").strip()


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.casefold(), right.casefold()).ratio()


def _product_identifiers(value: str) -> set[str]:
    return set(re.findall(r"(?<!\d)\d{7,14}(?!\d)", value))


def _candidate_key(review_type: str, source_id: int, target_id: int, detail: str = "") -> str:
    low, high = sorted((source_id, target_id))
    raw = f"{review_type}:{low}:{high}:{detail}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IdentityReviewService:
    """Builds a quiet, evidence-backed queue without changing identity knowledge."""

    def __init__(
        self,
        connection_factory: Callable[[], sqlite3.Connection] = connect,
        identity_repository: BusinessIdentityRepository | None = None,
    ) -> None:
        self._connect = connection_factory
        self.identities = identity_repository or BusinessIdentityRepository(connection_factory)

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def refresh_queue(self) -> int:
        self.identities.sync_existing_memory()
        candidates = [
            *self._supplier_candidates(),
            *self._product_candidates(),
            *self._attribute_candidates(),
        ]
        now = self._now()
        with self._connect() as connection:
            for candidate in candidates:
                connection.execute(
                    """
                    INSERT INTO identity_review_candidates (
                        candidate_key, entity_type, review_type,
                        source_canonical_id, target_canonical_id,
                        title, explanation, confidence, priority,
                        reasons_json, evidence_json, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ON CONFLICT(candidate_key) DO UPDATE SET
                        title = excluded.title,
                        explanation = excluded.explanation,
                        confidence = excluded.confidence,
                        priority = excluded.priority,
                        reasons_json = excluded.reasons_json,
                        evidence_json = excluded.evidence_json,
                        updated_at = excluded.updated_at
                    WHERE identity_review_candidates.status = 'pending'
                    """,
                    (
                        candidate["key"], candidate["entity_type"], candidate["review_type"],
                        candidate["source_id"], candidate["target_id"], candidate["title"],
                        candidate["explanation"], candidate["confidence"], candidate["priority"],
                        json.dumps(candidate["reasons"], ensure_ascii=False),
                        json.dumps(candidate["evidence"], ensure_ascii=False), now, now,
                    ),
                )
            active_keys = [candidate["key"] for candidate in candidates]
            if active_keys:
                placeholders = ",".join("?" for _ in active_keys)
                connection.execute(
                    f"""UPDATE identity_review_candidates
                        SET status = 'superseded', updated_at = ?
                        WHERE status = 'pending'
                          AND review_type NOT LIKE 'fact_%'
                          AND candidate_key NOT IN ({placeholders})""",
                    [now, *active_keys],
                )
            else:
                connection.execute(
                    """UPDATE identity_review_candidates
                       SET status = 'superseded', updated_at = ?
                       WHERE status = 'pending' AND review_type NOT LIKE 'fact_%'""",
                    (now,),
                )
            connection.commit()
        return len(candidates)

    def enqueue_fact_conflict(
        self, *, review_type: str, entity_type: str, canonical_id: int,
        title: str, explanation: str, reasons: Sequence[str],
        invoice_ids: Sequence[int], priority: int,
    ) -> None:
        """Accept an unresolved Business Fact without resolving it in this service."""
        stored_review_type = f"fact_{review_type}"
        key = _candidate_key(stored_review_type, canonical_id, canonical_id)
        now = self._now()
        with self._connect() as connection:
            equivalent = connection.execute(
                """SELECT id, status, evidence_json
                   FROM identity_review_candidates
                   WHERE review_type = ? AND entity_type = ?
                     AND source_canonical_id = ? AND target_canonical_id = ?
                   ORDER BY CASE status
                       WHEN 'confirmed' THEN 0 WHEN 'rejected' THEN 0
                       WHEN 'pending' THEN 1 ELSE 2 END, id""",
                (stored_review_type, entity_type, canonical_id, canonical_id),
            ).fetchall()
            if any(row["status"] in {"confirmed", "rejected"} for row in equivalent):
                regenerated_ids = [
                    row["id"] for row in equivalent if row["status"] == "pending"
                ]
                if regenerated_ids:
                    placeholders = ",".join("?" for _ in regenerated_ids)
                    connection.execute(
                        f"""UPDATE identity_review_candidates
                            SET status = 'superseded', updated_at = ?
                            WHERE id IN ({placeholders})""",
                        [now, *regenerated_ids],
                    )
                    connection.commit()
                return

            pending = [row for row in equivalent if row["status"] == "pending"]
            if pending:
                primary = pending[0]
                try:
                    previous = json.loads(primary["evidence_json"] or "{}")
                except json.JSONDecodeError:
                    previous = {}
                combined_invoice_ids = list(dict.fromkeys([
                    *(int(value) for value in previous.get("invoice_ids", ()) if value),
                    *(int(value) for value in invoice_ids if value),
                ]))
                connection.execute(
                    """UPDATE identity_review_candidates
                       SET title = ?, explanation = ?, priority = ?, reasons_json = ?,
                           evidence_json = ?, updated_at = ?
                       WHERE id = ?""",
                    (
                        title, explanation, priority,
                        json.dumps(list(reasons), ensure_ascii=False),
                        json.dumps({"invoice_ids": combined_invoice_ids}, ensure_ascii=False),
                        now, primary["id"],
                    ),
                )
                if len(pending) > 1:
                    duplicate_ids = [row["id"] for row in pending[1:]]
                    placeholders = ",".join("?" for _ in duplicate_ids)
                    connection.execute(
                        f"""UPDATE identity_review_candidates
                            SET status = 'superseded', updated_at = ?
                            WHERE id IN ({placeholders})""",
                        [now, *duplicate_ids],
                    )
                connection.commit()
                return

            connection.execute(
                """INSERT INTO identity_review_candidates(
                       candidate_key, entity_type, review_type, source_canonical_id,
                       target_canonical_id, title, explanation, confidence, priority,
                       reasons_json, evidence_json, status, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, 1.0, ?, ?, ?, 'pending', ?, ?)
                   ON CONFLICT(candidate_key) DO UPDATE SET
                       title = excluded.title, explanation = excluded.explanation,
                       priority = excluded.priority, reasons_json = excluded.reasons_json,
                       evidence_json = excluded.evidence_json, updated_at = excluded.updated_at
                   WHERE identity_review_candidates.status = 'pending'""",
                (
                    key, entity_type, stored_review_type, canonical_id, canonical_id,
                    title, explanation, priority,
                    json.dumps(list(reasons), ensure_ascii=False),
                    json.dumps({"invoice_ids": list(dict.fromkeys(invoice_ids))}, ensure_ascii=False),
                    now, now,
                ),
            )
            connection.commit()

    def _supplier_candidates(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT canonical_suppliers.*,
                       COUNT(DISTINCT invoice_identity_links.invoice_id) invoice_count,
                       GROUP_CONCAT(DISTINCT invoice_identity_links.invoice_id) invoice_ids
                FROM canonical_suppliers
                LEFT JOIN invoice_identity_links
                  ON invoice_identity_links.canonical_supplier_id = canonical_suppliers.id
                WHERE canonical_suppliers.active = 1
                GROUP BY canonical_suppliers.id
                """
            ).fetchall()
        results = []
        for left, right in combinations(rows, 2):
            similarity = _similarity(_text(left["canonical_name"]), _text(right["canonical_name"]))
            left_vat, right_vat = _text(left["vat_id"]), _text(right["vat_id"])
            vat_conflict = bool(left_vat and right_vat and left_vat != right_vat)
            if similarity < 0.80 or vat_conflict:
                continue
            confidence = min(0.94, 0.55 + similarity * 0.40)
            evidence_ids = self._first_ids(left["invoice_ids"], right["invoice_ids"])
            reasons = [f"The supplier names are {similarity:.0%} similar."]
            if not left_vat or not right_vat:
                reasons.append("At least one supplier record has no VAT ID to confirm the match.")
            impact = min(25, int(left["invoice_count"] or 0) + int(right["invoice_count"] or 0))
            results.append({
                "key": _candidate_key("supplier_match", left["id"], right["id"]),
                "entity_type": "supplier", "review_type": "supplier_match",
                "source_id": int(left["id"]), "target_id": int(right["id"]),
                "title": "These suppliers may be the same",
                "explanation": f"I think {_text(left['canonical_name'])} and {_text(right['canonical_name'])} may refer to one supplier.",
                "confidence": confidence, "priority": 60 + impact,
                "reasons": reasons, "evidence": {"invoice_ids": evidence_ids},
            })
        return results

    def _product_candidates(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT canonical_products.*,
                       COUNT(DISTINCT links.item_id) item_count,
                       GROUP_CONCAT(DISTINCT links.item_id) item_ids,
                       GROUP_CONCAT(DISTINCT items.invoice_id) invoice_ids,
                       GROUP_CONCAT(DISTINCT invoice_links.canonical_supplier_id) supplier_ids,
                       GROUP_CONCAT(items.unit_price) prices
                FROM canonical_products
                LEFT JOIN invoice_item_identity_links links
                  ON links.canonical_product_id = canonical_products.id
                LEFT JOIN invoice_items items ON items.id = links.item_id
                LEFT JOIN invoice_identity_links invoice_links ON invoice_links.invoice_id = items.invoice_id
                WHERE canonical_products.active = 1
                GROUP BY canonical_products.id
                """
            ).fetchall()
        results = []
        for left, right in combinations(rows, 2):
            left_identifiers = _product_identifiers(_text(left["canonical_name"]))
            right_identifiers = _product_identifiers(_text(right["canonical_name"]))
            if left_identifiers and right_identifiers and left_identifiers.isdisjoint(right_identifiers):
                continue
            similarity = _similarity(_text(left["canonical_name"]), _text(right["canonical_name"]))
            same_supplier = bool(self._csv_set(left["supplier_ids"]) & self._csv_set(right["supplier_ids"]))
            same_unit = bool(left["base_unit"] and left["base_unit"] == right["base_unit"])
            same_package = (
                left["package_quantity"] is not None
                and right["package_quantity"] is not None
                and float(left["package_quantity"]) == float(right["package_quantity"])
                and left["package_unit"] == right["package_unit"]
            )
            price_similarity = self._price_similarity(left["prices"], right["prices"])
            score = similarity * 0.55 + (0.15 if same_supplier else 0) + (0.10 if same_unit else 0) + (0.10 if same_package else 0) + (0.10 if price_similarity else 0)
            if similarity < 0.66 or score < 0.74:
                continue
            reasons = [f"The product descriptions are {similarity:.0%} similar."]
            if same_supplier:
                reasons.append("They appear in invoices from the same supplier.")
            if same_unit:
                reasons.append(f"Both use the same normalized unit: {left['base_unit']}.")
            if same_package:
                reasons.append("The observed package sizes match.")
            if price_similarity:
                reasons.append("Their recent unit prices are similar.")
            count = int(left["item_count"] or 0) + int(right["item_count"] or 0)
            results.append({
                "key": _candidate_key("product_match", left["id"], right["id"]),
                "entity_type": "product", "review_type": "product_match",
                "source_id": int(left["id"]), "target_id": int(right["id"]),
                "title": "These products may be the same",
                "explanation": f"I've noticed {_text(left['canonical_name'])} and {_text(right['canonical_name'])} may actually be one product.",
                "confidence": min(0.96, score), "priority": 65 + min(25, count),
                "reasons": reasons,
                "evidence": {"invoice_ids": self._first_ids(left["invoice_ids"], right["invoice_ids"]), "item_ids": self._first_ids(left["item_ids"], right["item_ids"])},
            })
        return results

    def _attribute_candidates(self) -> list[dict[str, Any]]:
        results = []
        with self._connect() as connection:
            product_rows = connection.execute(
                """
                SELECT products.id, products.canonical_name,
                       GROUP_CONCAT(DISTINCT links.normalized_unit) units,
                       GROUP_CONCAT(DISTINCT COALESCE(links.package_quantity, '') || ':' || links.package_unit) packages,
                       GROUP_CONCAT(DISTINCT items.invoice_id) invoice_ids,
                       COUNT(DISTINCT items.id) item_count
                FROM canonical_products products
                JOIN invoice_item_identity_links links ON links.canonical_product_id = products.id
                JOIN invoice_items items ON items.id = links.item_id
                WHERE products.active = 1
                GROUP BY products.id
                """
            ).fetchall()
            supplier_rows = connection.execute(
                """
                SELECT suppliers.id, suppliers.canonical_name,
                       GROUP_CONCAT(DISTINCT invoices.supplier_id) vat_ids,
                       GROUP_CONCAT(DISTINCT invoices.currency) currencies,
                       GROUP_CONCAT(DISTINCT invoices.id) invoice_ids,
                       COUNT(DISTINCT invoices.id) invoice_count
                FROM canonical_suppliers suppliers
                JOIN invoice_identity_links links ON links.canonical_supplier_id = suppliers.id
                JOIN invoices ON invoices.id = links.invoice_id
                WHERE suppliers.active = 1
                GROUP BY suppliers.id
                """
            ).fetchall()
        for row in product_rows:
            known_units = {"kg", "g", "l", "ml", "unit", "package"}
            units = sorted(value for value in self._csv_set(row["units"]) if value in known_units)
            packages = sorted(value for value in self._csv_set(row["packages"]) if value not in {"", ":"})
            for review_type, values, label in (("unit_variation", units, "units"), ("package_variation", packages, "package sizes")):
                if len(values) < 2:
                    continue
                results.append(self._variation_candidate("product", row, review_type, values, label, 88))
        for row in supplier_rows:
            vats = sorted(value for value in self._csv_set(row["vat_ids"]) if value)
            currencies = sorted({normalize_currency(value) for value in self._csv_set(row["currencies"]) if value})
            if len(vats) > 1:
                results.append(self._variation_candidate("supplier", row, "vat_conflict", vats, "VAT IDs", 96))
            if len(currencies) > 1:
                results.append(self._variation_candidate("supplier", row, "currency_difference", currencies, "currencies", 72))
        return results

    def _variation_candidate(self, entity_type: str, row: Mapping[str, Any], review_type: str, values: Sequence[str], label: str, priority: int) -> dict[str, Any]:
        entity_id = int(row["id"])
        return {
            "key": _candidate_key(review_type, entity_id, entity_id, "|".join(values)),
            "entity_type": entity_type, "review_type": review_type,
            "source_id": entity_id, "target_id": entity_id,
            "title": f"I found different {label}",
            "explanation": f"{_text(row['canonical_name'])} appears with more than one {label[:-1] if label.endswith('s') else label}. I need your help before treating them as comparable.",
            "confidence": 1.0, "priority": priority + min(
                10,
                int((
                    row["item_count"]
                    if "item_count" in row.keys()
                    else row["invoice_count"]
                ) or 0),
            ),
            "reasons": [f"Stored evidence contains: {', '.join(values)}.", "I will keep these observations separate until you review them."],
            "evidence": {"invoice_ids": self._first_ids(row["invoice_ids"])},
        }

    @staticmethod
    def _csv_set(value: Any) -> set[str]:
        return {_text(part) for part in _text(value).split(",") if _text(part)}

    @classmethod
    def _first_ids(cls, *values: Any) -> list[int]:
        ids = []
        for value in values:
            for part in cls._csv_set(value):
                try:
                    numeric = int(part)
                except ValueError:
                    continue
                if numeric not in ids:
                    ids.append(numeric)
        return ids[:4]

    @staticmethod
    def _price_similarity(left: Any, right: Any) -> bool:
        def values(raw: Any) -> list[float]:
            result = []
            for value in _text(raw).split(","):
                try:
                    number = float(value)
                except ValueError:
                    continue
                if number > 0:
                    result.append(number)
            return result
        left_values, right_values = values(left), values(right)
        if not left_values or not right_values:
            return False
        base = median(left_values)
        return base > 0 and abs(median(right_values) - base) / base <= 0.15

    def pending(self, limit: int = 5) -> list[IdentityReviewCandidate]:
        self.refresh_queue()
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT candidates.*,
                          COALESCE(source.canonical_name, product_source.canonical_name) source_name,
                          COALESCE(target.canonical_name, product_target.canonical_name) target_name
                   FROM identity_review_candidates candidates
                   LEFT JOIN canonical_suppliers source
                     ON candidates.entity_type = 'supplier' AND source.id = candidates.source_canonical_id
                   LEFT JOIN canonical_suppliers target
                     ON candidates.entity_type = 'supplier' AND target.id = candidates.target_canonical_id
                   LEFT JOIN canonical_products product_source
                     ON candidates.entity_type = 'product' AND product_source.id = candidates.source_canonical_id
                   LEFT JOIN canonical_products product_target
                     ON candidates.entity_type = 'product' AND product_target.id = candidates.target_canonical_id
                   WHERE candidates.status = 'pending'
                     AND COALESCE(source.active, product_source.active, 0) = 1
                     AND COALESCE(target.active, product_target.active, 0) = 1
                   ORDER BY candidates.priority DESC, candidates.confidence DESC, candidates.id
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        output = []
        for row in rows:
            evidence_data = json.loads(row["evidence_json"] or "{}")
            output.append(IdentityReviewCandidate(
                id=int(row["id"]), entity_type=row["entity_type"], review_type=row["review_type"],
                source_id=int(row["source_canonical_id"]), target_id=int(row["target_canonical_id"]),
                source_name=row["source_name"] or "Unknown identity",
                target_name=row["target_name"] or "Unknown identity",
                title=row["title"], explanation=row["explanation"],
                confidence=float(row["confidence"]), priority=int(row["priority"]),
                reasons=tuple(json.loads(row["reasons_json"] or "[]")),
                evidence=self.identities.resolve_evidence(evidence_data.get("invoice_ids", [])),
                status=row["status"],
            ))
        return output

    def confirm(
        self, candidate_id: int, *, keep_canonical_id: int | None = None,
        actor: str = "Barni user",
    ) -> int:
        candidate = self._candidate(candidate_id)
        if candidate["review_type"] not in {"supplier_match", "product_match"}:
            return self.acknowledge(candidate_id, actor=actor)
        evidence = json.loads(candidate["evidence_json"] or "{}")
        reason = "Confirmed after reviewing the supporting invoices"
        source_id = int(candidate["source_canonical_id"])
        target_id = int(candidate["target_canonical_id"])
        if keep_canonical_id is not None:
            if keep_canonical_id not in {source_id, target_id}:
                raise ValueError("Choose one of the reviewed identities.")
            if keep_canonical_id == source_id:
                source_id, target_id = target_id, source_id
        if candidate["entity_type"] == "supplier":
            decision_id = self.identities.merge_suppliers(source_id, target_id, actor=actor, reason=reason, evidence=evidence)
        else:
            decision_id = self.identities.merge_products(source_id, target_id, actor=actor, reason=reason, evidence=evidence)
        self._resolve(candidate_id, "confirmed", decision_id)
        return decision_id

    def reject(self, candidate_id: int, reason: str = "The identities are different", *, actor: str = "Barni user") -> int:
        candidate = self._candidate(candidate_id)
        now = self._now()
        with self._connect() as connection:
            decision = connection.execute(
                """INSERT INTO identity_decisions(
                       entity_type, source_canonical_id, target_canonical_id, decision_type,
                       alias, decided_at, actor, reason, evidence_json, previous_state_json, current_state_json
                   ) VALUES (?, ?, ?, 'reject_match', ?, ?, ?, ?, ?, '{}', '{}')""",
                (candidate["entity_type"], candidate["source_canonical_id"], candidate["target_canonical_id"], candidate["title"], now, actor, reason, candidate["evidence_json"]),
            )
            decision_id = int(decision.lastrowid)
            connection.commit()
        self._resolve(candidate_id, "rejected", decision_id)
        return decision_id

    def acknowledge(self, candidate_id: int, *, actor: str = "Barni user") -> int:
        candidate = self._candidate(candidate_id)
        now = self._now()
        with self._connect() as connection:
            decision = connection.execute(
                """INSERT INTO identity_decisions(
                       entity_type, source_canonical_id, target_canonical_id, decision_type,
                       alias, decided_at, actor, reason, evidence_json, previous_state_json, current_state_json
                   ) VALUES (?, ?, ?, 'acknowledge_variation', ?, ?, ?, ?, ?, '{}', '{}')""",
                (candidate["entity_type"], candidate["source_canonical_id"], candidate["target_canonical_id"], candidate["title"], now, actor, "Variation reviewed; keep observations separate", candidate["evidence_json"]),
            )
            decision_id = int(decision.lastrowid)
            connection.commit()
        self._resolve(candidate_id, "confirmed", decision_id)
        return decision_id

    def _candidate(self, candidate_id: int) -> sqlite3.Row:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM identity_review_candidates WHERE id = ? AND status = 'pending'", (candidate_id,)).fetchone()
        if row is None:
            raise ValueError("This review has already been resolved.")
        return row

    def _resolve(self, candidate_id: int, status: str, decision_id: int) -> None:
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                "UPDATE identity_review_candidates SET status = ?, resolution_decision_id = ?, resolved_at = ?, updated_at = ? WHERE id = ?",
                (status, decision_id, now, now, candidate_id),
            )
            connection.commit()

    def decisions(self, limit: int = 20) -> list[IdentityDecision]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM identity_decisions
                   WHERE decision_type <> 'undo'
                   ORDER BY decided_at DESC, id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [IdentityDecision(
            id=int(row["id"]), entity_type=row["entity_type"], decision_type=row["decision_type"],
            label=row["alias"] or f"{row['entity_type'].title()} decision",
            actor=row["actor"], reason=row["reason"], decided_at=row["decided_at"],
            reversible=not bool(row["reversed_at"]) and row["decision_type"] in {"merge", "rename", "split", "reject_match", "acknowledge_variation"},
        ) for row in rows]

    def undo(self, decision_id: int, *, actor: str = "Barni user") -> int:
        with self._connect() as connection:
            decision = connection.execute("SELECT * FROM identity_decisions WHERE id = ?", (decision_id,)).fetchone()
        if decision is None or decision["reversed_at"]:
            raise ValueError("This decision cannot be undone.")
        if decision["decision_type"] in {"merge", "rename", "split"}:
            reversal_id = self.identities.undo_decision(decision_id, actor=actor)
            candidate_status = "rejected" if decision["decision_type"] == "merge" else "superseded"
        elif decision["decision_type"] in {"reject_match", "acknowledge_variation"}:
            now = self._now()
            with self._connect() as connection:
                reversal = connection.execute(
                    """INSERT INTO identity_decisions(
                           entity_type, source_canonical_id, target_canonical_id, decision_type,
                           alias, decided_at, actor, reason, previous_state_json, current_state_json
                       ) VALUES (?, ?, ?, 'undo', ?, ?, ?, ?, '{}', '{}')""",
                    (decision["entity_type"], decision["source_canonical_id"], decision["target_canonical_id"], decision["alias"], now, actor, f"Undid decision #{decision_id}"),
                )
                reversal_id = int(reversal.lastrowid)
                connection.execute(
                    "UPDATE identity_decisions SET reversed_at = ?, reversal_decision_id = ? WHERE id = ?",
                    (now, reversal_id, decision_id),
                )
                connection.commit()
            candidate_status = "pending"
        else:
            raise ValueError("This decision cannot be undone.")
        with self._connect() as connection:
            connection.execute(
                """UPDATE identity_review_candidates
                   SET status = ?, resolution_decision_id = NULL, resolved_at = NULL, updated_at = ?
                   WHERE resolution_decision_id = ?""",
                (candidate_status, self._now(), decision_id),
            )
            connection.commit()
        return reversal_id

    def identity_records(self, entity_type: str, canonical_id: int) -> list[IdentityRecord]:
        if entity_type == "supplier":
            sql = """SELECT invoices.id record_id, invoices.id invoice_id,
                            COALESCE(invoices.supplier, 'Missing supplier') || ' · ' ||
                            COALESCE(invoices.invoice_number, 'No invoice number') label
                     FROM invoice_identity_links links
                     JOIN invoices ON invoices.id = links.invoice_id
                     WHERE links.canonical_supplier_id = ? ORDER BY invoices.invoice_date DESC"""
        elif entity_type == "product":
            sql = """SELECT items.id record_id, invoices.id invoice_id,
                            COALESCE(items.description, 'Unnamed product') || ' · ' ||
                            COALESCE(invoices.invoice_number, 'No invoice number') label
                     FROM invoice_item_identity_links links
                     JOIN invoice_items items ON items.id = links.item_id
                     JOIN invoices ON invoices.id = items.invoice_id
                     WHERE links.canonical_product_id = ? ORDER BY invoices.invoice_date DESC"""
        else:
            raise ValueError("Unsupported identity type.")
        with self._connect() as connection:
            rows = connection.execute(sql, (canonical_id,)).fetchall()
        return [IdentityRecord(int(row["record_id"]), row["label"], int(row["invoice_id"])) for row in rows]

    def queue_count(self) -> int:
        return len(self.pending(limit=1000))
