"""Tests for envault.search module."""

from __future__ import annotations

import pytest

from envault.search import (
    SearchError,
    SearchResult,
    search_by_key,
    search_by_tag,
    search_keys_with_prefix,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


class _FakeVault:
    """Minimal vault stub used for search tests."""

    def __init__(self, keys: list[str], meta: dict | None = None) -> None:
        self._keys = keys
        self._meta = meta or {}

    def list_keys(self) -> list[str]:
        return list(self._keys)


@pytest.fixture()
def vault():
    meta = {
        "DB_HOST": {"tags": ["database", "infra"]},
        "DB_PASS": {"tags": ["database", "secret"]},
        "API_KEY": {"tags": ["api"]},
        "APP_DEBUG": {"tags": []},
    }
    return _FakeVault(
        keys=["DB_HOST", "DB_PASS", "API_KEY", "APP_DEBUG", "APP_PORT"],
        meta=meta,
    )


# ---------------------------------------------------------------------------
# SearchResult
# ---------------------------------------------------------------------------


class TestSearchResult:
    def test_to_dict_contains_required_fields(self):
        r = SearchResult(key="FOO", matched_by="key_pattern")
        d = r.to_dict()
        assert "key" in d
        assert "matched_by" in d

    def test_repr_contains_key(self):
        r = SearchResult(key="FOO", matched_by="tag")
        assert "FOO" in repr(r)


# ---------------------------------------------------------------------------
# search_by_key
# ---------------------------------------------------------------------------


class TestSearchByKey:
    def test_glob_matches_prefix_wildcard(self, vault):
        results = search_by_key(vault, "DB_*")
        keys = [r.key for r in results]
        assert "DB_HOST" in keys
        assert "DB_PASS" in keys
        assert "API_KEY" not in keys

    def test_glob_exact_match(self, vault):
        results = search_by_key(vault, "API_KEY")
        assert len(results) == 1
        assert results[0].key == "API_KEY"

    def test_no_match_returns_empty_list(self, vault):
        results = search_by_key(vault, "NONEXISTENT_*")
        assert results == []

    def test_regex_mode(self, vault):
        results = search_by_key(vault, r"^APP_", use_regex=True)
        keys = [r.key for r in results]
        assert "APP_DEBUG" in keys
        assert "APP_PORT" in keys
        assert "DB_HOST" not in keys

    def test_invalid_regex_raises_search_error(self, vault):
        with pytest.raises(SearchError):
            search_by_key(vault, "[invalid", use_regex=True)

    def test_empty_pattern_raises_search_error(self, vault):
        with pytest.raises(SearchError):
            search_by_key(vault, "")

    def test_matched_by_field_is_key_pattern(self, vault):
        results = search_by_key(vault, "API_KEY")
        assert results[0].matched_by == "key_pattern"


# ---------------------------------------------------------------------------
# search_by_tag
# ---------------------------------------------------------------------------


class TestSearchByTag:
    def test_finds_keys_with_tag(self, vault):
        results = search_by_tag(vault, "database")
        keys = [r.key for r in results]
        assert "DB_HOST" in keys
        assert "DB_PASS" in keys

    def test_tag_not_present_returns_empty(self, vault):
        results = search_by_tag(vault, "nonexistent-tag")
        assert results == []

    def test_empty_tag_raises_search_error(self, vault):
        with pytest.raises(SearchError):
            search_by_tag(vault, "")

    def test_matched_by_field_is_tag(self, vault):
        results = search_by_tag(vault, "api")
        assert all(r.matched_by == "tag" for r in results)


# ---------------------------------------------------------------------------
# search_keys_with_prefix
# ---------------------------------------------------------------------------


class TestSearchKeysWithPrefix:
    def test_returns_matching_prefix(self, vault):
        results = search_keys_with_prefix(vault, "APP_")
        keys = [r.key for r in results]
        assert "APP_DEBUG" in keys
        assert "APP_PORT" in keys
        assert "DB_HOST" not in keys

    def test_empty_prefix_raises_search_error(self, vault):
        with pytest.raises(SearchError):
            search_keys_with_prefix(vault, "")

    def test_no_match_returns_empty_list(self, vault):
        results = search_keys_with_prefix(vault, "UNKNOWN_")
        assert results == []
