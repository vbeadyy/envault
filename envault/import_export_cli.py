"""CLI commands for importing and exporting vault snapshots."""
import click
from .sharing import export_vault, import_snapshot, SharingError
from .cli import _open_vault
from .audit import AuditLog


@click.command("export")
@click.argument("vault_path")
@click.argument("passphrase")
@click.option("--output", "-o", default=None, help="Write snapshot to file instead of stdout.")
def cmd_export(vault_path: str, passphrase: str, output: str) -> None:
    """Export an encrypted vault snapshot (base64) to stdout or a file."""
    try:
        vault = _open_vault(vault_path, passphrase)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        snapshot = export_vault(vault, passphrase)
    except SharingError as exc:
        raise click.ClickException(str(exc)) from exc

    if output:
        with open(output, "w") as fh:
            fh.write(snapshot)
        click.echo(f"Snapshot written to {output}")
    else:
        click.echo(snapshot)


@click.command("import")
@click.argument("vault_path")
@click.argument("passphrase")
@click.argument("snapshot_source")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys without prompting.",
)
def cmd_import(vault_path: str, passphrase: str, snapshot_source: str, overwrite: bool) -> None:
    """Import a base64 vault snapshot into an existing vault."""
    # snapshot_source can be a file path or a raw base64 string
    try:
        with open(snapshot_source, "r") as fh:
            snapshot = fh.read().strip()
    except (OSError, FileNotFoundError):
        snapshot = snapshot_source.strip()

    try:
        vault = _open_vault(vault_path, passphrase)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        added, skipped = import_snapshot(vault, passphrase, snapshot, overwrite=overwrite)
    except SharingError as exc:
        raise click.ClickException(str(exc)) from exc

    vault.save()
    click.echo(f"Imported {added} key(s), skipped {skipped} key(s).")
