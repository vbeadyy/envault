"""Tests for envault.history module."""

from __future__ import annotations

import json
import time

import pytest

from envault.history import History, HistoryError, Snapshot, MAX_SNAPSHOTS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def hist_path(tmp_path):
    return tmp_path / "history.json"


@pytest.fixture()
def hist(hist_path):
    return History(hist_path)


@pytest.fixture()
def populated_hist(hist):
    hist.push({"KEY": "val1"}, label="first")
    hist.push({"KEY": "val2"}, label="second")
    hist.push({"KEY": "val3", "OTHER": "x"}, label="third")
    return hist


# ---------------------------------------------------------------------------
# Snapshot unit tests
# ---------------------------------------------------------------------------

class TestSnapshot:
    def test_to_dict_contains_required_fields(self):
        snap = Snapshot(data={"A": "1"}, label="lbl")
        d = snap.to_dict()
        assert "timestamp" in d
        assert "label" in d
        assert "data" in d

    def test_from_dict_roundtrip(self):
        snap = Snapshot(data={"A": "1"}, label="lbl", timestamp=12345.0)
        restored = Snapshot.from_dict(snap.to_dict())
        assert restored.data == snap.data
        assert restored.label == snap.label
        assert restored.timestamp == snap.timestamp

    def test_timestamp_defaults_to_now(self):
        before = time.time()
        snap = Snapshot(data={})
        after = time.time()
        assert before <= snap.timestamp <= after


# ---------------------------------------------------------------------------
# History persistence
# ---------------------------------------------------------------------------

class TestHistoryPersistence:
    def test_empty_on_new_file(self, hist):
        assert len(hist) == 0

    def test_push_creates_file(self, hist, hist_path):
        hist.push({"K": "v"})
        assert hist_path.exists()

    def test_push_persists_across_reload(self, hist_path):
        h1 = History(hist_path)
        h1.push({"X": "1"}, label="orig")
        h2 = History(hist_path)
        assert len(h2) == 1
        assert h2.get(0).label == "orig"

    def test_corrupt_file_raises(self, hist_path):
        hist_path.write_text("NOT JSON", encoding="utf-8")
        with pytest.raises(HistoryError, match="Corrupt"):
            History(hist_path)


# ---------------------------------------------------------------------------
# History operations
# ---------------------------------------------------------------------------

class TestHistoryOperations:
    def test_list_newest_first(self, populated_hist):
        snaps = populated_hist.list()
        assert snaps[0].label == "third"
        assert snaps[-1].label == "first"

    def test_get_index_zero_is_newest(self, populated_hist):
        snap = populated_hist.get(0)
        assert snap.label == "third"

    def test_get_out_of_range_raises(self, populated_hist):
        with pytest.raises(HistoryError, match="No snapshot"):
            populated_hist.get(999)

    def test_push_invalid_data_raises(self, hist):
        with pytest.raises(HistoryError):
            hist.push("not a dict")  # type: ignore[arg-type]

    def test_clear_removes_all(self, populated_hist):
        populated_hist.clear()
        assert len(populated_hist) == 0

    def test_max_snapshots_enforced(self, hist):
        for i in range(MAX_SNAPSHOTS + 5):
            hist.push({"i": str(i)})
        assert len(hist) == MAX_SNAPSHOTS

    def test_push_copies_data(self, hist):
        d = {"K": "v"}
        hist.push(d)
        d["K"] = "mutated"
        assert hist.get(0).data["K"] == "v"
