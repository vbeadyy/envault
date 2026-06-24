"""Tests for envault.env_lint."""

import pytest
from envault.env_lint import LintIssue, lint_key, lint_value, lint_vault


# ---------------------------------------------------------------------------
# LintIssue helpers
# ---------------------------------------------------------------------------

class TestLintIssue:
    def test_to_dict_contains_required_fields(self):
        issue = LintIssue(key="FOO", message="bad", severity="error")
        d = issue.to_dict()
        assert "key" in d and "message" in d and "severity" in d

    def test_to_dict_values(self):
        issue = LintIssue(key="BAR", message="test msg", severity="warning")
        assert issue.to_dict() == {"key": "BAR", "message": "test msg", "severity": "warning"}

    def test_default_severity_is_warning(self):
        issue = LintIssue(key="X", message="m")
        assert issue.severity == "warning"


# ---------------------------------------------------------------------------
# lint_key
# ---------------------------------------------------------------------------

class TestLintKey:
    def test_valid_key_returns_none(self):
        assert lint_key("DATABASE_URL") is None

    def test_valid_single_letter(self):
        assert lint_key("A") is None

    def test_lowercase_key_returns_warning(self):
        issue = lint_key("database_url")
        assert issue is not None
        assert issue.severity == "warning"

    def test_starts_with_digit_returns_warning(self):
        issue = lint_key("1_BAD")
        assert issue is not None

    def test_empty_key_returns_error(self):
        issue = lint_key("")
        assert issue is not None
        assert issue.severity == "error"

    def test_key_with_hyphen_returns_warning(self):
        issue = lint_key("MY-KEY")
        assert issue is not None


# ---------------------------------------------------------------------------
# lint_value
# ---------------------------------------------------------------------------

class TestLintValue:
    def test_valid_value_returns_none(self):
        assert lint_value("FOO", "bar123") is None

    def test_leading_space_returns_warning(self):
        issue = lint_value("FOO", " bar")
        assert issue is not None
        assert issue.severity == "warning"

    def test_trailing_space_returns_warning(self):
        issue = lint_value("FOO", "bar ")
        assert issue is not None

    def test_empty_value_returns_warning(self):
        issue = lint_value("FOO", "")
        assert issue is not None
        assert issue.severity == "warning"


# ---------------------------------------------------------------------------
# lint_vault
# ---------------------------------------------------------------------------

class TestLintVault:
    def test_clean_vault_returns_empty_list(self):
        issues = lint_vault({"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc"})
        assert issues == []

    def test_detects_lowercase_key(self):
        issues = lint_vault({"bad_key": "value"})
        keys = [i.key for i in issues]
        assert "bad_key" in keys

    def test_detects_empty_value(self):
        issues = lint_vault({"FOO": ""})
        assert any(i.key == "FOO" for i in issues)

    def test_detects_case_insensitive_duplicate(self):
        issues = lint_vault({"FOO": "a", "foo": "b"})
        severities = [i.severity for i in issues]
        assert "error" in severities

    def test_multiple_issues_accumulated(self):
        issues = lint_vault({"bad": " leading", "BAD": "ok"})
        # 'bad' triggers key warning + value warning; 'BAD' is fine but
        # 'bad'/'BAD' are case-insensitive duplicates
        assert len(issues) >= 2

    def test_empty_vault_returns_empty_list(self):
        assert lint_vault({}) == []
