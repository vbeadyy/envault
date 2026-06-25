"""Rename keys within a vault, with optional audit logging."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envault.vault import Vault


class RenameError(Exception):
    """Raised when a rename operation fails."""


def rename_key(vault: "Vault", old_key: str, new_key: str, *, overwrite: bool = False) -> None:
    """Rename *old_key* to *new_key* inside *vault*.

    Parameters
    ----------
    vault:      The vault to operate on.
    old_key:    Existing key name.
    new_key:    Target key name.
    overwrite:  If *True*, silently overwrite *new_key* when it already exists.
                Defaults to *False* (raises :class:`RenameError`).

    Raises
    ------
    RenameError
        If *old_key* does not exist, *new_key* is invalid, or *new_key*
        already exists and *overwrite* is *False*.
    """
    if not old_key or not old_key.strip():
        raise RenameError("old_key must be a non-empty string")
    if not new_key or not new_key.strip():
        raise RenameError("new_key must be a non-empty string")

    old_key = old_key.strip()
    new_key = new_key.strip()

    if old_key == new_key:
        raise RenameError("old_key and new_key are identical")

    existing_keys = vault.list_keys()

    if old_key not in existing_keys:
        raise RenameError(f"Key '{old_key}' does not exist in the vault")

    if new_key in existing_keys and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists; pass overwrite=True to replace it"
        )

    value = vault.get(old_key)
    vault.set(new_key, value)
    vault.delete(old_key)


def rename_keys(vault: "Vault", mapping: dict[str, str], *, overwrite: bool = False) -> list[str]:
    """Bulk-rename keys according to *mapping* ``{old_key: new_key}``.

    Renames are applied one at a time in iteration order.  If any rename
    fails the already-applied renames are **not** rolled back.

    Returns a list of successfully renamed old keys.
    """
    if not mapping:
        raise RenameError("mapping must not be empty")

    renamed: list[str] = []
    for old_key, new_key in mapping.items():
        rename_key(vault, old_key, new_key, overwrite=overwrite)
        renamed.append(old_key)
    return renamed
