"""Encryption and decryption utilities for envault using AES-GCM."""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


NONCE_SIZE = 12  # bytes, standard for AES-GCM
KEY_SIZE = 32    # bytes, AES-256


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=passphrase.encode("utf-8"),
        salt=salt,
        iterations=600_000,
        dklen=KEY_SIZE,
    )


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext string and return a base64-encoded ciphertext bundle.

    Bundle format (all concatenated, then base64-encoded):
        salt (16 bytes) | nonce (12 bytes) | ciphertext
    """
    salt = os.urandom(16)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    bundle = salt + nonce + ciphertext
    return base64.b64encode(bundle).decode("utf-8")


def decrypt(encoded_bundle: str, passphrase: str) -> str:
    """Decrypt a base64-encoded ciphertext bundle and return plaintext.

    Raises ValueError on authentication failure (wrong passphrase / tampered data).
    """
    try:
        bundle = base64.b64decode(encoded_bundle.encode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid ciphertext: base64 decoding failed.") from exc

    if len(bundle) < 16 + NONCE_SIZE + 16:  # salt + nonce + min GCM tag
        raise ValueError("Invalid ciphertext: bundle too short.")

    salt = bundle[:16]
    nonce = bundle[16:16 + NONCE_SIZE]
    ciphertext = bundle[16 + NONCE_SIZE:]

    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed: wrong passphrase or corrupted data.") from exc

    return plaintext.decode("utf-8")
