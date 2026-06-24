"""Backup and restore support for vault files."""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import List


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


BACKUP_SUFFIX = ".bak"
_MAX_BACKUPS = 10


def _backup_dir(vault_path: Path) -> Path:
    """Return the directory used to store backups for *vault_path*."""
    return vault_path.parent / ".envault_backups"


def create_backup(vault_path: Path) -> Path:
    """Copy *vault_path* into the backup directory with a timestamp suffix.

    Returns the path of the newly created backup file.
    Raises :class:`BackupError` if the vault file does not exist.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise BackupError(f"Vault file not found: {vault_path}")

    backup_dir = _backup_dir(vault_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    backup_name = f"{vault_path.stem}_{timestamp}{BACKUP_SUFFIX}"
    dest = backup_dir / backup_name
    shutil.copy2(vault_path, dest)

    _prune_backups(backup_dir, vault_path.stem)
    return dest


def list_backups(vault_path: Path) -> List[Path]:
    """Return existing backups for *vault_path*, oldest first."""
    backup_dir = _backup_dir(Path(vault_path))
    if not backup_dir.exists():
        return []
    stem = Path(vault_path).stem
    backups = sorted(
        backup_dir.glob(f"{stem}_*{BACKUP_SUFFIX}"),
        key=lambda p: p.stat().st_mtime,
    )
    return backups


def restore_backup(backup_path: Path, vault_path: Path) -> None:
    """Overwrite *vault_path* with the contents of *backup_path*.

    Raises :class:`BackupError` if *backup_path* does not exist.
    """
    backup_path = Path(backup_path)
    vault_path = Path(vault_path)
    if not backup_path.exists():
        raise BackupError(f"Backup file not found: {backup_path}")
    shutil.copy2(backup_path, vault_path)


def _prune_backups(backup_dir: Path, stem: str) -> None:
    """Remove oldest backups so that at most *_MAX_BACKUPS* are kept."""
    backups = sorted(
        backup_dir.glob(f"{stem}_*{BACKUP_SUFFIX}"),
        key=lambda p: p.stat().st_mtime,
    )
    for old in backups[:-_MAX_BACKUPS]:
        old.unlink(missing_ok=True)
