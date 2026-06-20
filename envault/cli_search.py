"""CLI commands for searching vault entries."""

from __future__ import annotations

import click

from envault.cli import _open_vault
from envault.search import SearchError, search_by_key, search_by_tag, search_keys_with_prefix


@click.group("search")
def cmd_search() -> None:
    """Search vault entries by key pattern, prefix, or tag."""


@cmd_search.command("keys")
@click.argument("pattern")
@click.option("--regex", is_flag=True, default=False, help="Treat PATTERN as a regular expression.")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_search_keys(pattern: str, regex: bool, vault_path: str, passphrase: str) -> None:
    """Search keys by glob PATTERN (or regex with --regex)."""
    vault = _open_vault(vault_path, passphrase)
    try:
        results = search_by_key(vault, pattern, use_regex=regex)
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    if not results:
        click.echo("No keys matched.")
        return
    for r in results:
        click.echo(r.key)


@cmd_search.command("prefix")
@click.argument("prefix")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_search_prefix(prefix: str, vault_path: str, passphrase: str) -> None:
    """List keys whose names start with PREFIX."""
    vault = _open_vault(vault_path, passphrase)
    try:
        results = search_keys_with_prefix(vault, prefix)
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    if not results:
        click.echo("No keys matched.")
        return
    for r in results:
        click.echo(r.key)


@cmd_search.command("tag")
@click.argument("tag")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def cmd_search_tag(tag: str, vault_path: str, passphrase: str) -> None:
    """List keys that carry TAG."""
    vault = _open_vault(vault_path, passphrase)
    try:
        results = search_by_tag(vault, tag)
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    if not results:
        click.echo("No keys matched.")
        return
    for r in results:
        click.echo(r.key)
