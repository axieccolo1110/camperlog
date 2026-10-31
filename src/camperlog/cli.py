"""Root of the CLI. The command groups live in ``camperlog.commands``."""

import click

from camperlog.commands.campsite import campsite
from camperlog.commands.db import db
from camperlog.commands.fuel import fuel
from camperlog.commands.serve import serve
from camperlog.commands.trip import trip
from camperlog.db import SchemaOutdatedError, require_current_schema

# `db` must work on an outdated schema (it fixes it), `serve` checks on its own.
NO_SCHEMA_CHECK = ("db", "serve")


@click.group()
@click.pass_context
def cli(ctx):
    """CamperLog – Dein Reisetagebuch für den Globetrail."""
    if ctx.invoked_subcommand in NO_SCHEMA_CHECK:
        return
    try:
        require_current_schema()
    except SchemaOutdatedError as e:
        raise click.ClickException(str(e))


cli.add_command(trip)
cli.add_command(campsite)
cli.add_command(fuel)
cli.add_command(db)
cli.add_command(serve)


if __name__ == "__main__":
    cli()
