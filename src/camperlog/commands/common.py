"""Helpers shared by the command modules."""

import datetime as dt

import click
from rich.console import Console

console = Console()

POSITIVE_FLOAT = click.FloatRange(min=0, min_open=True)


def validate_date(ctx, param, value) -> dt.date:
    """Click callback: parse a date in the format YYYY-MM-DD."""
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise click.BadParameter("Datum muss im Format YYYY-MM-DD sein")
