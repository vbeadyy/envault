"""Tests for envault.sharing — export_vault and import_snapshot."""
import base64
import pytest

from envault.vault import Vault
from envault.sharing import SharingError, export_vault, import_snapshot


PASSPHRASE = "test-secret-passphrase"


@pytest.fixture()
def populated_vault(tmp_path):
    v = Vault(str(tmp_path / "vault.env"), PASSPHRASE)
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "abc123")
    return v


class TestExportVault:
    def test_returns_nonempty_string(self, populated_vault):
        result = export_vault(populated_vault, PASSPHRASE)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_is_base64(self, populated_vault):
        result = export_vault(populated_vault, PASSPHRASE)
        decoded = base64.b64decode(result)  # must not raise
        assert len(decoded) > 28  # salt(16) + nonce(12) + at least 1 byte

    def test_different_exports_differ(self, populated_vault):
        """Each export uses a fresh random salt so blobs differ."""
        r1 = export_vault(populated_vault, PASSPHRASE)
        r2 = export_vault(populated_vault, PASSPHRASE)
        assert r1 != r2

    def test_empty_vault_raises(self, tmp_path):
        v = Vault(str(tmp_path / "empty.env"), PASSPHRASE)
        with pytest.raises(SharingError, match="empty"):
            export_vault(v, PASSPHRASE)

    def test_empty_passphrase_raises(self, populated_vault):
        with pytest.raises(SharingError, match="Passphrase"):
            export_vault(populated_vault, "")


class TestImportSnapshot:
    def test_roundtrip_all_keys(self, populated_vault, tmp_path):
        snapshot = export_vault(populated_vault, PASSPHRASE)
        target = Vault(str(tmp_path / "target.env"), PASSPHRASE)
        added, skipped = import_snapshot(target, PASSPHRASE, snapshot)
        assert added == 3
        assert skipped == 0
        assert target.get("DB_HOST") == "localhost"
        assert target.get("API_KEY") == "abc123"

    def test_skip_existing_keys_by_default(self, populated_vault, tmp_path):
        snapshot = export_vault(populated_vault, PASSPHRASE)
        target = Vault(str(tmp_path / "target.env"), PASSPHRASE)
        target.set("DB_HOST", "remotehost")
        added, skipped = import_snapshot(target, PASSPHRASE, snapshot)
        assert skipped == 1
        assert target.get("DB_HOST") == "remotehost"  # not overwritten

    def test_overwrite_flag_replaces_keys(self, populated_vault, tmp_path):
        snapshot = export_vault(populated_vault, PASSPHRASE)
        target = Vault(str(tmp_path / "target.env"), PASSPHRASE)
        target.set("DB_HOST", "remotehost")
        added, skipped = import_snapshot(target, PASSPHRASE, snapshot, overwrite=True)
        assert skipped == 0
        assert target.get("DB_HOST") == "localhost"

    def test_wrong_passphrase_raises(self, populated_vault):
        snapshot = export_vault(populated_vault, PASSPHRASE)
        target_vault = populated_vault
        with pytest.raises(SharingError, match="[Dd]ecrypt"):
            import_snapshot(target_vault, "wrong-passphrase", snapshot)

    def test_corrupted_snapshot_raises(self, populated_vault, tmp_path):
        """A base64 blob that is not a valid encrypted snapshot should raise SharingError."""
        garbage = base64.b64encode(b"this-is-not-a-valid-snapshot").decode()
        target = Vault(str(tmp_path / "target.env"), PASSPHRASE)
        with pytest.raises(SharingError):
            import_snapshot(target, PASSPHRASE, garbage)
