from __future__ import annotations

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence

from database import connect
from services.business_facts import ComparablePriceLedger
from services.business_identity import BusinessIdentityRepository
from services.evidence import (
    Claim, Confidence, ConfidenceStatus, ConfidenceType, LOCAL_BUSINESS_ID,
    invoice_ref,
)


class StoryCategory:
    PRICE = "price"
    MEMORY = "memory"
    REVIEW = "review"
    DUPLICATE = "duplicate"
    QUIET = "quiet"


@dataclass(frozen=True)
class StoryEvidence:
    invoice_id: int
    supplier: str
    invoice_number: str
    invoice_date: str
    total: float | None
    archived_path: str

    @property
    def label(self) -> str:
        supplier = self.supplier or "Missing supplier"
        number = f"Invoice #{self.invoice_number}" if self.invoice_number else "No invoice number"
        return f"{supplier} · {number} · {self.invoice_date or 'Unknown date'}"


@dataclass(frozen=True)
class BusinessStory:
    story_type: str
    title: str
    description: str
    category: str
    priority: int
    tone: str = "neutral"
    icon: str = "•"
    evidence: tuple[StoryEvidence, ...] = ()
    evidence_values: Mapping[str, Any] = field(default_factory=dict)
    recommended_action: str | None = None
    action_target: int | str | None = None
    occurred_at: str = ""
    claim: Claim | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.claim is not None:
            return
        refs = tuple(invoice_ref(value.invoice_id, captured_at=value.invoice_date,
                                 location=value.archived_path,
                                 metadata={"supplier": value.supplier,
                                           "invoice_number": value.invoice_number})
                     for value in self.evidence)
        status = ConfidenceStatus.SUPPORTED if refs else ConfidenceStatus.INSUFFICIENT
        object.__setattr__(self, "claim", Claim(
            business_id=LOCAL_BUSINESS_ID, claim_type=self.story_type,
            subject_type="invoice", subject_id=self.action_target or (refs[0].source_id if refs else "none"),
            statement=self.description, evidence=refs,
            confidence=Confidence(ConfidenceType.ANSWER, status, None,
                                  "The story is derived from linked trusted records."),
            producer="business_story_engine", producer_version="2",
            value=dict(self.evidence_values), metadata={"category": self.category},
        ))


@dataclass(frozen=True)
class StoryContext:
    since: datetime | str | None = None
    current_invoice_id: int | None = None
    approval_outcome: str = ""
    memory_delta: Mapping[str, int] = field(default_factory=dict)


def _money(value: float) -> str:
    return f"₪{value:,.2f}"


def _since_text(value: datetime | str | None) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value or "").strip()


class BusinessStoryEngine:
    """Turns trusted memory and facts into reusable, evidence-linked stories."""

    minimum_price_change_pct = 5.0

    def __init__(self, connection_factory: Callable[[], sqlite3.Connection] = connect) -> None:
        self._connect = connection_factory
        self.ledger = ComparablePriceLedger(connection_factory)
        self.identities = BusinessIdentityRepository(connection_factory)

    def generate(
        self,
        context: StoryContext | None = None,
        *,
        max_stories: int = 3,
        include_quiet: bool = True,
    ) -> list[BusinessStory]:
        context = context or StoryContext()
        self.ledger.sync()
        stories = [
            *self._duplicate_stories(context),
            *self._price_stories(context),
            *self._identity_review_stories(context),
            *self._memory_stories(context),
        ]
        stories.sort(key=lambda story: story.priority, reverse=True)
        stories = self._deduplicate(stories)
        if stories:
            return stories[:max_stories]
        return [self._quiet_story(context)] if include_quiet else []

    def generate_feed(
        self,
        context: StoryContext | None = None,
        *,
        max_stories: int = 5,
    ) -> list[BusinessStory]:
        """Return a quiet, evidence-first journal of durable business events."""
        context = context or StoryContext()
        self.ledger.sync()
        stories = [
            *self._approved_invoice_stories(context),
            *self._new_supplier_stories(context),
            *self._product_repeat_stories(context),
            *self._price_stories(context),
            *self._historical_duplicate_stories(context),
            *self._identity_completed_stories(context),
        ]
        order = {
            "invoice_approved": 8,
            "supplier_learned": 7,
            "product_seen_again": 6,
            "price_increase": 5,
            "price_decrease": 5,
            "duplicate_resolved": 4,
            "identity_review_completed": 3,
        }
        stories.sort(
            key=lambda story: (
                story.occurred_at,
                order.get(story.story_type, 0),
                story.priority,
            ),
            reverse=True,
        )
        stories = self._deduplicate_feed(stories)
        if stories:
            return stories[:max_stories]
        return [self._quiet_story(context)]

    def _approved_invoice_stories(self, context: StoryContext) -> list[BusinessStory]:
        since = _since_text(context.since)
        clauses = ["status = 'approved'"]
        params: list[Any] = []
        if context.current_invoice_id:
            clauses.append("id = ?")
            params.append(context.current_invoice_id)
        elif since:
            clauses.append("datetime(COALESCE(NULLIF(approved_at, ''), created_at)) >= datetime(?)")
            params.append(since)
        else:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                f"""SELECT id, supplier, invoice_number,
                           COALESCE(NULLIF(approved_at, ''), created_at) AS occurred_at
                    FROM invoices WHERE {' AND '.join(clauses)}
                    ORDER BY datetime(occurred_at) DESC, id DESC""",
                params,
            ).fetchall()
        results = []
        for row in rows:
            evidence = self._evidence((int(row["id"]),))
            supplier = str(row["supplier"] or "Missing supplier")
            number = str(row["invoice_number"] or "")
            reference = f" Invoice #{number}" if number else ""
            results.append(BusinessStory(
                story_type="invoice_approved",
                title=f"{supplier} invoice approved",
                description=f"{supplier}{reference} was approved and added to Business Memory.",
                category=StoryCategory.MEMORY,
                priority=90,
                tone="positive",
                icon="✓",
                evidence=evidence,
                action_target=int(row["id"]),
                occurred_at=str(row["occurred_at"] or ""),
            ))
        return results

    def _new_supplier_stories(self, context: StoryContext) -> list[BusinessStory]:
        since = _since_text(context.since)
        if not since and not context.current_invoice_id:
            return []
        conditions = ["invoices.status = 'approved'"]
        params: list[Any] = []
        if context.current_invoice_id:
            conditions.append("invoices.id = ?")
            params.append(context.current_invoice_id)
        else:
            conditions.append(
                "datetime(COALESCE(NULLIF(invoices.approved_at, ''), invoices.created_at)) >= datetime(?)"
            )
            params.append(since)
        with self._connect() as connection:
            rows = connection.execute(
                f"""SELECT suppliers.canonical_name, invoices.id,
                           COALESCE(NULLIF(invoices.approved_at, ''), invoices.created_at) AS occurred_at
                    FROM invoice_identity_links links
                    JOIN canonical_suppliers suppliers ON suppliers.id = links.canonical_supplier_id
                    JOIN invoices ON invoices.id = links.invoice_id
                    WHERE {' AND '.join(conditions)}
                      AND invoices.id = (
                          SELECT first_invoices.id
                          FROM invoice_identity_links first_links
                          JOIN invoices first_invoices ON first_invoices.id = first_links.invoice_id
                          WHERE first_links.canonical_supplier_id = links.canonical_supplier_id
                            AND first_invoices.status = 'approved'
                          ORDER BY datetime(COALESCE(NULLIF(first_invoices.approved_at, ''),
                                                    first_invoices.created_at)), first_invoices.id
                          LIMIT 1
                      )
                    ORDER BY datetime(occurred_at) DESC, invoices.id DESC""",
                params,
            ).fetchall()
        return [BusinessStory(
            story_type="supplier_learned",
            title="I learned a new supplier",
            description=f"{row['canonical_name']} is now part of Business Memory.",
            category=StoryCategory.MEMORY,
            priority=85,
            tone="positive",
            icon="＋",
            evidence=self._evidence((int(row["id"]),)),
            recommended_action="See it in Business Memory",
            action_target=int(row["id"]),
            occurred_at=str(row["occurred_at"] or ""),
        ) for row in rows]

    def _product_repeat_stories(self, context: StoryContext) -> list[BusinessStory]:
        since = _since_text(context.since)
        if not since and not context.current_invoice_id:
            return []
        scope = "invoices.id = ?" if context.current_invoice_id else (
            "datetime(COALESCE(NULLIF(invoices.approved_at, ''), invoices.created_at)) >= datetime(?)"
        )
        value = context.current_invoice_id if context.current_invoice_id else since
        with self._connect() as connection:
            rows = connection.execute(
                f"""SELECT products.id AS product_id, products.canonical_name,
                           suppliers.canonical_name AS supplier_name,
                           MAX(COALESCE(NULLIF(invoices.approved_at, ''), invoices.created_at)) AS occurred_at,
                           COUNT(DISTINCT all_invoices.id) AS purchase_count,
                           GROUP_CONCAT(DISTINCT all_invoices.id) AS invoice_ids
                    FROM invoice_items items
                    JOIN invoice_item_identity_links product_links ON product_links.item_id = items.id
                    JOIN canonical_products products ON products.id = product_links.canonical_product_id
                    JOIN invoices ON invoices.id = items.invoice_id
                    JOIN invoice_identity_links supplier_links ON supplier_links.invoice_id = invoices.id
                    JOIN canonical_suppliers suppliers ON suppliers.id = supplier_links.canonical_supplier_id
                    JOIN invoice_item_identity_links all_product_links
                      ON all_product_links.canonical_product_id = products.id
                    JOIN invoice_items all_items ON all_items.id = all_product_links.item_id
                    JOIN invoices all_invoices ON all_invoices.id = all_items.invoice_id
                    JOIN invoice_identity_links all_supplier_links
                      ON all_supplier_links.invoice_id = all_invoices.id
                     AND all_supplier_links.canonical_supplier_id = suppliers.id
                    WHERE invoices.status = 'approved' AND all_invoices.status = 'approved'
                      AND {scope}
                    GROUP BY products.id, suppliers.id
                    HAVING COUNT(DISTINCT all_invoices.id) >= 2
                    ORDER BY datetime(occurred_at) DESC, purchase_count DESC""",
                (value,),
            ).fetchall()
        qualifying_product_ids = {
            product.id for product in self.identities.products()
        }
        results = []
        for row in rows:
            if int(row["product_id"]) not in qualifying_product_ids:
                continue
            invoice_ids = tuple(
                int(value) for value in str(row["invoice_ids"] or "").split(",") if value
            )
            count = int(row["purchase_count"])
            results.append(BusinessStory(
                story_type="product_seen_again",
                title="A familiar product returned",
                description=(
                    f"I've now seen {row['canonical_name']} from {row['supplier_name']} "
                    f"in {count} purchases."
                ),
                category=StoryCategory.MEMORY,
                priority=68,
                tone="neutral",
                icon="•",
                evidence=self._evidence(invoice_ids),
                evidence_values={"canonical_product_id": row["product_id"], "purchase_count": count},
                occurred_at=str(row["occurred_at"] or ""),
            ))
        return results

    def _historical_duplicate_stories(self, context: StoryContext) -> list[BusinessStory]:
        since = _since_text(context.since)
        if context.approval_outcome or not since:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT invoice_id, outcome, completed_at
                   FROM invoice_approval_operations
                   WHERE operation_status = 'completed'
                     AND outcome IN ('skipped', 'replaced', 'kept_both')
                     AND datetime(completed_at) >= datetime(?)
                   ORDER BY datetime(completed_at) DESC""",
                (since,),
            ).fetchall()
        wording = {
            "skipped": "You kept the existing invoice, so no duplicate knowledge was added.",
            "replaced": "You replaced the stored copy while preserving the same business record.",
            "kept_both": "You confirmed that both invoice records should be kept.",
        }
        return [BusinessStory(
            story_type="duplicate_resolved",
            title="Duplicate reviewed",
            description=wording[str(row["outcome"])],
            category=StoryCategory.DUPLICATE,
            priority=75,
            tone="attention",
            icon="⧉",
            evidence=self._evidence((int(row["invoice_id"]),)) if row["invoice_id"] else (),
            occurred_at=str(row["completed_at"] or ""),
        ) for row in rows if row["invoice_id"]]

    def _identity_completed_stories(self, context: StoryContext) -> list[BusinessStory]:
        since = _since_text(context.since)
        if not since:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT decisions.entity_type, decisions.decision_type,
                          decisions.decided_at, decisions.evidence_json,
                          COALESCE(suppliers.canonical_name, products.canonical_name, '') AS canonical_name
                   FROM identity_decisions decisions
                   LEFT JOIN canonical_suppliers suppliers
                     ON decisions.entity_type = 'supplier' AND suppliers.id = decisions.target_canonical_id
                   LEFT JOIN canonical_products products
                     ON decisions.entity_type = 'product' AND products.id = decisions.target_canonical_id
                   WHERE decisions.decision_type IN ('merge', 'rename', 'split')
                     AND decisions.reversed_at IS NULL
                     AND datetime(decisions.decided_at) >= datetime(?)
                   ORDER BY datetime(decisions.decided_at) DESC""",
                (since,),
            ).fetchall()
        results = []
        for row in rows:
            try:
                values = json.loads(row["evidence_json"] or "{}")
            except json.JSONDecodeError:
                continue
            invoice_ids = tuple(int(value) for value in values.get("invoice_ids", ()) if value)
            evidence = self._evidence(invoice_ids)
            if not evidence:
                continue
            entity = "supplier" if row["entity_type"] == "supplier" else "product"
            name = str(row["canonical_name"] or f"this {entity}")
            results.append(BusinessStory(
                story_type="identity_review_completed",
                title="Business identity clarified",
                description=f"I now understand {name} under one {entity} identity.",
                category=StoryCategory.MEMORY,
                priority=65,
                tone="positive",
                icon="✓",
                evidence=evidence,
                occurred_at=str(row["decided_at"] or ""),
            ))
        return results

    def _price_stories(self, context: StoryContext) -> list[BusinessStory]:
        facts = self._facts_in_scope(context)
        results: list[BusinessStory] = []
        for fact in facts:
            comparison = self.ledger.previous_comparable(fact, same_supplier=True)
            if comparison is None or comparison.change_pct is None:
                continue
            change = float(comparison.change_pct)
            if abs(change) < self.minimum_price_change_pct:
                continue
            increased = change > 0
            product = fact.canonical_product_name or "This product"
            unit = f" per {fact.normalized_unit}" if fact.normalized_unit else ""
            results.append(BusinessStory(
                story_type="price_increase" if increased else "price_decrease",
                title="Price increased" if increased else "Price decreased",
                description=(
                    f"{product} {'increased' if increased else 'decreased'} from "
                    f"{_money(float(comparison.previous.normalized_price))} to "
                    f"{_money(float(fact.normalized_price))}{unit} since the previous purchase "
                    f"({'+' if increased else ''}{change:.1f}%)."
                ),
                category=StoryCategory.PRICE,
                priority=95 if increased else 78,
                tone="attention" if increased else "positive",
                icon="📈" if increased else "📉",
                evidence=self._evidence(comparison.evidence_invoice_ids),
                evidence_values={
                    "canonical_product_id": fact.canonical_product_id,
                    "previous_price": comparison.previous.normalized_price,
                    "current_price": fact.normalized_price,
                    "normalized_unit": fact.normalized_unit,
                    "change_pct": round(change, 2),
                    "fact_status": fact.fact.trust_status,
                },
                recommended_action="Review the supporting invoices" if increased else None,
                action_target=fact.invoice_id,
                occurred_at=fact.observation_date,
            ))
        return results

    def _duplicate_stories(self, context: StoryContext) -> list[BusinessStory]:
        if context.approval_outcome not in {"skipped", "replaced", "kept_both"}:
            return []
        wording = {
            "skipped": "The existing invoice was kept and no duplicate knowledge was added.",
            "replaced": "The stored invoice was replaced while its business identity was preserved.",
            "kept_both": "Both invoices were kept after your review.",
        }[context.approval_outcome]
        invoice_ids = (context.current_invoice_id,) if context.current_invoice_id else ()
        return [BusinessStory(
            story_type="duplicate_resolved",
            title="I've seen this invoice before",
            description=wording,
            category=StoryCategory.DUPLICATE,
            priority=100,
            tone="attention",
            icon="⧉",
            evidence=self._evidence(invoice_ids),
        )]

    def _identity_review_stories(self, context: StoryContext) -> list[BusinessStory]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT evidence_json FROM identity_review_candidates
                   WHERE status = 'pending' ORDER BY priority DESC, id"""
            ).fetchall()
        if not rows:
            return []
        matching: list[tuple[int, ...]] = []
        for row in rows:
            try:
                values = json.loads(row["evidence_json"] or "{}")
            except json.JSONDecodeError:
                continue
            ids = tuple(int(value) for value in values.get("invoice_ids", ()) if value)
            if context.current_invoice_id and context.current_invoice_id not in ids:
                continue
            matching.append(ids)
        if not matching:
            return []
        count = min(len(matching), 2)
        invoice_ids = [value for ids in matching[:2] for value in ids]
        return [BusinessStory(
            story_type="identity_review_needed",
            title="One detail needs your help" if count == 1 else f"{count} details need your help",
            description=(
                "One product or supplier relationship needs confirmation before Barni can rely on it."
                if count == 1 else
                "Two product or supplier details need confirmation before Barni can rely on them."
            ),
            category=StoryCategory.REVIEW,
            priority=88,
            tone="attention",
            icon="◇",
            evidence=self._evidence(invoice_ids),
            recommended_action="Review identities",
            action_target="identity_review",
        )]

    def _memory_stories(self, context: StoryContext) -> list[BusinessStory]:
        delta = {key: int(value or 0) for key, value in context.memory_delta.items()}
        evidence = self._evidence((context.current_invoice_id,) if context.current_invoice_id else ())
        if delta.get("suppliers"):
            supplier = evidence[0].supplier if evidence else "This supplier"
            return [BusinessStory(
                story_type="supplier_learned",
                title="New supplier learned",
                description=f"{supplier} is now part of Business Memory.",
                category=StoryCategory.MEMORY,
                priority=76,
                tone="positive",
                icon="＋",
                evidence=evidence,
                recommended_action="See it in Business Memory",
            )]
        if delta.get("products"):
            count = delta["products"]
            return [BusinessStory(
                story_type="products_learned",
                title="Business Memory expanded",
                description=f"Barni learned {count} new {'product' if count == 1 else 'products'} from this invoice.",
                category=StoryCategory.MEMORY,
                priority=72,
                tone="positive",
                icon="＋",
                evidence=evidence,
                recommended_action="See it in Business Memory",
            )]
        since = _since_text(context.since)
        with self._connect() as connection:
            if context.current_invoice_id:
                rows = connection.execute(
                    "SELECT id FROM invoices WHERE id = ? AND status = 'approved'",
                    (context.current_invoice_id,),
                ).fetchall()
            elif since:
                rows = connection.execute(
                    """SELECT id FROM invoices WHERE status = 'approved'
                       AND datetime(COALESCE(NULLIF(approved_at, ''), created_at)) >= datetime(?)
                       ORDER BY id""",
                    (since,),
                ).fetchall()
            else:
                rows = []
        if not rows:
            return []
        ids = tuple(int(row["id"]) for row in rows)
        count = len(ids)
        return [BusinessStory(
            story_type="invoices_learned",
            title="Business Memory updated",
            description=f"Barni successfully learned {count} {'invoice' if count == 1 else 'invoices'}.",
            category=StoryCategory.MEMORY,
            priority=55,
            tone="positive",
            icon="✓",
            evidence=self._evidence(ids),
        )]

    def _facts_in_scope(self, context: StoryContext):
        if context.current_invoice_id:
            return self.ledger.facts_for_invoice(context.current_invoice_id, ensure=False)
        since = _since_text(context.since)
        return self.ledger.trusted_observations(recorded_since=since, ensure=False)

    def _evidence(self, invoice_ids: Sequence[int]) -> tuple[StoryEvidence, ...]:
        ids = tuple(dict.fromkeys(int(value) for value in invoice_ids if value))
        if not ids:
            return ()
        placeholders = ",".join("?" for _ in ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"""SELECT id, supplier, invoice_number, invoice_date, total, archived_path
                    FROM invoices WHERE id IN ({placeholders}) ORDER BY invoice_date, id""",
                ids,
            ).fetchall()
        return tuple(StoryEvidence(
            invoice_id=int(row["id"]), supplier=str(row["supplier"] or ""),
            invoice_number=str(row["invoice_number"] or ""),
            invoice_date=str(row["invoice_date"] or ""), total=row["total"],
            archived_path=str(row["archived_path"] or ""),
        ) for row in rows)

    @staticmethod
    def _deduplicate(stories: Sequence[BusinessStory]) -> list[BusinessStory]:
        results: list[BusinessStory] = []
        seen: set[tuple[str, Any]] = set()
        for story in stories:
            product = story.evidence_values.get("canonical_product_id")
            key = (story.category, product or story.story_type)
            if key not in seen:
                seen.add(key)
                results.append(story)
        return results

    @staticmethod
    def _deduplicate_feed(stories: Sequence[BusinessStory]) -> list[BusinessStory]:
        results: list[BusinessStory] = []
        seen: set[tuple[Any, ...]] = set()
        for story in stories:
            invoice_ids = tuple(source.invoice_id for source in story.evidence)
            product_id = story.evidence_values.get("canonical_product_id")
            key = (
                story.story_type,
                product_id or story.action_target or invoice_ids,
            )
            if key in seen:
                continue
            seen.add(key)
            results.append(story)
        return results

    def _quiet_story(self, context: StoryContext) -> BusinessStory:
        invoice_ids = (context.current_invoice_id,) if context.current_invoice_id else ()
        if not invoice_ids:
            with self._connect() as connection:
                latest = connection.execute(
                    "SELECT id FROM invoices WHERE status = 'approved' ORDER BY approved_at DESC, id DESC LIMIT 1"
                ).fetchone()
            invoice_ids = (int(latest["id"]),) if latest else ()
        evidence = self._evidence(invoice_ids)
        return BusinessStory(
            story_type="everything_normal",
            title="Everything looks good" if evidence else "Business Memory is ready to grow",
            description=(
                "This invoice is safely stored in Business Memory."
                if context.current_invoice_id else
                (
                    "No important changes need your attention right now."
                    if evidence else
                    "Feed Barni an invoice to begin building your business story."
                )
            ),
            category=StoryCategory.QUIET,
            priority=0,
            tone="positive",
            icon="✓",
            evidence=evidence,
        )
