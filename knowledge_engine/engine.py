from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class KnowledgeEvent:
    event_type: str
    source: str
    payload: dict[str, Any]
    created_at: datetime


class KnowledgeEngine:

    def process(self, event: KnowledgeEvent) -> None:
        print(f"Processing {event.event_type}")
