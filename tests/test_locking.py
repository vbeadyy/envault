"""Tests for envault.locking."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from envault.locking import (
    LockError,
    STALE_AFTER_SECONDS,
    acquire_lock,
    is_locked,
    release_lock,
    _lock_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_text("{}")
    return p


class TestAcquireLock:
    def test_creates_lock_file(self, vault_path):
        lock = acquire_lock(vault_path)
        assert lock.exists()
        lock.unlink()

    def test_lock_file_contains_pid_and_timestamp(self, vault_path):
        lock = acquire_lock(vault_path)
        parts = lock.read_text().strip().split()
        assert len(parts) == 2
        assert int(parts[0]) == os.getpid()
        assert float(parts[1]) > 0
        lock.unlink()

    def test_lock_path_derived_from_vault_path(self, vault_path):
        lock = acquire_lock(vault_path)
        assert lock == _lock_path(vault_path)
        lock.unlink()

    def test_raises_when_already_locked(self, vault_path):
        lock = acquire_lock(vault_path)
        try:
            with pytest.raises(LockError):
                acquire_lock(vault_path, timeout=0.15)
        finally:
            lock.unlink()

    def test_acquires_after_stale_lock_removed(self, vault_path):
        lock_file = _lock_path(vault_path)
        stale_time = time.time() - (STALE_AFTER_SECONDS + 5)
        lock_file.write_text(f"99999 {stale_time:.6f}\n")

        lock = acquire_lock(vault_path, timeout=1.0)
        assert lock.exists()
        lock.unlink()


class TestReleaseLock:
    def test_removes_lock_file(self, vault_path):
        lock = acquire_lock(vault_path)
        release_lock(lock)
        assert not lock.exists()

    def test_raises_if_lock_missing(self, vault_path):
        lock = _lock_path(vault_path)
        with pytest.raises(LockError, match="does not exist"):
            release_lock(lock)

    def test_raises_if_wrong_pid(self, vault_path):
        lock_file = _lock_path(vault_path)
        lock_file.write_text(f"1 {time.time():.6f}\n")  # PID 1 is init, not us
        with pytest.raises(LockError, match="owned by PID"):
            release_lock(lock_file)
        lock_file.unlink(missing_ok=True)


class TestIsLocked:
    def test_false_when_no_lock(self, vault_path):
        assert not is_locked(vault_path)

    def test_true_when_locked(self, vault_path):
        lock = acquire_lock(vault_path)
        assert is_locked(vault_path)
        lock.unlink()

    def test_false_for_stale_lock(self, vault_path):
        lock_file = _lock_path(vault_path)
        stale_time = time.time() - (STALE_AFTER_SECONDS + 10)
        lock_file.write_text(f"99999 {stale_time:.6f}\n")
        assert not is_locked(vault_path)
        lock_file.unlink()
