"""Search and filter vault entries by key patterns or value metadata."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import List, Optional

from envault.vault import Vault


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    key: str
    matched_by: str  # 'key_pattern' | 'value_prefix' | 'tag'

    def to_dict(self) -> dict:
        return {"key": self.key, "matched_by": self.matched_by}

    def __repr__(self) -> str:
        return f"SearchResult(key={self.key!r}, matched_by={self.matched_by!r})"


def search_by_key(
    vault: Vault,
    pattern: str,
    *,
    use_regex: bool = False,
) -> List[SearchResult]:
    """Return keys matching *pattern* (glob by default, regex if use_regex=True)."""
    if not pattern:
        raise SearchError("Search pattern must not be empty.")

    results: List[SearchResult] = []
    keys = vault.list_keys()

    for key in keys:
        if use_regex:
            try:
                matched = bool(re.search(pattern, key))
            except re.error as exc:
                raise SearchError(f"Invalid regex pattern: {exc}") from exc
        else:
            matched = fnmatch.fnmatch(key, pattern)

        if matched:
            results.append(SearchResult(key=key, matched_by="key_pattern"))

    return results


def search_by_tag(
    vault: Vault,
    tag: str,
) -> List[SearchResult]:
    """Return keys that carry *tag* in their metadata."""
    if not tag:
        raise SearchError("Tag must not be empty.")

    results: List[SearchResult] = []
    metadata: dict = getattr(vault, "_meta", {})

    for key in vault.list_keys():
        tags = metadata.get(key, {}).get("tags", [])
        if tag in tags:
            results.append(SearchResult(key=key, matched_by="tag"))

    return results


def search_keys_with_prefix(
    vault: Vault,
    prefix: str,
) -> List[SearchResult]:
    """Return keys whose names start with *prefix*."""
    if not prefix:
        raise SearchError("Prefix must not be empty.")

    return [
        SearchResult(key=k, matched_by="key_pattern")
        for k in vault.list_keys()
        if k.startswith(prefix)
    ]
