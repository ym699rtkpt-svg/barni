from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from database import root_dir


class FeedJournalCursor:
    """Persists only when the business journal was last delivered successfully."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or root_dir() / "feed-journal.json"

    def previous_visit(self, now: datetime | None = None) -> str:
        for candidate in (self.path, self.path.with_suffix(".json.backup")):
            if not candidate.exists():
                continue
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
                value = str(payload.get("last_successful_visit") or "").strip()
                datetime.fromisoformat(value)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
            return value
        current = now or datetime.now()
        return current.strftime("%Y-%m-%dT00:00:00")

    def mark_visited(self, visited_at: datetime | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        backup = self.path.with_suffix(".json.backup")
        if self.path.exists():
            try:
                existing = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = None
            if isinstance(existing, dict):
                shutil.copy2(self.path, backup)
        payload = {
            "last_successful_visit": (visited_at or datetime.now()).isoformat(timespec="seconds")
        }
        temporary = self.path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)
