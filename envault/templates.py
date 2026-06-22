"""Template support for envault: save and apply .env templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class TemplateError(Exception):
    """Raised when a template operation fails."""


class TemplateManager:
    """Manages named .env templates stored as JSON on disk."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        else:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    def create(self, name: str, keys: List[str]) -> None:
        """Create a template with placeholder values for the given keys."""
        if not name:
            raise TemplateError("Template name must not be empty.")
        if name in self._data:
            raise TemplateError(f"Template '{name}' already exists.")
        if not keys:
            raise TemplateError("Template must contain at least one key.")
        self._data[name] = {k: "" for k in keys}
        self.save()

    def delete(self, name: str) -> None:
        if name not in self._data:
            raise TemplateError(f"Template '{name}' not found.")
        del self._data[name]
        self.save()

    def get(self, name: str) -> Dict[str, str]:
        if name not in self._data:
            raise TemplateError(f"Template '{name}' not found.")
        return dict(self._data[name])

    def list_templates(self) -> List[str]:
        return list(self._data.keys())

    def apply(self, name: str, values: Dict[str, str]) -> Dict[str, str]:
        """Return a mapping of template keys filled with the supplied values.

        Missing values default to an empty string; extra values are ignored.
        """
        template = self.get(name)
        result: Dict[str, str] = {}
        for key in template:
            result[key] = values.get(key, "")
        return result
