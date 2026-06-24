"""CLI commands for managing key expiry in envault."""

import time
from datetime import datetime

import click

from envault.cli import _open_vault, _prompt_passphrase
from envault.expiry import (
    ExpiryError,
    ExpiryRecord,
    get_expired_keys,
    get_expiring_soon_keys,
    remove_expiry,
    set_expiry,
)


@click.group("expiry")
def cmd_expiry():
    """Manage key expiry policies."""


@cmd_expiry.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("expires_at")  # ISO datetime string: YYYY-MM-DDTHH:MM:SS
@click.option("--warn-before", default=86400, show_default=True, help="Seconds before expiry to warn.")
def cmd_expiry_set(vault_path: str, key: str, expires_at: str, warn_before: int):
    """Set an expiry date on KEY in vault at VAULT_PATH."""
    try:
        ts = datetime.fromisoformat(expires_at).timestamp()
    except ValueError:
        raise click.ClickException(f"Invalid datetime format: '{expires_at}'. Use YYYY-MM-DDTHH:MM:SS.")

    passphrase = _prompt_passphrase(confirm=False)
    vault = _open_vault(vault_path, passphrase)

    records: dict = vault.metadata.get("expiry", {})
    parsed = {k: ExpiryRecord.from_dict(v) for k, v in records.items()}

    try:
        updated = set_expiry(parsed, key, ts, warn_before)
    except ExpiryError as exc:
        raise click.ClickException(str(exc))

    vault.metadata["expiry"] = {k: r.to_dict() for k, r in updated.items()}
    vault.save(passphrase)
    click.echo(f"Expiry set for '{key}' at {expires_at}.")


@cmd_expiry.command("remove")
@click.argument("vault_path")
@click.argument("key")
def cmd_expiry_remove(vault_path: str, key: str):
    """Remove expiry policy from KEY."""
    passphrase = _prompt_passphrase(confirm=False)
    vault = _open_vault(vault_path, passphrase)

    records: dict = vault.metadata.get("expiry", {})
    parsed = {k: ExpiryRecord.from_dict(v) for k, v in records.items()}

    try:
        updated = remove_expiry(parsed, key)
    except ExpiryError as exc:
        raise click.ClickException(str(exc))

    vault.metadata["expiry"] = {k: r.to_dict() for k, r in updated.items()}
    vault.save(passphrase)
    click.echo(f"Expiry removed for '{key}'.")


@cmd_expiry.command("check")
@click.argument("vault_path")
def cmd_expiry_check(vault_path: str):
    """Report expired and soon-to-expire keys."""
    passphrase = _prompt_passphrase(confirm=False)
    vault = _open_vault(vault_path, passphrase)

    records: dict = vault.metadata.get("expiry", {})
    if not records:
        click.echo("No expiry records found.")
        return

    parsed = {k: ExpiryRecord.from_dict(v) for k, v in records.items()}
    expired = get_expired_keys(parsed)
    soon = get_expiring_soon_keys(parsed)

    if expired:
        click.echo(click.style("Expired keys:", fg="red"))
        for r in expired:
            dt = datetime.fromtimestamp(r.expires_at).isoformat()
            click.echo(f"  [EXPIRED]  {r.key}  (expired at {dt})")

    if soon:
        click.echo(click.style("Expiring soon:", fg="yellow"))
        for r in soon:
            dt = datetime.fromtimestamp(r.expires_at).isoformat()
            remaining = int(r.expires_at - time.time())
            click.echo(f"  [SOON]     {r.key}  (expires at {dt}, {remaining}s remaining)")

    if not expired and not soon:
        click.echo("All keys are valid and not expiring soon.")
