"""CLI commands for renaming vault keys."""

from __future__ import annotations

import click

from envault.cli import _open_vault, _prompt_passphrase
from envault.env_rename import RenameError, rename_key


@click.group("rename")
def cmd_rename() -> None:
    """Rename keys inside a vault."""


@cmd_rename.command("key")
@click.argument("vault_path")
@click.argument("old_key")
@click.argument("new_key")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite new_key if it already exists.",
)
@click.option("--profile", default=None, help="Profile name to load passphrase from.")
def cmd_rename_key(
    vault_path: str,
    old_key: str,
    new_key: str,
    overwrite: bool,
    profile: str | None,
) -> None:
    """Rename OLD_KEY to NEW_KEY in VAULT_PATH."""
    passphrase = _prompt_passphrase(profile)
    try:
        vault = _open_vault(vault_path, passphrase)
        rename_key(vault, old_key, new_key, overwrite=overwrite)
        vault.save(passphrase)
        click.echo(f"Renamed '{old_key}' → '{new_key}' in {vault_path}")
    except RenameError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_rename.command("bulk")
@click.argument("vault_path")
@click.argument("pairs", nargs=-1, required=True, metavar="OLD_KEY:NEW_KEY...")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite destination keys if they already exist.",
)
@click.option("--profile", default=None, help="Profile name to load passphrase from.")
def cmd_rename_bulk(
    vault_path: str,
    pairs: tuple[str, ...],
    overwrite: bool,
    profile: str | None,
) -> None:
    """Bulk-rename keys in VAULT_PATH using PAIRS formatted as OLD_KEY:NEW_KEY."""
    mapping: dict[str, str] = {}
    for pair in pairs:
        if ":" not in pair:
            raise click.BadParameter(
                f"Each pair must be formatted as OLD_KEY:NEW_KEY, got: {pair!r}"
            )
        old, _, new = pair.partition(":")
        mapping[old] = new

    passphrase = _prompt_passphrase(profile)
    try:
        vault = _open_vault(vault_path, passphrase)
        from envault.env_rename import rename_keys

        renamed = rename_keys(vault, mapping, overwrite=overwrite)
        vault.save(passphrase)
        for old_key in renamed:
            click.echo(f"  Renamed '{old_key}' → '{mapping[old_key]}'")
        click.echo(f"Done — {len(renamed)} key(s) renamed.")
    except RenameError as exc:
        raise click.ClickException(str(exc)) from exc
