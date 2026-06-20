"""CLI commands for vault key rotation."""

from __future__ import annotations

import click

from envault.cli import _open_vault
from envault.rotation import apply_rotation, RotationError


@click.command("rotate")
@click.argument("vault_path", default=".envault")
def cmd_rotate(vault_path: str) -> None:
    """Re-encrypt all secrets under a new master passphrase.

    VAULT_PATH defaults to '.envault' in the current directory.
    """
    old_passphrase = click.prompt(
        "Current passphrase",
        hide_input=True,
        confirmation_prompt=False,
    )

    new_passphrase = click.prompt(
        "New passphrase",
        hide_input=True,
        confirmation_prompt=True,
    )

    if old_passphrase == new_passphrase:
        click.echo(
            click.style(
                "New passphrase must differ from the current one.", fg="yellow"
            )
        )
        raise SystemExit(1)

    vault = _open_vault(vault_path)

    try:
        apply_rotation(vault, old_passphrase, new_passphrase)
    except RotationError as exc:
        click.echo(click.style(f"Rotation failed: {exc}", fg="red"))
        raise SystemExit(1)

    secret_count = len(vault.secrets)
    click.echo(
        click.style(
            f"✓ Rotated {secret_count} secret(s) successfully.", fg="green"
        )
    )
