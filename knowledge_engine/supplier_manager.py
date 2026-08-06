from __future__ import annotations

from knowledge_engine.repository import KnowledgeRepository


class SupplierManager:

    def __init__(
        self,
        repository: KnowledgeRepository | None = None,
    ) -> None:
        self.repository = repository or KnowledgeRepository()

    def handle(self, event) -> bool:
        if event.event_type != "invoice_approved":
            return False

        payload = event.payload

        updated = self.repository.upsert_supplier_memory(
            supplier_name=payload.get("supplier", ""),
            supplier_id=payload.get("supplier_id", ""),
            invoice_id=payload.get("invoice_id"),
            invoice_date=payload.get("invoice_date", ""),
            total=payload.get("total"),
        )

        if updated:
            print("[SupplierManager] Supplier memory updated")
        else:
            print("[SupplierManager] Duplicate event skipped")

        return updated

    def update_supplier(self):
        pass

    def supplier_statistics(self):
        pass

    def supplier_memory(self):
        pass
