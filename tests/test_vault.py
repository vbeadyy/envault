"""Tests for the Vault class in envault/vault.py."""

import pytest
from pathlib import Path

from envault.vault import Vault, VaultError


PASSPHRASE = "super-secret-passphrase"


@pytest.fixture
def tmp_vault_path(tmp_path: Path) -> Path:
    return tmp_path / ".envault"


@pytest.fixture
def saved_vault(tmp_vault_path: Path) -> Vault:
    """A vault pre-populated with data and saved to disk."""
    v = Vault(tmp_vault_path, PASSPHRASE)
    v.set("API_KEY", "abc123")
    v.set("DB_URL", "postgres://localhost/mydb")
    v.save()
    return v


class TestVaultPersistence:
    def test_save_creates_file(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        v.set("FOO", "bar")
        v.save()
        assert tmp_vault_path.exists()

    def test_load_restores_data(self, saved_vault, tmp_vault_path):
        v2 = Vault(tmp_vault_path, PASSPHRASE)
        v2.load()
        assert v2.get("API_KEY") == "abc123"
        assert v2.get("DB_URL") == "postgres://localhost/mydb"

    def test_wrong_passphrase_raises(self, saved_vault, tmp_vault_path):
        v2 = Vault(tmp_vault_path, "wrong-passphrase")
        with pytest.raises(VaultError):
            v2.load()

    def test_missing_file_raises(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        with pytest.raises(VaultError, match="not found"):
            v.load()

    def test_round_trip_empty_vault(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        v.save()
        v2 = Vault(tmp_vault_path, PASSPHRASE)
        v2.load()
        assert v2.all() == {}


class TestVaultDataAccess:
    def test_set_and_get(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        v.set("KEY", "value")
        assert v.get("KEY") == "value"

    def test_get_missing_returns_none(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        assert v.get("MISSING") is None

    def test_delete_existing_key(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        v.set("TO_DELETE", "bye")
        assert v.delete("TO_DELETE") is True
        assert v.get("TO_DELETE") is None

    def test_delete_missing_key_returns_false(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        assert v.delete("GHOST") is False

    def test_all_returns_copy(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        v.set("A", "1")
        copy = v.all()
        copy["B"] = "2"
        assert v.get("B") is None

    def test_len(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        assert len(v) == 0
        v.set("X", "1")
        assert len(v) == 1

    def test_export_env_format(self, tmp_vault_path):
        v = Vault(tmp_vault_path, PASSPHRASE)
        v.set("ZEBRA", "z")
        v.set("ALPHA", "a")
        output = v.export_env()
        lines = output.splitlines()
        assert lines[0] == "ALPHA=a"
        assert lines[1] == "ZEBRA=z"
