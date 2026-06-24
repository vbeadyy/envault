"""Key expiry management for envault vaults."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ExpiryError(Exception):
    """Raised when an expiry operation fails."""


@dataclass
class ExpiryRecord:
    key: str
    expires_at: float  # Unix timestamp
    warn_before: int = 86400  # seconds before expiry to start warning (default 1 day)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "expires_at": self.expires_at,
            "warn_before": self.warn_before,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryRecord":
        return cls(
            key=data["key"],
            expires_at=float(data["expires_at"]),
            warn_before=int(data.get("warn_before", 86400)),
        )

    def is_expired(self, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        return now >= self.expires_at

    def is_expiring_soon(self, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        return not self.is_expired(now) and (self.expires_at - now) <= self.warn_before


def set_expiry(
    records: Dict[str, ExpiryRecord],
    key: str,
    expires_at: float,
    warn_before: int = 86400,
) -> Dict[str, ExpiryRecord]:
    """Set or update an expiry record for a key."""
    if not key:
        raise ExpiryError("Key must not be empty.")
    if expires_at <= time.time():
        raise ExpiryError("expires_at must be a future timestamp.")
    updated = dict(records)
    updated[key] = ExpiryRecord(key=key, expires_at=expires_at, warn_before=warn_before)
    return updated


def remove_expiry(records: Dict[str, ExpiryRecord], key: str) -> Dict[str, ExpiryRecord]:
    """Remove an expiry record for a key."""
    if key not in records:
        raise ExpiryError(f"No expiry record found for key '{key}'.")
    updated = dict(records)
    del updated[key]
    return updated


def get_expired_keys(
    records: Dict[str, ExpiryRecord], now: Optional[float] = None
) -> List[ExpiryRecord]:
    """Return all records whose keys have expired."""
    now = now if now is not None else time.time()
    return [r for r in records.values() if r.is_expired(now)]


def get_expiring_soon_keys(
    records: Dict[str, ExpiryRecord], now: Optional[float] = None
) -> List[ExpiryRecord]:
    """Return all records whose keys will expire soon (within warn_before window)."""
    now = now if now is not None else time.time()
    return [r for r in records.values() if r.is_expiring_soon(now)]
