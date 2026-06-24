"""Tests for envault.env_merge."""

import pytest

from envault.env_merge import (
    ConflictStrategy,
    MergeConflict,
    MergeError,
    MergeResult,
    merge_vaults,
)


# ---------------------------------------------------------------------------
# MergeConflict
# ---------------------------------------------------------------------------

class TestMergeConflict:
    def test_to_dict_contains_required_fields(self):
        c = MergeConflict(key="FOO", our_value="a", their_value="b")
        d = c.to_dict()
        assert "key" in d
        assert "our_value" in d
        assert "their_value" in d

    def test_to_dict_values(self):
        c = MergeConflict(key="X", our_value="1", their_value="2")
        d = c.to_dict()
        assert d["key"] == "X"
        assert d["our_value"] == "1"
        assert d["their_value"] == "2"


# ---------------------------------------------------------------------------
# merge_vaults — happy path
# ---------------------------------------------------------------------------

class TestMergeVaults:
    def test_no_overlap_all_added(self):
        result = merge_vaults({"A": "1"}, {"B": "2"})
        assert result.merged == {"A": "1", "B": "2"}
        assert "B" in result.added_keys
        assert "A" in result.removed_keys

    def test_identical_vaults_no_conflicts(self):
        base = {"A": "1", "B": "2"}
        result = merge_vaults(base, base.copy())
        assert not result.has_conflicts
        assert result.merged == base

    def test_incoming_only_key_is_added(self):
        result = merge_vaults({"A": "1"}, {"A": "1", "B": "new"})
        assert "B" in result.added_keys
        assert result.merged["B"] == "new"

    def test_base_only_key_recorded_as_removed(self):
        result = merge_vaults({"A": "1", "OLD": "x"}, {"A": "1"})
        assert "OLD" in result.removed_keys
        assert result.merged["OLD"] == "x"


# ---------------------------------------------------------------------------
# Conflict resolution strategies
# ---------------------------------------------------------------------------

class TestConflictStrategies:
    BASE = {"K": "original"}
    INCOMING = {"K": "changed"}

    def test_strategy_ours_keeps_base_value(self):
        result = merge_vaults(self.BASE, self.INCOMING, ConflictStrategy.OURS)
        assert result.merged["K"] == "original"
        assert result.has_conflicts

    def test_strategy_theirs_takes_incoming_value(self):
        result = merge_vaults(self.BASE, self.INCOMING, ConflictStrategy.THEIRS)
        assert result.merged["K"] == "changed"
        assert result.has_conflicts

    def test_strategy_error_raises_on_conflict(self):
        with pytest.raises(MergeError, match="Conflict on key"):
            merge_vaults(self.BASE, self.INCOMING, ConflictStrategy.ERROR)

    def test_conflict_recorded_regardless_of_strategy(self):
        for strategy in (ConflictStrategy.OURS, ConflictStrategy.THEIRS):
            result = merge_vaults(self.BASE, self.INCOMING, strategy)
            assert len(result.conflicts) == 1
            assert result.conflicts[0].key == "K"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_non_dict_base_raises(self):
        with pytest.raises(MergeError):
            merge_vaults("not-a-dict", {})

    def test_non_dict_incoming_raises(self):
        with pytest.raises(MergeError):
            merge_vaults({}, ["list"])

    def test_empty_vaults_produce_empty_result(self):
        result = merge_vaults({}, {})
        assert result.merged == {}
        assert not result.has_conflicts
