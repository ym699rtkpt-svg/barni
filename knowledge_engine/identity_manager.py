from __future__ import annotations

from services.business_identity import BusinessIdentityRepository


class IdentityManager:
    def __init__(self, repository: BusinessIdentityRepository | None = None) -> None:
        self.repository = repository or BusinessIdentityRepository()

    def handle(self, event) -> bool:
        if event.event_type != "invoice_approved":
            return False
        invoice_id = event.payload.get("invoice_id")
        if invoice_id is None:
            return False
        self.repository.learn_invoice(int(invoice_id))
        return True

