"""Vault locking: prevent concurrent access via lock files."""

from __future__ import annotations

import os
import time
from pathlib import Path

LOCK_SUFFIX = ".lock"
STALE_AFTER_SECONDS = 30


class LockError(Exception):
    """Raised when a vault lock cannot be acquired or released."""


def _lock_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(vault_path.suffix + LOCK_SUFFIX)


def acquire_lock(vault_path: Path, *, timeout: float = 5.0) -> Path:
    """Acquire a lock for *vault_path*.

    Writes a lock file containing the current PID and timestamp.  Retries
    for *timeout* seconds before raising :class:`LockError`.  Stale locks
    older than :data:`STALE_AFTER_SECONDS` are removed automatically.

    Returns the path of the created lock file.
    """
    lock = _lock_path(vault_path)
    deadline = time.monotonic() + timeout

    while True:
        if lock.exists():
            try:
                data = lock.read_text().strip().split()
                created_at = float(data[1]) if len(data) >= 2 else 0.0
                if time.time() - created_at > STALE_AFTER_SECONDS:
                    lock.unlink(missing_ok=True)
            except (OSError, ValueError):
                lock.unlink(missing_ok=True)

        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                fh.write(f"{os.getpid()} {time.time():.6f}\n")
            return lock
        except FileExistsError:
            pass

        if time.monotonic() >= deadline:
            raise LockError(
                f"Could not acquire lock for '{vault_path}' within {timeout}s. "
                f"Remove '{lock}' if no other process is using the vault."
            )
        time.sleep(0.05)


def release_lock(lock_path: Path) -> None:
    """Release (delete) a previously acquired lock file.

    Raises :class:`LockError` if the lock no longer exists or belongs to a
    different PID, which would indicate a logic error in the caller.
    """
    if not lock_path.exists():
        raise LockError(f"Lock file '{lock_path}' does not exist; cannot release.")

    try:
        pid_str = lock_path.read_text().strip().split()[0]
        if int(pid_str) != os.getpid():
            raise LockError(
                f"Lock file '{lock_path}' is owned by PID {pid_str}, not {os.getpid()}."
            )
    except (OSError, IndexError, ValueError) as exc:
        raise LockError(f"Malformed lock file '{lock_path}': {exc}") from exc

    lock_path.unlink(missing_ok=True)


def is_locked(vault_path: Path) -> bool:
    """Return *True* if a (non-stale) lock file exists for *vault_path*."""
    lock = _lock_path(vault_path)
    if not lock.exists():
        return False
    try:
        data = lock.read_text().strip().split()
        created_at = float(data[1]) if len(data) >= 2 else 0.0
        return time.time() - created_at <= STALE_AFTER_SECONDS
    except (OSError, ValueError):
        return False
