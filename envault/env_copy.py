"""Copy keys between vaults or within the same vault."""
from __future__ import annotations

from typing import Optional

from envault.vault import Vault, VaultError


class CopyError(Exception):
    """Raised when a copy operation fails."""


def copy_key(
    src_vault: Vault,
    dst_vault: Vault,
    src_key: str,
    dst_key: Optional[str] = None,
    overwrite: bool = False,
) -> str:
    """Copy *src_key* from *src_vault* into *dst_vault*.

    Parameters
    ----------
    src_vault:  vault to read the value from.
    dst_vault:  vault to write the value to.
    src_key:    key name in the source vault.
    dst_key:    key name in the destination vault; defaults to *src_key*.
    overwrite:  if ``False`` (default) and *dst_key* already exists in
                *dst_vault*, a :class:`CopyError` is raised.

    Returns
    -------
    The destination key name that was written.
    """
    if not src_key:
        raise CopyError("src_key must not be empty")

    dst_key = dst_key or src_key

    if not dst_key:
        raise CopyError("dst_key must not be empty")

    try:
        value = src_vault.get(src_key)
    except VaultError as exc:
        raise CopyError(f"Source key {src_key!r} not found: {exc}") from exc

    existing_keys = dst_vault.list_keys()
    if dst_key in existing_keys and not overwrite:
        raise CopyError(
            f"Destination key {dst_key!r} already exists. "
            "Pass overwrite=True to replace it."
        )

    dst_vault.set(dst_key, value)
    return dst_key


def copy_keys(
    src_vault: Vault,
    dst_vault: Vault,
    keys: list[str],
    overwrite: bool = False,
) -> list[str]:
    """Copy multiple keys from *src_vault* to *dst_vault*.

    Returns the list of destination key names that were written.
    Raises :class:`CopyError` on the first failure.
    """
    if not keys:
        raise CopyError("keys list must not be empty")

    copied: list[str] = []
    for key in keys:
        dst_key = copy_key(src_vault, dst_vault, key, overwrite=overwrite)
        copied.append(dst_key)
    return copied
