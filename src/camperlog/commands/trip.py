"""``camperlog trip``"""

import click
from rich.table import Table

from camperlog.commands.common import console, validate_date
from camperlog.db import session_scope
from camperlog.services.trips import add_trip, list_trips


@click.group()
def trip():
    """Verwalte deine Reisen."""
    pass


@trip.command("add")
@click.option("--from", "origin", required=True, help="Startort")
@click.option("--to", "destination", required=True, help="Zielort")
@click.option("--km", type=click.IntRange(min=1), required=True, help="Kilometer")
@click.option(
    "--date",
    type=str,
    required=True,
    callback=validate_date,
    help="Datum (YYYY-MM-DD)",
)
def trip_add(origin, destination, km, date):
    """Fügt eine neue Reise hinzu."""
    with session_scope() as session:
        add_trip(session, origin, destination, km, date)
    msg = f"[green]✓ Reise gespeichert:[/green] {origin} → {destination} ({km} km)"
    console.print(msg)


@trip.command("list")
def trip_list():
    """Zeigt alle Reisen an."""
    with session_scope() as session:
        trips = list_trips(session)

    if not trips:
        console.print("[yellow]Keine Reisen erfasst.[/yellow]")
        return

    table = Table(title="📍 Alle Reisen")
    table.add_column("Datum", style="cyan")
    table.add_column("Von", style="magenta")
    table.add_column("Nach", style="magenta")
    table.add_column("km", style="green", justify="right")

    for trip_item in trips:
        table.add_row(
            trip_item.date.isoformat(),
            trip_item.origin,
            trip_item.destination,
            str(trip_item.km),
        )

    console.print(table)
