"""Environment variable validation for envault.

Provides schema-based validation of vault entries, allowing teams to
enforce naming conventions, required keys, value formats, and types.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidateError(Exception):
    """Raised when a validation operation fails unexpectedly."""


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """Represents a single validation problem found in the vault."""

    key: str
    message: str
    severity: Severity = Severity.ERROR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "message": self.message,
            "severity": self.severity.value,
        }

    def __repr__(self) -> str:  # pragma: no cover
        icon = "✖" if self.severity == Severity.ERROR else "⚠"
        return f"{icon} [{self.severity.value.upper()}] {self.key}: {self.message}"


@dataclass
class SchemaRule:
    """A single rule in a validation schema.

    Attributes:
        key:       The exact key name this rule applies to.  Use ``None``
                   to apply a pattern rule via ``pattern`` instead.
        required:  If True, the key must be present in the vault.
        pattern:   Optional regex that the *value* must match.
        key_regex: When provided, this regex is matched against *key names*
                   rather than ``key`` equality (useful for wildcard rules).
        min_len:   Minimum character length for the value.
        max_len:   Maximum character length for the value.
        severity:  Severity to attach when this rule is violated.
    """

    key: Optional[str] = None
    required: bool = False
    pattern: Optional[str] = None
    key_regex: Optional[str] = None
    min_len: Optional[int] = None
    max_len: Optional[int] = None
    severity: Severity = Severity.ERROR


def validate_vault(
    entries: Dict[str, str],
    rules: List[SchemaRule],
) -> List[ValidationIssue]:
    """Validate *entries* against a list of *rules*.

    Args:
        entries: Mapping of key → plaintext value from the vault.
        rules:   Schema rules to enforce.

    Returns:
        A (possibly empty) list of :class:`ValidationIssue` objects.
    """
    issues: List[ValidationIssue] = []

    for rule in rules:
        # Determine which keys this rule targets
        if rule.key is not None:
            target_keys = [rule.key] if rule.key in entries else []
            if rule.required and rule.key not in entries:
                issues.append(
                    ValidationIssue(
                        key=rule.key,
                        message="Required key is missing from vault.",
                        severity=rule.severity,
                    )
                )
                continue
        elif rule.key_regex is not None:
            try:
                compiled = re.compile(rule.key_regex)
            except re.error as exc:
                raise ValidateError(f"Invalid key_regex '{rule.key_regex}': {exc}") from exc
            target_keys = [k for k in entries if compiled.fullmatch(k)]
        else:
            # Rule applies to all keys
            target_keys = list(entries.keys())

        for k in target_keys:
            value = entries[k]

            if rule.min_len is not None and len(value) < rule.min_len:
                issues.append(
                    ValidationIssue(
                        key=k,
                        message=(
                            f"Value is too short (min {rule.min_len} chars, "
                            f"got {len(value)})."
                        ),
                        severity=rule.severity,
                    )
                )

            if rule.max_len is not None and len(value) > rule.max_len:
                issues.append(
                    ValidationIssue(
                        key=k,
                        message=(
                            f"Value is too long (max {rule.max_len} chars, "
                            f"got {len(value)})."
                        ),
                        severity=rule.severity,
                    )
                )

            if rule.pattern is not None:
                try:
                    compiled_val = re.compile(rule.pattern)
                except re.error as exc:
                    raise ValidateError(
                        f"Invalid pattern '{rule.pattern}': {exc}"
                    ) from exc
                if not compiled_val.fullmatch(value):
                    issues.append(
                        ValidationIssue(
                            key=k,
                            message=(
                                f"Value does not match required pattern "
                                f"'{rule.pattern}'."
                            ),
                            severity=rule.severity,
                        )
                    )

    return issues


def has_errors(issues: List[ValidationIssue]) -> bool:
    """Return True if any issue has ERROR severity."""
    return any(i.severity == Severity.ERROR for i in issues)
