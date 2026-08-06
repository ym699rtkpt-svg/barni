from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class KnowledgeEvent:
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
