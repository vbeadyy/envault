"""Command-line interface for envault vault operations."""

import getpass
import sys
from pathlib import Path

import click

from envault.vault import Vault, VaultError, DEFAULT_VAULT_FILENAME


def _open_vault(vault_file: str, passphrase: str, *, require_existing: bool = True) -> Vault:
    path = Path(vault_file)
    v = Vault(path, passphrase)
    if require_existing:
        try:
            v.load()
        except VaultError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)
    return v


@click.group()
def cli() -> None:
    """envault — encrypted .env manager."""


@cli.command("init")
@click.option("--file", "vault_file", default=DEFAULT_VAULT_FILENAME, show_default=True)
def cmd_init(vault_file: str) -> None:
    """Initialise a new empty vault."""
    path = Path(vault_file)
    if path.exists():
        click.echo(f"Vault already exists at {path}", err=True)
        sys.exit(1)
    passphrase = getpass.getpass("New passphrase: ")
    confirm = getpass.getpass("Confirm passphrase: ")
    if passphrase != confirm:
        click.echo("Passphrases do not match.", err=True)
        sys.exit(1)
    v = Vault(path, passphrase)
    v.save()
    click.echo(f"Vault initialised at {path}")


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--file", "vault_file", default=DEFAULT_VAULT_FILENAME, show_default=True)
def cmd_set(key: str, value: str, vault_file: str) -> None:
    """Set KEY to VALUE in the vault."""
    passphrase = getpass.getpass("Passphrase: ")
    v = _open_vault(vault_file, passphrase)
    v.set(key, value)
    v.save()
    click.echo(f"Set {key}")


@cli.command("get")
@click.argument("key")
@click.option("--file", "vault_file", default=DEFAULT_VAULT_FILENAME, show_default=True)
def cmd_get(key: str, vault_file: str) -> None:
    """Print the value of KEY from the vault."""
    passphrase = getpass.getpass("Passphrase: ")
    v = _open_vault(vault_file, passphrase)
    value = v.get(key)
    if value is None:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    click.echo(value)


@cli.command("delete")
@click.argument("key")
@click.option("--file", "vault_file", default=DEFAULT_VAULT_FILENAME, show_default=True)
def cmd_delete(key: str, vault_file: str) -> None:
    """Delete KEY from the vault."""
    passphrase = getpass.getpass("Passphrase: ")
    v = _open_vault(vault_file, passphrase)
    if not v.delete(key):
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    v.save()
    click.echo(f"Deleted {key}")


@cli.command("export")
@click.option("--file", "vault_file", default=DEFAULT_VAULT_FILENAME, show_default=True)
def cmd_export(vault_file: str) -> None:
    """Export vault contents as a .env-formatted string."""
    passphrase = getpass.getpass("Passphrase: ")
    v = _open_vault(vault_file, passphrase)
    click.echo(v.export_env())


if __name__ == "__main__":
    cli()
