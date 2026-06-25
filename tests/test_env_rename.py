"""Tests for envault.env_rename."""

from __future__ import annotations

import pytest

from envault.env_rename import RenameError, rename_key, rename_keys


# ---------------------------------------------------------------------------
# Minimal fake vault
# ---------------------------------------------------------------------------

class _FakeVault:
    def __init__(self, data: dict[str, str] | None = None) -> None:
        self._data: dict[str, str] = dict(data or {})

    def list_keys(self) -> list[str]:
        return list(self._data.keys())

    def get(self, key: str) -> str:
        return self._data[key]

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        del self._data[key]


@pytest.fixture()
def vault() -> _FakeVault:
    return _FakeVault({"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"})


# ---------------------------------------------------------------------------
# rename_key
# ---------------------------------------------------------------------------

class TestRenameKey:
    def test_key_is_renamed(self, vault: _FakeVault) -> None:
        rename_key(vault, "DB_HOST", "DATABASE_HOST")
        assert "DATABASE_HOST" in vault.list_keys()
        assert "DB_HOST" not in vault.list_keys()

    def test_value_is_preserved(self, vault: _FakeVault) -> None:
        rename_key(vault, "DB_HOST", "DATABASE_HOST")
        assert vault.get("DATABASE_HOST") == "localhost"

    def test_other_keys_unchanged(self, vault: _FakeVault) -> None:
        rename_key(vault, "DB_HOST", "DATABASE_HOST")
        assert vault.get("DB_PORT") == "5432"

    def test_missing_old_key_raises(self, vault: _FakeVault) -> None:
        with pytest.raises(RenameError, match="does not exist"):
            rename_key(vault, "MISSING", "NEW_KEY")

    def test_duplicate_new_key_raises_by_default(self, vault: _FakeVault) -> None:
        with pytest.raises(RenameError, match="already exists"):
            rename_key(vault, "DB_HOST", "DB_PORT")

    def test_overwrite_allows_duplicate_new_key(self, vault: _FakeVault) -> None:
        rename_key(vault, "DB_HOST", "DB_PORT", overwrite=True)
        assert vault.get("DB_PORT") == "localhost"

    def test_empty_old_key_raises(self, vault: _FakeVault) -> None:
        with pytest.raises(RenameError, match="non-empty"):
            rename_key(vault, "", "NEW_KEY")

    def test_empty_new_key_raises(self, vault: _FakeVault) -> None:
        with pytest.raises(RenameError, match="non-empty"):
            rename_key(vault, "DB_HOST", "")

    def test_identical_keys_raise(self, vault: _FakeVault) -> None:
        with pytest.raises(RenameError, match="identical"):
            rename_key(vault, "DB_HOST", "DB_HOST")


# ---------------------------------------------------------------------------
# rename_keys
# ---------------------------------------------------------------------------

class TestRenameKeys:
    def test_all_keys_renamed(self, vault: _FakeVault) -> None:
        renamed = rename_keys(vault, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
        assert set(renamed) == {"DB_HOST", "DB_PORT"}
        assert "DATABASE_HOST" in vault.list_keys()
        assert "DATABASE_PORT" in vault.list_keys()

    def test_returns_list_of_old_keys(self, vault: _FakeVault) -> None:
        result = rename_keys(vault, {"API_KEY": "API_SECRET"})
        assert result == ["API_KEY"]

    def test_empty_mapping_raises(self, vault: _FakeVault) -> None:
        with pytest.raises(RenameError, match="empty"):
            rename_keys(vault, {})

    def test_partial_failure_leaves_applied_renames(self, vault: _FakeVault) -> None:
        """Renames before the bad one are kept (no rollback)."""
        with pytest.raises(RenameError):
            rename_keys(vault, {"DB_HOST": "DATABASE_HOST", "MISSING": "X"})
        # First rename succeeded
        assert "DATABASE_HOST" in vault.list_keys()
