"""Tests for envault.rotation key-rotation feature."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.rotation import RotationError, rotate_key, apply_rotation


OLD_PASS = "old-secret"
NEW_PASS = "new-secret"


@pytest.fixture()
def populated_vault(tmp_path):
    path = tmp_path / "vault.json"
    v = Vault(path)
    v.init(OLD_PASS)
    v.set("DB_URL", "postgres://localhost/mydb", OLD_PASS)
    v.set("API_KEY", "supersecret123", OLD_PASS)
    return v


class TestRotateKey:
    def test_returns_dict_with_same_keys(self, populated_vault):
        rotated = rotate_key(populated_vault, OLD_PASS, NEW_PASS)
        assert set(rotated.keys()) == {"DB_URL", "API_KEY"}

    def test_ciphertexts_differ_after_rotation(self, populated_vault):
        rotated = rotate_key(populated_vault, OLD_PASS, NEW_PASS)
        for name, new_ct in rotated.items():
            assert new_ct != populated_vault.secrets[name]

    def test_rotated_values_decrypt_with_new_key(self, populated_vault):
        from envault.crypto import derive_key, decrypt

        rotated = rotate_key(populated_vault, OLD_PASS, NEW_PASS)
        new_key = derive_key(NEW_PASS, populated_vault.salt)

        assert decrypt(new_key, rotated["DB_URL"]) == "postgres://localhost/mydb"
        assert decrypt(new_key, rotated["API_KEY"]) == "supersecret123"

    def test_wrong_old_passphrase_raises(self, populated_vault):
        with pytest.raises(RotationError, match="old passphrase"):
            rotate_key(populated_vault, "wrong-pass", NEW_PASS)

    def test_original_vault_unchanged(self, populated_vault):
        original_secrets = dict(populated_vault.secrets)
        rotate_key(populated_vault, OLD_PASS, NEW_PASS)
        assert populated_vault.secrets == original_secrets


class TestApplyRotation:
    def test_vault_secrets_updated(self, populated_vault):
        original_cts = dict(populated_vault.secrets)
        apply_rotation(populated_vault, OLD_PASS, NEW_PASS)
        for name in original_cts:
            assert populated_vault.secrets[name] != original_cts[name]

    def test_can_get_secrets_after_rotation(self, populated_vault):
        apply_rotation(populated_vault, OLD_PASS, NEW_PASS)
        assert populated_vault.get("DB_URL", NEW_PASS) == "postgres://localhost/mydb"
        assert populated_vault.get("API_KEY", NEW_PASS) == "supersecret123"

    def test_old_passphrase_no_longer_works(self, populated_vault):
        apply_rotation(populated_vault, OLD_PASS, NEW_PASS)
        with pytest.raises(Exception):
            populated_vault.get("DB_URL", OLD_PASS)

    def test_persists_to_disk(self, populated_vault):
        from envault.vault import Vault

        path = populated_vault.path
        apply_rotation(populated_vault, OLD_PASS, NEW_PASS)

        reloaded = Vault(path)
        reloaded.load()
        assert reloaded.get("DB_URL", NEW_PASS) == "postgres://localhost/mydb"
