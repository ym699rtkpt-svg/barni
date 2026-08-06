from datetime import datetime

from knowledge_engine.engine import KnowledgeEngine
from knowledge_engine.events import KnowledgeEvent


engine = KnowledgeEngine()

event = KnowledgeEvent(
    event_type="invoice_approved",
    payload={"supplier": "Test Supplier"},
    created_at=datetime.now(),
)

engine.handle_event(event)
