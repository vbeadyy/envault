"""CLI commands for template management."""

from __future__ import annotations

import click

from envault.cli import _open_vault
from envault.templates import TemplateError, TemplateManager


@click.group("template")
def cmd_template() -> None:
    """Manage .env templates."""


@cmd_template.command("create")
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)
@click.option("--templates-file", default=".envault_templates.json", show_default=True)
def cmd_template_create(name: str, keys: tuple, templates_file: str) -> None:
    """Create a template NAME with the given KEYS."""
    mgr = TemplateManager(__import__("pathlib").Path(templates_file))
    try:
        mgr.create(name, list(keys))
        click.echo(f"Template '{name}' created with keys: {', '.join(keys)}")
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_template.command("delete")
@click.argument("name")
@click.option("--templates-file", default=".envault_templates.json", show_default=True)
def cmd_template_delete(name: str, templates_file: str) -> None:
    """Delete template NAME."""
    mgr = TemplateManager(__import__("pathlib").Path(templates_file))
    try:
        mgr.delete(name)
        click.echo(f"Template '{name}' deleted.")
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc


@cmd_template.command("list")
@click.option("--templates-file", default=".envault_templates.json", show_default=True)
def cmd_template_list(templates_file: str) -> None:
    """List all available templates."""
    mgr = TemplateManager(__import__("pathlib").Path(templates_file))
    names = mgr.list_templates()
    if not names:
        click.echo("No templates defined.")
    else:
        for name in names:
            keys = list(mgr.get(name).keys())
            click.echo(f"{name}: {', '.join(keys)}")


@cmd_template.command("apply")
@click.argument("name")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--templates-file", default=".envault_templates.json", show_default=True)
def cmd_template_apply(name: str, vault_path: str, passphrase: str, templates_file: str) -> None:
    """Apply template NAME, populating keys from the current vault values."""
    from pathlib import Path

    mgr = TemplateManager(Path(templates_file))
    vault = _open_vault(vault_path, passphrase)
    try:
        template_keys = mgr.get(name)
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc

    values = {k: vault.get(k) or "" for k in template_keys}
    result = mgr.apply(name, values)
    for key, val in result.items():
        status = "(set)" if val else "(empty)"
        click.echo(f"  {key}={val!r} {status}")
