"""Tests for envault.tags module."""

from __future__ import annotations

import pytest

from envault.tags import (
    TagError,
    add_tag,
    all_tags,
    filter_by_tag,
    list_tags,
    remove_tag,
)


# ---------------------------------------------------------------------------
# add_tag
# ---------------------------------------------------------------------------

class TestAddTag:
    def test_adds_tag_to_new_key(self):
        result = add_tag({}, "DB_URL", "database")
        assert result == {"DB_URL": ["database"]}

    def test_adds_tag_to_existing_key(self):
        base = {"DB_URL": ["database"]}
        result = add_tag(base, "DB_URL", "production")
        assert "production" in result["DB_URL"]
        assert "database" in result["DB_URL"]

    def test_duplicate_tag_is_ignored(self):
        base = {"DB_URL": ["database"]}
        result = add_tag(base, "DB_URL", "database")
        assert result["DB_URL"].count("database") == 1

    def test_empty_key_raises(self):
        with pytest.raises(TagError):
            add_tag({}, "", "database")

    def test_empty_tag_raises(self):
        with pytest.raises(TagError):
            add_tag({}, "DB_URL", "")

    def test_does_not_mutate_original(self):
        base = {"DB_URL": ["database"]}
        add_tag(base, "DB_URL", "production")
        assert base["DB_URL"] == ["database"]


# ---------------------------------------------------------------------------
# remove_tag
# ---------------------------------------------------------------------------

class TestRemoveTag:
    def test_removes_existing_tag(self):
        base = {"DB_URL": ["database", "production"]}
        result = remove_tag(base, "DB_URL", "production")
        assert "production" not in result["DB_URL"]

    def test_key_removed_when_no_tags_remain(self):
        base = {"DB_URL": ["database"]}
        result = remove_tag(base, "DB_URL", "database")
        assert "DB_URL" not in result

    def test_missing_tag_raises(self):
        base = {"DB_URL": ["database"]}
        with pytest.raises(TagError):
            remove_tag(base, "DB_URL", "nonexistent")

    def test_missing_key_raises(self):
        with pytest.raises(TagError):
            remove_tag({}, "DB_URL", "database")


# ---------------------------------------------------------------------------
# list_tags / filter_by_tag / all_tags
# ---------------------------------------------------------------------------

class TestQueryFunctions:
    def setup_method(self):
        self.tags = {
            "DB_URL": ["database", "production"],
            "REDIS_URL": ["cache", "production"],
            "SECRET_KEY": ["security"],
        }

    def test_list_tags_returns_tags_for_key(self):
        assert set(list_tags(self.tags, "DB_URL")) == {"database", "production"}

    def test_list_tags_returns_empty_for_unknown_key(self):
        assert list_tags(self.tags, "UNKNOWN") == []

    def test_filter_by_tag_returns_matching_keys(self):
        result = filter_by_tag(self.tags, "production")
        assert set(result) == {"DB_URL", "REDIS_URL"}

    def test_filter_by_tag_returns_empty_for_unknown_tag(self):
        assert filter_by_tag(self.tags, "nonexistent") == []

    def test_all_tags_returns_sorted_unique_tags(self):
        result = all_tags(self.tags)
        assert result == sorted({"database", "production", "cache", "security"})

    def test_all_tags_empty_when_no_tags(self):
        assert all_tags({}) == []
