"""Team sharing support for envault vaults.

Provides functionality to export encrypted vault snapshots and import
them, enabling secure sharing of .env configurations across teams.
"""

import base64
import json
import time
from typing import Optional

from envault.crypto import derive_key, encrypt, decrypt
from envault.vault import Vault, VaultError


SHARE_FORMAT_VERSION = 1


class SharingError(Exception):
    """Raised when a sharing operation fails."""


def export_vault(vault: Vault, passphrase: str, recipient_passphrase: str) -> str:
    """Export a vault as a portable encrypted snapshot string.

    The vault contents are re-encrypted with the recipient's passphrase so
    they can be safely transmitted and imported by another user.

    Args:
        vault: The Vault instance to export.
        passphrase: Current passphrase used to read the vault.
        recipient_passphrase: Passphrase the recipient will use to import.

    Returns:
        A base64-encoded JSON string representing the encrypted snapshot.

    Raises:
        SharingError: If the vault cannot be exported.
    """
    try:
        secrets = {key: vault.get(key) for key in vault.list_keys()}
    except VaultError as exc:
        raise SharingError(f"Failed to read vault for export: {exc}") from exc

    payload = json.dumps(secrets).encode()

    import os
    salt = os.urandom(16)
    key = derive_key(recipient_passphrase, salt)
    ciphertext = encrypt(payload, key)

    snapshot = {
        "version": SHARE_FORMAT_VERSION,
        "salt": base64.b64encode(salt).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "exported_at": int(time.time()),
    }
    return base64.b64encode(json.dumps(snapshot).encode()).decode()


def import_snapshot(snapshot_str: str, passphrase: str) -> dict:
    """Decrypt and parse a shared vault snapshot.

    Args:
        snapshot_str: The base64-encoded snapshot produced by export_vault.
        passphrase: Passphrase used when the snapshot was exported.

    Returns:
        A dict mapping secret keys to their plaintext values.

    Raises:
        SharingError: If decryption fails or the format is invalid.
    """
    try:
        raw = json.loads(base64.b64decode(snapshot_str).decode())
    except Exception as exc:
        raise SharingError(f"Invalid snapshot format: {exc}") from exc

    if raw.get("version") != SHARE_FORMAT_VERSION:
        raise SharingError(
            f"Unsupported snapshot version: {raw.get('version')}"
        )

    try:
        salt = base64.b64decode(raw["salt"])
        ciphertext = base64.b64decode(raw["ciphertext"])
    except KeyError as exc:
        raise SharingError(f"Snapshot missing field: {exc}") from exc

    key = derive_key(passphrase, salt)
    try:
        plaintext = decrypt(ciphertext, key)
    except Exception as exc:
        raise SharingError("Decryption failed — wrong passphrase?") from exc

    try:
        return json.loads(plaintext.decode())
    except Exception as exc:
        raise SharingError(f"Failed to parse decrypted payload: {exc}") from exc
