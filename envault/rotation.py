"""Key rotation support for envault vaults."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

from envault.crypto import derive_key, encrypt, decrypt

if TYPE_CHECKING:
    from envault.vault import Vault


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    vault: "Vault",
    old_passphrase: str,
    new_passphrase: str,
) -> dict[str, str]:
    """Re-encrypt all vault secrets under a new passphrase.

    Returns a mapping of {key: new_ciphertext} without modifying the
    vault in-place — the caller decides whether to persist the result.
    """
    old_key = derive_key(old_passphrase, vault.salt)
    new_key = derive_key(new_passphrase, vault.salt)

    rotated: dict[str, str] = {}
    for name, ciphertext in vault.secrets.items():
        try:
            plaintext = decrypt(old_key, ciphertext)
        except Exception as exc:
            raise RotationError(
                f"Failed to decrypt '{name}' with the old passphrase: {exc}"
            ) from exc
        rotated[name] = encrypt(new_key, plaintext)

    return rotated


def apply_rotation(
    vault: "Vault",
    old_passphrase: str,
    new_passphrase: str,
) -> None:
    """Rotate the vault key in-place and persist the changes."""
    rotated = rotate_key(vault, old_passphrase, new_passphrase)
    vault.secrets.update(rotated)
    vault.save(new_passphrase)
