"""Polecenia ``flask`` projektu (obok ``flask db`` z Flask-Migrate)."""

from __future__ import annotations

import click
from flask import Flask, current_app
from flask.cli import with_appcontext

from backend.core.constants import PASSWORD_MIN_LENGTH
from backend.services.demo_seed_service import DemoSeedService


@click.command("seed-demo")
@click.option("--reset", is_flag=True, help="Usuń istniejące dane demo i utwórz je od nowa.")
@with_appcontext
def seed_demo_command(reset: bool) -> None:
    """Tworzy konta demo, mieszkanie i przykładowe zadania (nie w produkcji)."""
    if current_app.config["ENV_NAME"] == "production":
        raise click.ClickException("Dane demo nie są dostępne w środowisku produkcyjnym.")
    password = current_app.config["DEMO_PASSWORD"]
    if len(password) < PASSWORD_MIN_LENGTH:
        raise click.ClickException(
            f"Ustaw DEMO_PASSWORD (co najmniej {PASSWORD_MIN_LENGTH} znaków) w pliku .env."
        )

    result = DemoSeedService().seed(password, reset=reset)
    if not result.created:
        click.echo("Dane demo już istnieją. Użyj --reset, aby utworzyć je od nowa.")
        return
    click.echo("Utworzono dane demo. Konta (hasło: wartość DEMO_PASSWORD z .env):")
    for email in result.emails:
        click.echo(f"  {email}")


def register_cli(app: Flask) -> None:
    app.cli.add_command(seed_demo_command)
