"""Tests for envault.templates.TemplateManager."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.templates import TemplateError, TemplateManager


@pytest.fixture()
def tpl_path(tmp_path: Path) -> Path:
    return tmp_path / "templates.json"


@pytest.fixture()
def mgr(tpl_path: Path) -> TemplateManager:
    return TemplateManager(tpl_path)


class TestCreateTemplate:
    def test_create_adds_template(self, mgr: TemplateManager) -> None:
        mgr.create("base", ["DB_URL", "SECRET_KEY"])
        assert "base" in mgr.list_templates()

    def test_create_stores_empty_values(self, mgr: TemplateManager) -> None:
        mgr.create("base", ["DB_URL"])
        assert mgr.get("base") == {"DB_URL": ""}

    def test_create_duplicate_raises(self, mgr: TemplateManager) -> None:
        mgr.create("base", ["A"])
        with pytest.raises(TemplateError, match="already exists"):
            mgr.create("base", ["B"])

    def test_empty_name_raises(self, mgr: TemplateManager) -> None:
        with pytest.raises(TemplateError, match="must not be empty"):
            mgr.create("", ["A"])

    def test_empty_keys_raises(self, mgr: TemplateManager) -> None:
        with pytest.raises(TemplateError, match="at least one key"):
            mgr.create("base", [])


class TestDeleteTemplate:
    def test_delete_removes_template(self, mgr: TemplateManager) -> None:
        mgr.create("base", ["A"])
        mgr.delete("base")
        assert "base" not in mgr.list_templates()

    def test_delete_unknown_raises(self, mgr: TemplateManager) -> None:
        with pytest.raises(TemplateError, match="not found"):
            mgr.delete("ghost")


class TestPersistence:
    def test_save_and_reload(self, tpl_path: Path) -> None:
        mgr = TemplateManager(tpl_path)
        mgr.create("web", ["PORT", "HOST"])
        mgr2 = TemplateManager(tpl_path)
        assert "web" in mgr2.list_templates()
        assert set(mgr2.get("web").keys()) == {"PORT", "HOST"}


class TestApplyTemplate:
    def test_apply_fills_known_keys(self, mgr: TemplateManager) -> None:
        mgr.create("base", ["DB", "PORT"])
        result = mgr.apply("base", {"DB": "postgres://localhost/dev", "PORT": "5432"})
        assert result["DB"] == "postgres://localhost/dev"
        assert result["PORT"] == "5432"

    def test_apply_defaults_missing_to_empty(self, mgr: TemplateManager) -> None:
        mgr.create("base", ["DB", "PORT"])
        result = mgr.apply("base", {"DB": "sqlite"})
        assert result["PORT"] == ""

    def test_apply_ignores_extra_values(self, mgr: TemplateManager) -> None:
        mgr.create("base", ["A"])
        result = mgr.apply("base", {"A": "1", "EXTRA": "ignored"})
        assert "EXTRA" not in result

    def test_apply_unknown_template_raises(self, mgr: TemplateManager) -> None:
        with pytest.raises(TemplateError, match="not found"):
            mgr.apply("ghost", {})
