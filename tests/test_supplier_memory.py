from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from database import connect
from knowledge_engine.events import KnowledgeEvent
from knowledge_engine.repository import KnowledgeRepository
from knowledge_engine.supplier_manager import SupplierManager


with TemporaryDirectory() as directory:
    database_file = Path(directory) / "knowledge_test.db"

    repository = KnowledgeRepository(
        connection_factory=lambda: connect(database_file)
    )
    manager = SupplierManager(repository)

    event = KnowledgeEvent(
        event_type="invoice_approved",
        payload={
            "invoice_id": 101,
            "supplier": "Test Supplier",
            "supplier_id": "515151515",
            "invoice_date": "2026-08-06",
            "total": 100.0,
        },
        created_at=datetime.now(),
    )

    assert manager.handle(event) is True
    assert manager.handle(event) is False

    memory = repository.get_supplier_memory("515151515")

    assert memory is not None
    assert memory["invoice_count"] == 1
    assert memory["total_spend"] == 100.0
    assert memory["last_invoice_id"] == 101

    print("Supplier memory test passed")
