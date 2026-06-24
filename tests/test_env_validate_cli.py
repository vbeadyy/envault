"""Tests for env_validate_cli commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envault.env_validate_cli import cmd_validate_run, cmd_validate_key
from envault.env_validate import ValidationIssue, Severity


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_vault():
    vault = MagicMock()
    vault.get.return_value = "somevalue"
    return vault


def _patch_open(vault):
    return patch("envault.env_validate_cli._open_vault", return_value=vault)


def _patch_passphrase():
    return patch("envault.env_validate_cli._prompt_passphrase", return_value="secret")


class TestCmdValidateRun:
    def test_no_issues_prints_success(self, runner, mock_vault):
        with _patch_passphrase(), _patch_open(mock_vault):
            with patch("envault.env_validate_cli.validate_vault", return_value=[]):
                result = runner.invoke(cmd_validate_run, ["fake.vault"])
        assert result.exit_code == 0
        assert "No validation issues found" in result.output

    def test_issues_are_printed(self, runner, mock_vault):
        issue = ValidationIssue(
            key="EMPTY_VAR",
            message="Value is empty",
            severity=Severity.WARNING,
        )
        with _patch_passphrase(), _patch_open(mock_vault):
            with patch("envault.env_validate_cli.validate_vault", return_value=[issue]):
                result = runner.invoke(cmd_validate_run, ["fake.vault"])
        assert "EMPTY_VAR" in result.output
        assert "Value is empty" in result.output

    def test_fail_on_error_exits_nonzero(self, runner, mock_vault):
        issue = ValidationIssue(
            key="BAD_KEY",
            message="Invalid format",
            severity=Severity.ERROR,
        )
        with _patch_passphrase(), _patch_open(mock_vault):
            with patch("envault.env_validate_cli.validate_vault", return_value=[issue]):
                result = runner.invoke(
                    cmd_validate_run, ["fake.vault", "--fail-on-error"]
                )
        assert result.exit_code != 0

    def test_warnings_do_not_trigger_fail_on_error(self, runner, mock_vault):
        issue = ValidationIssue(
            key="WARN_KEY",
            message="Minor issue",
            severity=Severity.WARNING,
        )
        with _patch_passphrase(), _patch_open(mock_vault):
            with patch("envault.env_validate_cli.validate_vault", return_value=[issue]):
                result = runner.invoke(
                    cmd_validate_run, ["fake.vault", "--fail-on-error"]
                )
        assert result.exit_code == 0


class TestCmdValidateKey:
    def test_valid_key_prints_success(self, runner, mock_vault):
        with _patch_passphrase(), _patch_open(mock_vault):
            with patch("envault.env_validate_cli.validate_key", return_value=[]):
                result = runner.invoke(cmd_validate_key, ["fake.vault", "MY_KEY"])
        assert "passed all validation" in result.output
        assert result.exit_code == 0

    def test_missing_key_exits_nonzero(self, runner, mock_vault):
        mock_vault.get.side_effect = KeyError("MY_KEY")
        with _patch_passphrase(), _patch_open(mock_vault):
            result = runner.invoke(cmd_validate_key, ["fake.vault", "MY_KEY"])
        assert result.exit_code != 0
        assert "not found" in result.output
