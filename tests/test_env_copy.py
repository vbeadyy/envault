"""Tests for envault.env_copy."""
from __future__ import annotations

import pytest

from envault.env_copy import CopyError, copy_key, copy_keys


# ---------------------------------------------------------------------------
# Minimal in-memory vault stub
# ---------------------------------------------------------------------------

class _FakeVault:
    def __init__(self, data: dict[str, str] | None = None):
        self._data: dict[str, str] = dict(data or {})

    def get(self, key: str) -> str:
        from envault.vault import VaultError
        if key not in self._data:
            raise VaultError(f"{key!r} not found")
        return self._data[key]

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def list_keys(self) -> list[str]:
        return list(self._data.keys())


@pytest.fixture()
def src():
    return _FakeVault({"DB_URL": "postgres://localhost/dev", "SECRET": "abc123"})


@pytest.fixture()
def dst():
    return _FakeVault()


# ---------------------------------------------------------------------------
# copy_key
# ---------------------------------------------------------------------------

class TestCopyKey:
    def test_copies_value(self, src, dst):
        copy_key(src, dst, "DB_URL")
        assert dst.get("DB_URL") == "postgres://localhost/dev"

    def test_default_dst_key_matches_src_key(self, src, dst):
        result = copy_key(src, dst, "SECRET")
        assert result == "SECRET"

    def test_custom_dst_key(self, src, dst):
        result = copy_key(src, dst, "DB_URL", dst_key="DATABASE_URL")
        assert result == "DATABASE_URL"
        assert dst.get("DATABASE_URL") == "postgres://localhost/dev"

    def test_missing_src_key_raises(self, src, dst):
        with pytest.raises(CopyError, match="not found"):
            copy_key(src, dst, "NONEXISTENT")

    def test_empty_src_key_raises(self, src, dst):
        with pytest.raises(CopyError, match="src_key must not be empty"):
            copy_key(src, dst, "")

    def test_overwrite_false_raises_if_dst_key_exists(self, src):
        existing = _FakeVault({"DB_URL": "old_value"})
        with pytest.raises(CopyError, match="already exists"):
            copy_key(src, existing, "DB_URL", overwrite=False)

    def test_overwrite_true_replaces_value(self, src):
        existing = _FakeVault({"DB_URL": "old_value"})
        copy_key(src, existing, "DB_URL", overwrite=True)
        assert existing.get("DB_URL") == "postgres://localhost/dev"


# ---------------------------------------------------------------------------
# copy_keys
# ---------------------------------------------------------------------------

class TestCopyKeys:
    def test_copies_multiple_keys(self, src, dst):
        result = copy_keys(src, dst, ["DB_URL", "SECRET"])
        assert result == ["DB_URL", "SECRET"]
        assert dst.get("DB_URL") == "postgres://localhost/dev"
        assert dst.get("SECRET") == "abc123"

    def test_empty_list_raises(self, src, dst):
        with pytest.raises(CopyError, match="must not be empty"):
            copy_keys(src, dst, [])

    def test_stops_on_first_error(self, src, dst):
        with pytest.raises(CopyError):
            copy_keys(src, dst, ["DB_URL", "MISSING"])
        # DB_URL was processed before the error
        assert "DB_URL" in dst.list_keys()
        assert "MISSING" not in dst.list_keys()
