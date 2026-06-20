"""CLI commands for managing secret tags."""

from __future__ import annotations

import click

from envault.cli import _open_vault
from envault.tags import (
    TagError,
    add_tag,
    all_tags,
    filter_by_tag,
    list_tags,
    remove_tag,
)


@click.group("tag")
def cmd_tag() -> None:
    """Manage tags for secrets."""


@cmd_tag.command("add")
@click.argument("key")
@click.argument("tag")
@click.option("--vault", default=".envault", show_default=True, help="Path to vault file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
def cmd_tag_add(key: str, tag: str, vault: str, passphrase: str) -> None:
    """Add TAG to the secret KEY."""
    try:
        v = _open_vault(vault, passphrase)
        v.tags = add_tag(v.tags, key, tag)
        v.save(passphrase)
        click.echo(f"Tag '{tag}' added to '{key}'.")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_tag.command("remove")
@click.argument("key")
@click.argument("tag")
@click.option("--vault", default=".envault", show_default=True, help="Path to vault file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
def cmd_tag_remove(key: str, tag: str, vault: str, passphrase: str) -> None:
    """Remove TAG from the secret KEY."""
    try:
        v = _open_vault(vault, passphrase)
        v.tags = remove_tag(v.tags, key, tag)
        v.save(passphrase)
        click.echo(f"Tag '{tag}' removed from '{key}'.")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_tag.command("list")
@click.argument("key")
@click.option("--vault", default=".envault", show_default=True, help="Path to vault file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
def cmd_tag_list(key: str, vault: str, passphrase: str) -> None:
    """List all tags for the secret KEY."""
    v = _open_vault(vault, passphrase)
    tags = list_tags(v.tags, key)
    if tags:
        click.echo(", ".join(tags))
    else:
        click.echo(f"No tags for '{key}'.")


@cmd_tag.command("filter")
@click.argument("tag")
@click.option("--vault", default=".envault", show_default=True, help="Path to vault file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
def cmd_tag_filter(tag: str, vault: str, passphrase: str) -> None:
    """List all secret keys that have TAG."""
    v = _open_vault(vault, passphrase)
    keys = filter_by_tag(v.tags, tag)
    if keys:
        for k in keys:
            click.echo(k)
    else:
        click.echo(f"No secrets tagged with '{tag}'.")


@cmd_tag.command("all")
@click.option("--vault", default=".envault", show_default=True, help="Path to vault file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
def cmd_tag_all(vault: str, passphrase: str) -> None:
    """List all unique tags across all secrets."""
    v = _open_vault(vault, passphrase)
    tags = all_tags(v.tags)
    if tags:
        for t in tags:
            click.echo(t)
    else:
        click.echo("No tags defined.")
