"""Tests for envault.diff module."""

import pytest
from envault.diff import DiffEntry, diff_vaults, has_changes


OLD = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "old_secret"}
NEW = {"DB_HOST": "localhost", "DB_PORT": "5433", "API_KEY": "abc123"}


class TestDiffEntry:
    def test_to_dict_contains_required_fields(self):
        entry = DiffEntry(key="FOO", status="added", new_value="bar")
        d = entry.to_dict()
        assert "key" in d
        assert "status" in d
        assert "old_value" in d
        assert "new_value" in d

    def test_repr_added(self):
        entry = DiffEntry(key="FOO", status="added", new_value="bar")
        assert repr(entry).startswith("+")

    def test_repr_removed(self):
        entry = DiffEntry(key="FOO", status="removed", old_value="bar")
        assert repr(entry).startswith("-")

    def test_repr_changed(self):
        entry = DiffEntry(key="FOO", status="changed", old_value="a", new_value="b")
        assert repr(entry).startswith("~")

    def test_repr_unchanged(self):
        entry = DiffEntry(key="FOO", status="unchanged", new_value="bar")
        assert repr(entry).startswith(" ")


class TestDiffVaults:
    def test_detects_added_keys(self):
        entries = diff_vaults(OLD, NEW)
        added = [e for e in entries if e.status == "added"]
        assert any(e.key == "API_KEY" for e in added)

    def test_detects_removed_keys(self):
        entries = diff_vaults(OLD, NEW)
        removed = [e for e in entries if e.status == "removed"]
        assert any(e.key == "SECRET" for e in removed)

    def test_detects_changed_keys(self):
        entries = diff_vaults(OLD, NEW)
        changed = [e for e in entries if e.status == "changed"]
        assert any(e.key == "DB_PORT" for e in changed)

    def test_unchanged_hidden_by_default(self):
        entries = diff_vaults(OLD, NEW)
        unchanged = [e for e in entries if e.status == "unchanged"]
        assert unchanged == []

    def test_show_unchanged_flag(self):
        entries = diff_vaults(OLD, NEW, show_unchanged=True)
        unchanged = [e for e in entries if e.status == "unchanged"]
        assert any(e.key == "DB_HOST" for e in unchanged)

    def test_identical_dicts_no_changes(self):
        entries = diff_vaults(OLD, OLD)
        assert not has_changes(entries)

    def test_empty_old(self):
        entries = diff_vaults({}, {"FOO": "bar"})
        assert len(entries) == 1
        assert entries[0].status == "added"

    def test_empty_new(self):
        entries = diff_vaults({"FOO": "bar"}, {})
        assert len(entries) == 1
        assert entries[0].status == "removed"

    def test_keys_sorted(self):
        data = {"Z": "1", "A": "2", "M": "3"}
        entries = diff_vaults({}, data)
        keys = [e.key for e in entries]
        assert keys == sorted(keys)


class TestHasChanges:
    def test_returns_false_when_all_unchanged(self):
        entries = [DiffEntry(key="X", status="unchanged", new_value="v")]
        assert not has_changes(entries)

    def test_returns_true_when_change_present(self):
        entries = [DiffEntry(key="X", status="added", new_value="v")]
        assert has_changes(entries)
