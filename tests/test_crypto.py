"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt, derive_key


PHRASE = "super-secret-passphrase"
SAMPLE_ENV = "DB_PASSWORD=hunter2\nAPI_KEY=abc123\nSECRET=mysecret"


class TestDeriveKey:
    def test_returns_32_bytes(self):
        salt = b"0123456789abcdef"
        key = derive_key(PHRASE, salt)
        assert len(key) == 32

    def test_deterministic(self):
        salt = b"saltsaltsaltsalt"
        assert derive_key(PHRASE, salt) == derive_key(PHRASE, salt)

    def test_different_passphrases_produce_different_keys(self):
        salt = b"saltsaltsaltsalt"
        assert derive_key("phrase-a", salt) != derive_key("phrase-b", salt)

    def test_different_salts_produce_different_keys(self):
        assert derive_key(PHRASE, b"salt1salt1salt1a") != derive_key(PHRASE, b"salt2salt2salt2b")


class TestEncryptDecrypt:
    def test_roundtrip(self):
        token = encrypt(SAMPLE_ENV, PHRASE)
        result = decrypt(token, PHRASE)
        assert result == SAMPLE_ENV

    def test_encrypt_produces_base64_string(self):
        import base64
        token = encrypt(SAMPLE_ENV, PHRASE)
        # Should not raise
        base64.b64decode(token.encode("utf-8"))

    def test_different_encryptions_of_same_plaintext(self):
        """Each call produces a unique ciphertext due to random salt/nonce."""
        t1 = encrypt(SAMPLE_ENV, PHRASE)
        t2 = encrypt(SAMPLE_ENV, PHRASE)
        assert t1 != t2

    def test_wrong_passphrase_raises(self):
        token = encrypt(SAMPLE_ENV, PHRASE)
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(token, "wrong-passphrase")

    def test_tampered_ciphertext_raises(self):
        import base64
        token = encrypt(SAMPLE_ENV, PHRASE)
        raw = bytearray(base64.b64decode(token))
        raw[-1] ^= 0xFF  # flip last byte
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(ValueError):
            decrypt(tampered, PHRASE)

    def test_invalid_base64_raises(self):
        with pytest.raises(ValueError, match="base64 decoding failed"):
            decrypt("!!!not_base64!!!", PHRASE)

    def test_empty_string_roundtrip(self):
        token = encrypt("", PHRASE)
        assert decrypt(token, PHRASE) == ""

    def test_unicode_content_roundtrip(self):
        content = "KEY=héllo\nOTHER=日本語"
        token = encrypt(content, PHRASE)
        assert decrypt(token, PHRASE) == content
