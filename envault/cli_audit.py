"""CLI command for displaying the vault audit log."""

from __future__ import annotations

from pathlib import Path

import click

from envault.audit import AuditLog, audit_log_path


DEFAULT_VAULT_PATH = Path(".envault")


def _format_entry(entry) -> str:
    action = entry.action.upper().ljust(8)
    key_part = f"  key={entry.key}" if entry.key else ""
    return f"[{entry.timestamp}]  {action}  actor={entry.actor}{key_part}"


@click.command("log")
@click.option(
    "--vault",
    "vault_path",
    default=str(DEFAULT_VAULT_PATH),
    show_default=True,
    help="Path to the vault file.",
    type=click.Path(),
)
@click.option(
    "-n",
    "count",
    default=20,
    show_default=True,
    help="Number of recent entries to display.",
)
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    default=False,
    help="Show all entries instead of the most recent.",
)
def cmd_log(vault_path: str, count: int, show_all: bool) -> None:
    """Display the audit log for the vault."""
    path = Path(vault_path)
    log_path = audit_log_path(path)

    if not log_path.exists():
        click.echo("No audit log found. Have you initialised a vault here?")
        raise SystemExit(1)

    log = AuditLog(log_path)
    entries = log.entries() if show_all else log.last(count)

    if not entries:
        click.echo("Audit log is empty.")
        return

    click.echo(f"Showing {len(entries)} audit log entr{'y' if len(entries) == 1 else 'ies'}:\n")
    for entry in entries:
        click.echo(_format_entry(entry))
