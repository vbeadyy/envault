"""Merge two vault snapshots with conflict resolution strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class MergeError(Exception):
    """Raised when a merge operation fails."""


class ConflictStrategy(str, Enum):
    OURS = "ours"       # Keep value from base vault
    THEIRS = "theirs"   # Take value from incoming vault
    ERROR = "error"     # Raise on any conflict


@dataclass
class MergeConflict:
    key: str
    our_value: str
    their_value: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "our_value": self.our_value,
            "their_value": self.their_value,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MergeConflict(key={self.key!r}, "
            f"our={self.our_value!r}, their={self.their_value!r})"
        )


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    added_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


def merge_vaults(
    base: Dict[str, str],
    incoming: Dict[str, str],
    strategy: ConflictStrategy = ConflictStrategy.OURS,
) -> MergeResult:
    """Merge *incoming* into *base*, returning a MergeResult.

    Keys present only in *incoming* are always added.
    Keys present only in *base* are kept as-is and recorded in removed_keys
    (they represent keys absent from the incoming side).
    """
    if not isinstance(base, dict) or not isinstance(incoming, dict):
        raise MergeError("Both base and incoming must be dictionaries.")

    result = MergeResult()
    all_keys = set(base) | set(incoming)

    for key in sorted(all_keys):
        in_base = key in base
        in_incoming = key in incoming

        if in_base and in_incoming:
            if base[key] == incoming[key]:
                result.merged[key] = base[key]
            else:
                conflict = MergeConflict(
                    key=key,
                    our_value=base[key],
                    their_value=incoming[key],
                )
                result.conflicts.append(conflict)
                if strategy == ConflictStrategy.ERROR:
                    raise MergeError(
                        f"Conflict on key {key!r}: "
                        f"{base[key]!r} vs {incoming[key]!r}"
                    )
                elif strategy == ConflictStrategy.THEIRS:
                    result.merged[key] = incoming[key]
                else:  # OURS
                    result.merged[key] = base[key]
        elif in_incoming:
            result.merged[key] = incoming[key]
            result.added_keys.append(key)
        else:
            result.merged[key] = base[key]
            result.removed_keys.append(key)

    return result
