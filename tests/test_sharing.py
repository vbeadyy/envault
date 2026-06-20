"""Tests for envault.sharing — vault export/import functionality."""

import pytest

from envault.sharing import export_vault, import_snapshot, SharingError
from envault.vault import Vault


PASSPHRASE = "team-secret-pass"
RECIPIENT_PASS = "recipient-pass-456"


@pytest.fixture
def populated_vault(tmp_path):
    vault_file = tmp_path / "test.vault"
    vault = Vault(str(vault_file), PASSPHRASE)
    vault.set("DB_HOST", "localhost")
    vault.set("DB_PORT", "5432")
    vault.set("API_KEY", "supersecret")
    vault.save()
    return vault


class TestExportVault:
    def test_returns_nonempty_string(self, populated_vault):
        result = export_vault(populated_vault, PASSPHRASE, RECIPIENT_PASS)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_is_base64(self, populated_vault):
        import base64
        result = export_vault(populated_vault, PASSPHRASE, RECIPIENT_PASS)
        # Should not raise
        base64.b64decode(result)

    def test_different_exports_differ(self, populated_vault):
        """Each export uses a fresh random salt so outputs should differ."""
        first = export_vault(populated_vault, PASSPHRASE, RECIPIENT_PASS)
        second = export_vault(populated_vault, PASSPHRASE, RECIPIENT_PASS)
        assert first != second


class TestImportSnapshot:
    def test_roundtrip_recovers_all_secrets(self, populated_vault):
        snapshot = export_vault(populated_vault, PASSPHRASE, RECIPIENT_PASS)
        recovered = import_snapshot(snapshot, RECIPIENT_PASS)
        assert recovered["DB_HOST"] == "localhost"
        assert recovered["DB_PORT"] == "5432"
        assert recovered["API_KEY"] == "supersecret"

    def test_wrong_passphrase_raises_sharing_error(self, populated_vault):
        snapshot = export_vault(populated_vault, PASSPHRASE, RECIPIENT_PASS)
        with pytest.raises(SharingError, match="Decryption failed"):
            import_snapshot(snapshot, "wrong-passphrase")

    def test_corrupted_snapshot_raises_sharing_error(self):
        with pytest.raises(SharingError):
            import_snapshot("notvalidbase64!!!", RECIPIENT_PASS)

    def test_empty_vault_roundtrip(self, tmp_path):
        vault_file = tmp_path / "empty.vault"
        vault = Vault(str(vault_file), PASSPHRASE)
        vault.save()
        snapshot = export_vault(vault, PASSPHRASE, RECIPIENT_PASS)
        recovered = import_snapshot(snapshot, RECIPIENT_PASS)
        assert recovered == {}

    def test_unsupported_version_raises(self, populated_vault):
        import base64, json
        snapshot = export_vault(populated_vault, PASSPHRASE, RECIPIENT_PASS)
        raw = json.loads(base64.b64decode(snapshot).decode())
        raw["version"] = 99
        bad_snapshot = base64.b64encode(json.dumps(raw).encode()).decode()
        with pytest.raises(SharingError, match="Unsupported snapshot version"):
            import_snapshot(bad_snapshot, RECIPIENT_PASS)

    def test_missing_field_raises(self):
        import base64, json
        bad_payload = {"version": 1, "exported_at": 0}  # missing salt + ciphertext
        bad_snapshot = base64.b64encode(json.dumps(bad_payload).encode()).decode()
        with pytest.raises(SharingError, match="missing field"):
            import_snapshot(bad_snapshot, RECIPIENT_PASS)
