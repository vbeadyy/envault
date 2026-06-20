"""Profile management for envault — switch between named env configurations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


PROFILES_FILENAME = ".envault_profiles.json"


class ProfileError(Exception):
    """Raised when profile operations fail."""


class ProfileManager:
    """Manages named profiles that map to sets of vault keys."""

    def __init__(self, profiles_path: Path) -> None:
        self._path = profiles_path
        self._data: Dict[str, List[str]] = {}
        if self._path.exists():
            self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        try:
            raw = self._path.read_text(encoding="utf-8")
            self._data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise ProfileError(f"Failed to load profiles: {exc}") from exc

    def save(self) -> None:
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            raise ProfileError(f"Failed to save profiles: {exc}") from exc

    # ------------------------------------------------------------------
    # Profile operations
    # ------------------------------------------------------------------

    def create(self, name: str, keys: Optional[List[str]] = None) -> None:
        """Create a new profile, optionally pre-populated with *keys*."""
        if name in self._data:
            raise ProfileError(f"Profile '{name}' already exists.")
        self._data[name] = list(keys or [])

    def delete(self, name: str) -> None:
        """Remove a profile by *name*."""
        if name not in self._data:
            raise ProfileError(f"Profile '{name}' does not exist.")
        del self._data[name]

    def add_key(self, name: str, key: str) -> None:
        """Associate *key* with profile *name*."""
        if name not in self._data:
            raise ProfileError(f"Profile '{name}' does not exist.")
        if key not in self._data[name]:
            self._data[name].append(key)

    def remove_key(self, name: str, key: str) -> None:
        """Disassociate *key* from profile *name*."""
        if name not in self._data:
            raise ProfileError(f"Profile '{name}' does not exist.")
        if key not in self._data[name]:
            raise ProfileError(f"Key '{key}' not in profile '{name}'.")
        self._data[name].remove(key)

    def get_keys(self, name: str) -> List[str]:
        """Return the list of keys belonging to *name*."""
        if name not in self._data:
            raise ProfileError(f"Profile '{name}' does not exist.")
        return list(self._data[name])

    def list_profiles(self) -> List[str]:
        """Return sorted list of profile names."""
        return sorted(self._data.keys())
