"""Tag management for grouping and filtering vault secrets."""

from __future__ import annotations

from typing import Dict, List, Optional


class TagError(Exception):
    """Raised when a tag operation fails."""


def add_tag(tags: Dict[str, List[str]], key: str, tag: str) -> Dict[str, List[str]]:
    """Add a tag to a secret key. Returns updated tags dict."""
    if not key:
        raise TagError("Secret key must not be empty.")
    if not tag:
        raise TagError("Tag must not be empty.")
    updated = {k: list(v) for k, v in tags.items()}
    if key not in updated:
        updated[key] = []
    if tag not in updated[key]:
        updated[key].append(tag)
    return updated


def remove_tag(tags: Dict[str, List[str]], key: str, tag: str) -> Dict[str, List[str]]:
    """Remove a tag from a secret key. Returns updated tags dict."""
    updated = {k: list(v) for k, v in tags.items()}
    if key not in updated or tag not in updated[key]:
        raise TagError(f"Tag '{tag}' not found on key '{key}'.")
    updated[key].remove(tag)
    if not updated[key]:
        del updated[key]
    return updated


def list_tags(tags: Dict[str, List[str]], key: str) -> List[str]:
    """Return all tags for a given secret key."""
    return list(tags.get(key, []))


def filter_by_tag(tags: Dict[str, List[str]], tag: str) -> List[str]:
    """Return all secret keys that have the given tag."""
    return [key for key, key_tags in tags.items() if tag in key_tags]


def all_tags(tags: Dict[str, List[str]]) -> List[str]:
    """Return a sorted list of all unique tags across all keys."""
    unique: set = set()
    for key_tags in tags.values():
        unique.update(key_tags)
    return sorted(unique)
