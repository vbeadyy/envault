"""Linting/validation rules for .env variable keys and values."""

import re
from dataclasses import dataclass, field
from typing import List, Optional


class LintError(Exception):
    """Raised when a lint check encounters an unrecoverable problem."""


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def to_dict(self) -> dict:
        return {"key": self.key, "message": self.message, "severity": self.severity}

    def __repr__(self) -> str:  # pragma: no cover
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')
_WHITESPACE_VALUE = re.compile(r'^\s|\s$')


def lint_key(key: str) -> Optional[LintIssue]:
    """Return a LintIssue if *key* violates naming conventions, else None."""
    if not key:
        return LintIssue(key=key, message="Key must not be empty.", severity="error")
    if not _KEY_PATTERN.match(key):
        return LintIssue(
            key=key,
            message=(
                "Key should be uppercase letters, digits, and underscores, "
                "starting with a letter."
            ),
            severity="warning",
        )
    return None


def lint_value(key: str, value: str) -> Optional[LintIssue]:
    """Return a LintIssue if *value* looks suspicious, else None."""
    if _WHITESPACE_VALUE.search(value):
        return LintIssue(
            key=key,
            message="Value has leading or trailing whitespace.",
            severity="warning",
        )
    if value == "":
        return LintIssue(
            key=key,
            message="Value is empty.",
            severity="warning",
        )
    return None


def lint_vault(keys_and_values: dict) -> List[LintIssue]:
    """Run all lint rules against a mapping of key -> plaintext value.

    Args:
        keys_and_values: dict of variable name -> plaintext string value.

    Returns:
        List of LintIssue objects (may be empty).
    """
    issues: List[LintIssue] = []
    seen: dict = {}
    for key, value in keys_and_values.items():
        # Duplicate detection (case-insensitive)
        lower = key.lower()
        if lower in seen:
            issues.append(
                LintIssue(
                    key=key,
                    message=f"Duplicate key (case-insensitive conflict with '{seen[lower]}').",
                    severity="error",
                )
            )
        else:
            seen[lower] = key

        key_issue = lint_key(key)
        if key_issue:
            issues.append(key_issue)

        val_issue = lint_value(key, value)
        if val_issue:
            issues.append(val_issue)

    return issues
