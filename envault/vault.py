"""Vault module for reading, writing, and managing encrypted .env vault files."""

import json
import os
import secrets
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import derive_key, encrypt, decrypt

DEFAULT_VAULT_FILENAME = ".envault"


class VaultError(Exception):
    """Raised when a vault operation fails."""


class Vault:
    """Represents an encrypted .env vault stored on disk."""

    def __init__(self, path: Path, passphrase: str):
        self.path = Path(path)
        self.passphrase = passphrase
        self._data: Dict[str, str] = {}
        self._salt: Optional[bytes] = None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load and decrypt the vault from disk."""
        if not self.path.exists():
            raise VaultError(f"Vault file not found: {self.path}")

        raw = self.path.read_bytes()
        if len(raw) < 16:
            raise VaultError("Vault file is too short to be valid.")
        try:
            # First 16 bytes are the salt used for key derivation.
            self._salt = raw[:16]
            ciphertext = raw[16:]
            key = derive_key(self.passphrase, self._salt)
            plaintext = decrypt(key, ciphertext)
            self._data = json.loads(plaintext.decode())
        except VaultError:
            raise
        except Exception as exc:
            raise VaultError("Failed to decrypt vault — wrong passphrase?") from exc

    def save(self) -> None:
        """Encrypt and write the vault to disk."""
        if self._salt is None:
            self._salt = secrets.token_bytes(16)
        key = derive_key(self.passphrase, self._salt)
        plaintext = json.dumps(self._data).encode()
        ciphertext = encrypt(key, plaintext)
        self.path.write_bytes(self._salt + ciphertext)

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Store a key/value pair in the vault."""
        self._data[key] = value

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value by key, or None if not present."""
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        """Remove a key from the vault. Returns True if the key existed."""
        return self._data.pop(key, None) is not None

    def all(self) -> Dict[str, str]:
        """Return a copy of all stored key/value pairs."""
        return dict(self._data)

    def export_env(self) -> str:
        """Render vault contents as a .env-formatted string."""
        lines = [f'{k}={v}' for k, v in sorted(self._data.items())]
        return os.linesep.join(lines)

    def import_env(self, env_string: str) -> int:
        """Parse a .env-formatted string and load entries into the vault.

        Lines starting with '#' are treated as comments and skipped.
        Lines without an '=' separator are also skipped.

        Returns the number of key/value pairs imported.
        """
        count = 0
        for line in env_string.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            self._data[key.strip()] = value.strip()
            count += 1
        return count

    def __len__(self) -> int:
        return len(self._data)
