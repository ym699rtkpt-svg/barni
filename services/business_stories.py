from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence

from database import connect
from services.business_facts import ComparablePriceLedger


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
        import json

        matching: list[tuple[int, ...]] = []
        for row in rows:
            values = json.loads(row["evidence_json"] or "{}")
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
