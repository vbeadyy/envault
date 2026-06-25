"""Clone (deep-copy) all keys from one vault profile into another."""

from __future__ import annotations

from typing import List, Optional


class CloneError(Exception):
    """Raised when a clone operation fails."""


def clone_vault(
    source: object,
    destination: object,
    passphrase: str,
    *,
    prefix: Optional[str] = None,
    overwrite: bool = False,
) -> List[str]:
    """Copy all keys from *source* vault into *destination* vault.

    Parameters
    ----------
    source:
        A :class:`~envault.vault.Vault` instance to read from.
    destination:
        A :class:`~envault.vault.Vault` instance to write into.
    passphrase:
        Passphrase used to decrypt values from *source* and re-encrypt them
        for *destination* (both vaults must share the same passphrase).
    prefix:
        Optional string prefix.  When supplied only keys whose names start
        with *prefix* are copied.
    overwrite:
        When ``False`` (default) an existing key in *destination* raises
        :class:`CloneError`.  When ``True`` existing keys are silently
        overwritten.

    Returns
    -------
    list[str]
        Sorted list of key names that were copied.
    """
    if source is destination:
        raise CloneError("source and destination vaults must be different objects")

    keys: List[str] = sorted(source.list_keys())
    if prefix is not None:
        keys = [k for k in keys if k.startswith(prefix)]

    if not overwrite:
        dest_keys = set(destination.list_keys())
        conflicts = [k for k in keys if k in dest_keys]
        if conflicts:
            raise CloneError(
                f"keys already exist in destination (use overwrite=True): {conflicts}"
            )

    copied: List[str] = []
    for key in keys:
        value = source.get(key, passphrase)
        destination.set(key, value, passphrase)
        copied.append(key)

    return copied
