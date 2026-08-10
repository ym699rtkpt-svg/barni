from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Mapping

import database


class FirstFeedState:
    """Small persisted product-state record for the one-time First Feed flow."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or database.root_dir() / "product-state.json"

    def is_complete(self) -> bool:
        payload = self._read()
        return bool(payload.get("first_feed_completed_at"))

    def onboarding_required(self, *, approved_invoice_count: int) -> bool:
        if self.is_complete():
            return False
        if approved_invoice_count > 0:
            # Existing businesses predate this state record and must not be forced
            # through first-use onboarding.
            self.complete(source="existing_business_memory")
            return False
        return True

    def complete(
        self,
        *,
        invoice_id: int | None = None,
        source: str = "first_approved_invoice",
        completed_at: datetime | None = None,
    ) -> None:
        if self.is_complete():
            return
        payload = self._read()
        payload.update({
            "first_feed_completed_at": (completed_at or datetime.now()).isoformat(
                timespec="seconds"
            ),
            "first_feed_invoice_id": invoice_id,
            "first_feed_completion_source": source,
        })
        self._write(payload)

    def _read(self) -> dict:
        backup = self.path.with_suffix(self.path.suffix + ".backup")
        for candidate in (self.path, backup):
            if not candidate.exists():
                continue
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                return payload
        return {}

    def _write(self, payload: Mapping[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        backup = self.path.with_suffix(self.path.suffix + ".backup")
        if self.path.exists() and self._read():
            shutil.copy2(self.path, backup)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(dict(payload), handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)
