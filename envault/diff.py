"""Diff utilities for comparing vault snapshots."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "status": self.status,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }

    def __repr__(self) -> str:
        if self.status == "added":
            return f"+ {self.key}={self.new_value}"
        elif self.status == "removed":
            return f"- {self.key}={self.old_value}"
        elif self.status == "changed":
            return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"
        else:
            return f"  {self.key}={self.new_value}"


def diff_vaults(
    old: Dict[str, str],
    new: Dict[str, str],
    show_unchanged: bool = False,
) -> List[DiffEntry]:
    """Compare two plaintext key-value dicts and return a list of DiffEntry."""
    entries: List[DiffEntry] = []
    all_keys = sorted(set(old) | set(new))

    for key in all_keys:
        if key in old and key not in new:
            entries.append(DiffEntry(key=key, status="removed", old_value=old[key]))
        elif key not in old and key in new:
            entries.append(DiffEntry(key=key, status="added", new_value=new[key]))
        elif old[key] != new[key]:
            entries.append(
                DiffEntry(key=key, status="changed", old_value=old[key], new_value=new[key])
            )
        else:
            if show_unchanged:
                entries.append(
                    DiffEntry(key=key, status="unchanged", new_value=new[key])
                )

    return entries


def has_changes(entries: List[DiffEntry]) -> bool:
    """Return True if any entry represents a meaningful change."""
    return any(e.status != "unchanged" for e in entries)
