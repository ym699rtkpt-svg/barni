from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Mapping

from services.business_facts import ComparablePriceLedger
from services.business_memory import business_memory_data
from services.product_state import FirstFeedState


@dataclass(frozen=True)
class LearningSnapshot:
    invoices: int = 0
    suppliers: int = 0
    products: int = 0
    comparable_prices: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class LearningChange:
    invoices: int = 0
    suppliers: int = 0
    products: int = 0
    comparable_prices: int = 0

    @property
    def learned_something(self) -> bool:
        return any(asdict(self).values())

    def visible_rows(self) -> tuple[tuple[int, str], ...]:
        rows = (
            (self.suppliers, "supplier" if self.suppliers == 1 else "suppliers"),
            (self.products, "product" if self.products == 1 else "products"),
            (
                self.comparable_prices,
                "comparable price" if self.comparable_prices == 1 else "comparable prices",
            ),
        )
        return tuple(row for row in rows if row[0] > 0)

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def capture_learning_snapshot(
    *,
    memory_provider: Callable[[], Mapping[str, object]] = business_memory_data,
    price_ledger: ComparablePriceLedger | None = None,
) -> LearningSnapshot:
    """Capture persisted, canonical knowledge without deriving learning in the UI."""
    memory = memory_provider()
    ledger = price_ledger or ComparablePriceLedger()
    trusted_prices = len(ledger.trusted_observations(ensure=False))
    return LearningSnapshot(
        invoices=int(memory.get("invoice_count") or 0),
        suppliers=int(memory.get("supplier_count") or 0),
        products=int(memory.get("product_count") or 0),
        comparable_prices=trusted_prices,
    )


def learning_change(
    before: LearningSnapshot | Mapping[str, object],
    after: LearningSnapshot | Mapping[str, object],
) -> LearningChange:
    def value(snapshot: LearningSnapshot | Mapping[str, object], key: str) -> int:
        if isinstance(snapshot, LearningSnapshot):
            return int(getattr(snapshot, key))
        aliases = {
            "invoices": ("invoices", "invoice_count"),
            "suppliers": ("suppliers", "supplier_count"),
            "products": ("products", "product_count"),
            "comparable_prices": (
                "comparable_prices", "price_points", "price_point_count",
            ),
        }
        for candidate in aliases.get(key, (key,)):
            if candidate in snapshot:
                return int(snapshot.get(candidate) or 0)
        return 0

    return LearningChange(**{
        key: max(0, value(after, key) - value(before, key))
        for key in ("invoices", "suppliers", "products", "comparable_prices")
    })


def visible_learning_rows(change: Mapping[str, object]) -> tuple[tuple[int, str], ...]:
    return LearningChange(
        invoices=int(change.get("invoices") or 0),
        suppliers=int(change.get("suppliers") or 0),
        products=int(change.get("products") or 0),
        comparable_prices=int(
            change.get("comparable_prices", change.get("price_points")) or 0
        ),
    ).visible_rows()


def first_feed_onboarding_required(state: "FirstFeedState" | None = None) -> bool:
    store = state or FirstFeedState()
    memory = business_memory_data()
    return store.onboarding_required(
        approved_invoice_count=int(memory.get("invoice_count") or 0)
    )

