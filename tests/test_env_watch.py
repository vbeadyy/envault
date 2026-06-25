"""Tests for envault.env_watch."""

import os
import time
import pytest

from envault.env_watch import (
    WatchError,
    WatchEvent,
    watch_vault,
    _stat,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vault_file(tmp_path):
    p = tmp_path / "test.vault"
    p.write_bytes(b"initial content")
    return p


# ---------------------------------------------------------------------------
# WatchEvent tests
# ---------------------------------------------------------------------------

class TestWatchEvent:
    def _make(self):
        return WatchEvent(
            path="/tmp/x.vault",
            previous_mtime=1000.0,
            current_mtime=2000.0,
            previous_size=10,
            current_size=20,
        )

    def test_to_dict_contains_required_fields(self):
        ev = self._make()
        d = ev.to_dict()
        for key in ("path", "previous_mtime", "current_mtime", "previous_size", "current_size"):
            assert key in d

    def test_to_dict_values(self):
        ev = self._make()
        d = ev.to_dict()
        assert d["path"] == "/tmp/x.vault"
        assert d["previous_size"] == 10
        assert d["current_size"] == 20

    def test_repr_contains_path(self):
        ev = self._make()
        assert "/tmp/x.vault" in repr(ev)


# ---------------------------------------------------------------------------
# _stat tests
# ---------------------------------------------------------------------------

def test_stat_returns_mtime_and_size(vault_file):
    mtime, size = _stat(str(vault_file))
    assert isinstance(mtime, float)
    assert size == len(b"initial content")


def test_stat_raises_on_missing_file(tmp_path):
    with pytest.raises(WatchError, match="not found"):
        _stat(str(tmp_path / "nonexistent.vault"))


# ---------------------------------------------------------------------------
# watch_vault tests
# ---------------------------------------------------------------------------

def test_watch_vault_raises_on_missing_file(tmp_path):
    with pytest.raises(WatchError):
        watch_vault(
            str(tmp_path / "no.vault"),
            callback=lambda e: None,
            interval=0.05,
            timeout=0.1,
        )


def test_watch_vault_raises_on_non_positive_interval(vault_file):
    with pytest.raises(WatchError, match="interval must be positive"):
        watch_vault(str(vault_file), callback=lambda e: None, interval=0)


def test_watch_vault_detects_change(vault_file):
    events = []

    calls = {"n": 0}

    def stop_after_event():
        return len(events) >= 1

    def write_after_first_poll():
        calls["n"] += 1
        if calls["n"] == 1:
            time.sleep(0.05)
            vault_file.write_bytes(b"updated content with more data")
        return len(events) >= 1

    watch_vault(
        str(vault_file),
        callback=events.append,
        interval=0.05,
        timeout=2.0,
        _stop_flag=write_after_first_poll,
    )

    assert len(events) >= 1
    ev = events[0]
    assert ev.path == str(vault_file)
    assert ev.current_size > ev.previous_size


def test_watch_vault_no_event_when_file_unchanged(vault_file):
    events = []
    counter = {"n": 0}

    def stop_after_3():
        counter["n"] += 1
        return counter["n"] >= 3

    watch_vault(
        str(vault_file),
        callback=events.append,
        interval=0.05,
        _stop_flag=stop_after_3,
    )

    assert events == []
