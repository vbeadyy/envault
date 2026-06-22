"""Vault snapshot history: save and restore previous versions of a vault."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

HISTORY_VERSION = 1
MAX_SNAPSHOTS = 50


class HistoryError(Exception):
    """Raised when a history operation fails."""


class Snapshot:
    """A point-in-time copy of vault secrets."""

    def __init__(self, data: dict, timestamp: Optional[float] = None, label: str = "") -> None:
        self.data: dict = data
        self.timestamp: float = timestamp if timestamp is not None else time.time()
        self.label: str = label

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Snapshot":
        return cls(
            data=d["data"],
            timestamp=d["timestamp"],
            label=d.get("label", ""),
        )

    def __repr__(self) -> str:  # pragma: no cover
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        label_part = f" ({self.label})" if self.label else ""
        return f"<Snapshot {ts}{label_part} keys={list(self.data.keys())}>"


class History:
    """Persist and manage a list of Snapshot objects for a vault."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._snapshots: List[Snapshot] = self._load()

    def _load(self) -> List[Snapshot]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [Snapshot.from_dict(s) for s in raw.get("snapshots", [])]
        except (json.JSONDecodeError, KeyError) as exc:
            raise HistoryError(f"Corrupt history file: {exc}") from exc

    def _save(self) -> None:
        payload = {
            "version": HISTORY_VERSION,
            "snapshots": [s.to_dict() for s in self._snapshots],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def push(self, data: dict, label: str = "") -> Snapshot:
        """Append a new snapshot; prune oldest if limit exceeded."""
        if not isinstance(data, dict):
            raise HistoryError("data must be a dict")
        snap = Snapshot(data=dict(data), label=label)
        self._snapshots.append(snap)
        if len(self._snapshots) > MAX_SNAPSHOTS:
            self._snapshots = self._snapshots[-MAX_SNAPSHOTS:]
        self._save()
        return snap

    def list(self) -> List[Snapshot]:
        """Return snapshots newest-first."""
        return list(reversed(self._snapshots))

    def get(self, index: int) -> Snapshot:
        """Return snapshot by newest-first index (0 = most recent)."""
        ordered = self.list()
        if index < 0 or index >= len(ordered):
            raise HistoryError(f"No snapshot at index {index} (total: {len(ordered)})")
        return ordered[index]

    def clear(self) -> None:
        self._snapshots = []
        self._save()

    def __len__(self) -> int:
        return len(self._snapshots)
