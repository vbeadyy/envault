"""Tests for envault.env_clone."""

from __future__ import annotations

import pytest

from envault.env_clone import CloneError, clone_vault


# ---------------------------------------------------------------------------
# Minimal fake vault
# ---------------------------------------------------------------------------

class _FakeVault:
    def __init__(self, data: dict[str, str] | None = None):
        self._data: dict[str, str] = dict(data or {})

    def list_keys(self):
        return list(self._data.keys())

    def get(self, key: str, passphrase: str) -> str:  # noqa: ARG002
        return self._data[key]

    def set(self, key: str, value: str, passphrase: str) -> None:  # noqa: ARG002
        self._data[key] = value


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def source():
    return _FakeVault({"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"})


@pytest.fixture()
def destination():
    return _FakeVault()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCloneVault:
    def test_copies_all_keys(self, source, destination):
        copied = clone_vault(source, destination, "pass")
        assert set(copied) == {"DB_HOST", "DB_PORT", "API_KEY"}

    def test_values_are_transferred(self, source, destination):
        clone_vault(source, destination, "pass")
        assert destination.get("DB_HOST", "pass") == "localhost"
        assert destination.get("API_KEY", "pass") == "secret"

    def test_returns_sorted_list(self, source, destination):
        copied = clone_vault(source, destination, "pass")
        assert copied == sorted(copied)

    def test_prefix_filters_keys(self, source, destination):
        copied = clone_vault(source, destination, "pass", prefix="DB_")
        assert copied == ["DB_HOST", "DB_PORT"]
        assert destination.list_keys() == ["DB_HOST", "DB_PORT"]

    def test_prefix_no_match_returns_empty(self, source, destination):
        copied = clone_vault(source, destination, "pass", prefix="NONE_")
        assert copied == []

    def test_conflict_raises_without_overwrite(self, source):
        dest = _FakeVault({"DB_HOST": "remotehost"})
        with pytest.raises(CloneError, match="DB_HOST"):
            clone_vault(source, dest, "pass")

    def test_conflict_overwrite_replaces_value(self, source):
        dest = _FakeVault({"DB_HOST": "remotehost"})
        clone_vault(source, dest, "pass", overwrite=True)
        assert dest.get("DB_HOST", "pass") == "localhost"

    def test_same_object_raises(self, source):
        with pytest.raises(CloneError, match="different objects"):
            clone_vault(source, source, "pass")

    def test_empty_source_returns_empty(self, destination):
        empty = _FakeVault()
        result = clone_vault(empty, destination, "pass")
        assert result == []
