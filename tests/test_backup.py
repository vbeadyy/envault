"""Tests for envault.backup."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.backup import (
    BackupError,
    _MAX_BACKUPS,
    _backup_dir,
    create_backup,
    list_backups,
    restore_backup,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_text("original content")
    return p


class TestCreateBackup:
    def test_returns_path(self, vault_file: Path) -> None:
        result = create_backup(vault_file)
        assert isinstance(result, Path)

    def test_backup_file_exists(self, vault_file: Path) -> None:
        dest = create_backup(vault_file)
        assert dest.exists()

    def test_backup_stored_in_backup_dir(self, vault_file: Path) -> None:
        dest = create_backup(vault_file)
        assert dest.parent == _backup_dir(vault_file)

    def test_backup_content_matches(self, vault_file: Path) -> None:
        dest = create_backup(vault_file)
        assert dest.read_text() == vault_file.read_text()

    def test_missing_vault_raises(self, tmp_path: Path) -> None:
        with pytest.raises(BackupError, match="not found"):
            create_backup(tmp_path / "nonexistent.vault")

    def test_multiple_backups_have_unique_names(self, vault_file: Path) -> None:
        a = create_backup(vault_file)
        time.sleep(1.1)  # ensure different timestamp
        b = create_backup(vault_file)
        assert a != b


class TestListBackups:
    def test_empty_when_no_backups(self, vault_file: Path) -> None:
        assert list_backups(vault_file) == []

    def test_lists_created_backups(self, vault_file: Path) -> None:
        create_backup(vault_file)
        backups = list_backups(vault_file)
        assert len(backups) == 1

    def test_oldest_first_ordering(self, vault_file: Path) -> None:
        first = create_backup(vault_file)
        time.sleep(1.1)
        second = create_backup(vault_file)
        backups = list_backups(vault_file)
        assert backups[0] == first
        assert backups[1] == second


class TestRestoreBackup:
    def test_restores_content(self, vault_file: Path) -> None:
        original = vault_file.read_text()
        backup = create_backup(vault_file)
        vault_file.write_text("modified content")
        restore_backup(backup, vault_file)
        assert vault_file.read_text() == original

    def test_missing_backup_raises(self, vault_file: Path, tmp_path: Path) -> None:
        with pytest.raises(BackupError, match="not found"):
            restore_backup(tmp_path / "ghost.bak", vault_file)


class TestPruneBackups:
    def test_prunes_old_backups(self, vault_file: Path) -> None:
        for _ in range(_MAX_BACKUPS + 3):
            time.sleep(0.05)
            create_backup(vault_file)
        remaining = list_backups(vault_file)
        assert len(remaining) <= _MAX_BACKUPS
