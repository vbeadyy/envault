"""Tests for envault.profiles.ProfileManager."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.profiles import ProfileManager, ProfileError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def profiles_path(tmp_path: Path) -> Path:
    return tmp_path / ".envault_profiles.json"


@pytest.fixture()
def mgr(profiles_path: Path) -> ProfileManager:
    pm = ProfileManager(profiles_path)
    pm.create("development", ["DB_URL", "DEBUG"])
    pm.create("production", ["DB_URL", "SECRET_KEY"])
    pm.save()
    return pm


# ---------------------------------------------------------------------------
# Creation & listing
# ---------------------------------------------------------------------------


class TestCreateProfile:
    def test_create_adds_profile(self, mgr: ProfileManager) -> None:
        mgr.create("staging")
        assert "staging" in mgr.list_profiles()

    def test_create_duplicate_raises(self, mgr: ProfileManager) -> None:
        with pytest.raises(ProfileError, match="already exists"):
            mgr.create("development")

    def test_list_profiles_sorted(self, mgr: ProfileManager) -> None:
        names = mgr.list_profiles()
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------


class TestKeyManagement:
    def test_get_keys_returns_correct_keys(self, mgr: ProfileManager) -> None:
        assert set(mgr.get_keys("development")) == {"DB_URL", "DEBUG"}

    def test_add_key_appends(self, mgr: ProfileManager) -> None:
        mgr.add_key("development", "NEW_KEY")
        assert "NEW_KEY" in mgr.get_keys("development")

    def test_add_key_idempotent(self, mgr: ProfileManager) -> None:
        mgr.add_key("development", "DB_URL")
        assert mgr.get_keys("development").count("DB_URL") == 1

    def test_remove_key(self, mgr: ProfileManager) -> None:
        mgr.remove_key("development", "DEBUG")
        assert "DEBUG" not in mgr.get_keys("development")

    def test_remove_missing_key_raises(self, mgr: ProfileManager) -> None:
        with pytest.raises(ProfileError, match="not in profile"):
            mgr.remove_key("development", "NONEXISTENT")

    def test_get_keys_unknown_profile_raises(self, mgr: ProfileManager) -> None:
        with pytest.raises(ProfileError, match="does not exist"):
            mgr.get_keys("ghost")


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_save_and_reload(self, profiles_path: Path, mgr: ProfileManager) -> None:
        mgr.add_key("production", "NEW_PROD_KEY")
        mgr.save()

        reloaded = ProfileManager(profiles_path)
        assert "NEW_PROD_KEY" in reloaded.get_keys("production")

    def test_delete_persists(self, profiles_path: Path, mgr: ProfileManager) -> None:
        mgr.delete("development")
        mgr.save()

        reloaded = ProfileManager(profiles_path)
        assert "development" not in reloaded.list_profiles()

    def test_load_nonexistent_file_starts_empty(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path / "no_file.json")
        assert pm.list_profiles() == []
