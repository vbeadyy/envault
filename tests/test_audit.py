"""Tests for the audit log module."""

import json
import pytest
from pathlib import Path

from envault.audit import AuditEntry, AuditLog, audit_log_path, AUDIT_FILENAME


@pytest.fixture
def audit_path(tmp_path) -> Path:
    return tmp_path / AUDIT_FILENAME


@pytest.fixture
def audit(audit_path) -> AuditLog:
    return AuditLog(audit_path)


class TestAuditEntry:
    def test_to_dict_contains_required_fields(self):
        entry = AuditEntry(action="set", key="DB_URL", actor="alice")
        d = entry.to_dict()
        assert d["action"] == "set"
        assert d["key"] == "DB_URL"
        assert d["actor"] == "alice"
        assert "timestamp" in d

    def test_from_dict_roundtrip(self):
        entry = AuditEntry(action="get", key="SECRET", actor="bob", timestamp="2024-01-01T00:00:00+00:00")
        restored = AuditEntry.from_dict(entry.to_dict())
        assert restored.action == entry.action
        assert restored.key == entry.key
        assert restored.actor == entry.actor
        assert restored.timestamp == entry.timestamp

    def test_none_key_allowed(self):
        entry = AuditEntry(action="init", key=None, actor="carol")
        assert entry.key is None
        assert entry.to_dict()["key"] is None


class TestAuditLog:
    def test_record_creates_file(self, audit, audit_path):
        audit.record("init", actor="alice")
        assert audit_path.exists()

    def test_record_returns_entry(self, audit):
        entry = audit.record("set", key="FOO", actor="alice")
        assert isinstance(entry, AuditEntry)
        assert entry.action == "set"
        assert entry.key == "FOO"

    def test_entries_accumulate(self, audit):
        audit.record("set", key="A", actor="alice")
        audit.record("set", key="B", actor="bob")
        audit.record("get", key="A", actor="carol")
        assert len(audit.entries()) == 3

    def test_persistence_across_instances(self, audit_path):
        log1 = AuditLog(audit_path)
        log1.record("set", key="X", actor="dave")
        log2 = AuditLog(audit_path)
        assert len(log2.entries()) == 1
        assert log2.entries()[0].key == "X"

    def test_last_returns_most_recent(self, audit):
        for i in range(15):
            audit.record("set", key=f"KEY_{i}", actor="alice")
        recent = audit.last(5)
        assert len(recent) == 5
        assert recent[-1].key == "KEY_14"

    def test_file_is_valid_json(self, audit, audit_path):
        audit.record("init", actor="eve")
        data = json.loads(audit_path.read_text())
        assert isinstance(data, list)
        assert data[0]["action"] == "init"

    def test_corrupted_file_starts_fresh(self, audit_path):
        audit_path.write_text("not valid json", encoding="utf-8")
        log = AuditLog(audit_path)
        assert log.entries() == []


def test_audit_log_path_uses_parent_dir(tmp_path):
    vault_file = tmp_path / "subdir" / "my.vault"
    result = audit_log_path(vault_file)
    assert result == tmp_path / "subdir" / AUDIT_FILENAME
