from knowledge_engine.events import KnowledgeEvent

from knowledge_engine.supplier_manager import SupplierManager
from knowledge_engine.product_manager import ProductManager
from knowledge_engine.pricing_manager import PricingManager
from knowledge_engine.metrics_manager import MetricsManager
from knowledge_engine.memory_manager import MemoryManager


class KnowledgeEngine:

    def __init__(self):
        self.supplier = SupplierManager()
        self.product = ProductManager()
        self.pricing = PricingManager()
        self.metrics = MetricsManager()
        self.memory = MemoryManager()

    def handle_event(self, event: KnowledgeEvent) -> None:
        print(f"[KnowledgeEngine] Handling event: {event.event_type}")

        self.supplier.handle(event)
        self.product.handle(event)
        self.pricing.handle(event)
        self.metrics.handle(event)
        self.memory.handle(event)
