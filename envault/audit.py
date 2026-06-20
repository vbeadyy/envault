"""Audit log for tracking vault access and modifications."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_FILENAME = ".envault_audit.json"


class AuditEntry:
    """Represents a single audit log entry."""

    def __init__(self, action: str, key: Optional[str], actor: str, timestamp: Optional[str] = None):
        self.action = action
        self.key = key
        self.actor = actor
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "key": self.key,
            "actor": self.actor,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            key=data.get("key"),
            actor=data["actor"],
            timestamp=data["timestamp"],
        )

    def __repr__(self) -> str:
        return f"AuditEntry(action={self.action!r}, key={self.key!r}, actor={self.actor!r})"


class AuditLog:
    """Manages a persistent audit log stored alongside the vault."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._entries: List[AuditEntry] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._entries = [AuditEntry.from_dict(e) for e in raw]
            except (json.JSONDecodeError, KeyError):
                self._entries = []

    def _save(self) -> None:
        self.path.write_text(
            json.dumps([e.to_dict() for e in self._entries], indent=2),
            encoding="utf-8",
        )

    def record(self, action: str, key: Optional[str] = None, actor: Optional[str] = None) -> AuditEntry:
        resolved_actor = actor or os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
        entry = AuditEntry(action=action, key=key, actor=resolved_actor)
        self._entries.append(entry)
        self._save()
        return entry

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def last(self, n: int = 10) -> List[AuditEntry]:
        return self._entries[-n:]


def audit_log_path(vault_path: Path) -> Path:
    """Return the audit log path for a given vault file."""
    return vault_path.parent / AUDIT_FILENAME
