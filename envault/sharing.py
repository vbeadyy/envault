"""Vault sharing utilities: export and import encrypted snapshots."""
import base64
import json
from typing import Tuple

from .crypto import encrypt, decrypt, derive_key
from .vault import Vault


class SharingError(Exception):
    """Raised when export or import fails."""


def export_vault(vault: Vault, passphrase: str) -> str:
    """Serialize and encrypt all vault entries to a portable base64 string.

    The snapshot format is::

        base64( salt(16) + nonce(12) + ciphertext )

    where the plaintext is a JSON object mapping key -> plaintext value.
    """
    if not passphrase:
        raise SharingError("Passphrase must not be empty.")

    keys = vault.list_keys()
    if not keys:
        raise SharingError("Vault is empty; nothing to export.")

    plaintext_map = {}
    for key in keys:
        try:
            plaintext_map[key] = vault.get(key)
        except Exception as exc:
            raise SharingError(f"Failed to read key '{key}': {exc}") from exc

    raw = json.dumps(plaintext_map, separators=(",", ":")).encode()

    import os
    salt = os.urandom(16)
    enc_key = derive_key(passphrase, salt)
    nonce, ciphertext = encrypt(enc_key, raw)

    blob = salt + nonce + ciphertext
    return base64.b64encode(blob).decode()


def import_snapshot(
    vault: Vault,
    passphrase: str,
    snapshot: str,
    overwrite: bool = False,
) -> Tuple[int, int]:
    """Decrypt a snapshot and merge its entries into *vault*.

    Returns
    -------
    (added, skipped) counts.
    """
    if not passphrase:
        raise SharingError("Passphrase must not be empty.")

    try:
        blob = base64.b64decode(snapshot)
    except Exception as exc:
        raise SharingError(f"Invalid snapshot encoding: {exc}") from exc

    if len(blob) < 16 + 12 + 1:
        raise SharingError("Snapshot data is too short to be valid.")

    salt = blob[:16]
    nonce = blob[16:28]
    ciphertext = blob[28:]

    enc_key = derive_key(passphrase, salt)
    try:
        raw = decrypt(enc_key, nonce, ciphertext)
    except Exception as exc:
        raise SharingError(f"Decryption failed — wrong passphrase or corrupt snapshot: {exc}") from exc

    try:
        plaintext_map = json.loads(raw.decode())
    except Exception as exc:
        raise SharingError(f"Snapshot payload is not valid JSON: {exc}") from exc

    existing_keys = set(vault.list_keys())
    added = 0
    skipped = 0

    for key, value in plaintext_map.items():
        if key in existing_keys and not overwrite:
            skipped += 1
            continue
        vault.set(key, value)
        added += 1

    return added, skipped
