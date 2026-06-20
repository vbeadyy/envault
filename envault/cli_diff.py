"""CLI commands for diffing vault profiles or snapshots."""

import click

from .diff import diff_vaults, has_changes
from .vault import Vault, VaultError
from .profiles import ProfileManager, ProfileError


@click.command("diff")
@click.argument("profile_a")
@click.argument("profile_b")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--show-unchanged", is_flag=True, default=False, help="Include unchanged keys")
@click.pass_context
def cmd_diff(ctx: click.Context, profile_a: str, profile_b: str, passphrase: str, show_unchanged: bool) -> None:
    """Show differences between two vault profiles."""
    vault_path = ctx.obj.get("vault_path", ".envault")

    try:
        mgr = ProfileManager(vault_path)
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc

    results = {}
    for profile_name in (profile_a, profile_b):
        try:
            profile_path = mgr.profile_path(profile_name)
            vault = Vault(profile_path, passphrase)
            vault.load()
            results[profile_name] = vault.get_all_plain()
        except (VaultError, ProfileError) as exc:
            raise click.ClickException(f"[{profile_name}] {exc}") from exc

    entries = diff_vaults(results[profile_a], results[profile_b], show_unchanged=show_unchanged)

    if not has_changes(entries):
        click.echo(f"No differences between '{profile_a}' and '{profile_b}'.")
        return

    click.echo(f"Diff: {profile_a} -> {profile_b}")
    click.echo("-" * 40)
    for entry in entries:
        if entry.status == "added":
            click.secho(repr(entry), fg="green")
        elif entry.status == "removed":
            click.secho(repr(entry), fg="red")
        elif entry.status == "changed":
            click.secho(repr(entry), fg="yellow")
        else:
            click.echo(repr(entry))
