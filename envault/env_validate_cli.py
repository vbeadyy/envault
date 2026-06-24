"""CLI commands for env variable validation."""

import click
from envault.cli import _open_vault, _prompt_passphrase
from envault.env_validate import validate_vault, Severity


@click.group(name="validate")
def cmd_validate():
    """Validate environment variable values against rules."""


@cmd_validate.command(name="run")
@click.argument("vault_path")
@click.option("--profile", default=None, help="Profile to validate.")
@click.option(
    "--severity",
    type=click.Choice([s.value for s in Severity], case_sensitive=False),
    default=None,
    help="Minimum severity level to report.",
)
@click.option("--fail-on-error", is_flag=True, default=False,
              help="Exit with non-zero code if errors found.")
def cmd_validate_run(vault_path, profile, severity, fail_on_error):
    """Run validation against all keys in the vault."""
    passphrase = _prompt_passphrase(confirm=False)
    vault = _open_vault(vault_path, passphrase, profile)

    min_severity = Severity(severity) if severity else None
    issues = validate_vault(vault, min_severity=min_severity)

    if not issues:
        click.secho("No validation issues found.", fg="green")
        return

    error_count = 0
    for issue in issues:
        color = "red" if issue.severity == Severity.ERROR else "yellow"
        click.secho(str(issue), fg=color)
        if issue.severity == Severity.ERROR:
            error_count += 1

    click.echo(f"\nTotal issues: {len(issues)} ({error_count} error(s))")

    if fail_on_error and error_count > 0:
        raise SystemExit(1)


@cmd_validate.command(name="key")
@click.argument("vault_path")
@click.argument("key")
@click.option("--profile", default=None, help="Profile to use.")
def cmd_validate_key(vault_path, key, profile):
    """Validate a single key in the vault."""
    passphrase = _prompt_passphrase(confirm=False)
    vault = _open_vault(vault_path, passphrase, profile)

    from envault.env_validate import validate_key
    try:
        value = vault.get(key)
    except Exception:
        click.secho(f"Key '{key}' not found in vault.", fg="red")
        raise SystemExit(1)

    issues = validate_key(key, value)
    if not issues:
        click.secho(f"Key '{key}' passed all validation checks.", fg="green")
        return

    for issue in issues:
        color = "red" if issue.severity == Severity.ERROR else "yellow"
        click.secho(str(issue), fg=color)
