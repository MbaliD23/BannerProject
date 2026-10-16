from __future__ import annotations

import json

import click

from .collector import collect_all
from .database import init_database
from .logging_config import configure_logging
from .scheduler import run_scheduler


@click.group()
def main() -> None:
    """Banner Analytics operational commands."""
    configure_logging()


@main.command("init-db")
def init_db_command() -> None:
    init_database()
    click.echo("Database schema initialized.")


@main.command("collect")
def collect_command() -> None:
    init_database()
    click.echo(json.dumps(collect_all(), indent=2))


@main.command("scheduler")
def scheduler_command() -> None:
    init_database()
    run_scheduler()


if __name__ == "__main__":
    main()

