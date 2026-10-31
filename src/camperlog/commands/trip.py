"""``camperlog trip``"""

import click
from rich.table import Table

from camperlog.commands.common import console, validate_date
from camperlog.db import session_scope
from camperlog.services.errors import ValidationError
from camperlog.services.trips import add_trip, list_trips


@click.group()
def trip():
    """Verwalte deine Reisen."""
    pass


@trip.command("add")
@click.option(
    "--start",
    type=str,
    required=True,
    callback=validate_date,
    help="Startdatum (YYYY-MM-DD)",
)
@click.option(
    "--end",
    type=str,
    required=True,
    callback=validate_date,
    help="Enddatum (YYYY-MM-DD)",
)
@click.option(
    "--km",
    type=click.IntRange(min=1),
    default=None,
    help="Distanz in Kilometern (optional)",
)
def trip_add(start, end, km):
    """Legt eine neue Reise mit Zeitraum an."""
    try:
        with session_scope() as session:
            add_trip(session, start, end, km)
    except ValidationError as e:
        raise click.ClickException(str(e))
    distance = f" ({km} km)" if km else ""
    console.print(
        f"[green]✓ Reise gespeichert:[/green] {start.isoformat()} – "
        f"{end.isoformat()}{distance}"
    )


@trip.command("list")
def trip_list():
    """Zeigt alle Reisen an."""
    with session_scope() as session:
        trips = list_trips(session)

    if not trips:
        console.print("[yellow]Keine Reisen erfasst.[/yellow]")
        return

    table = Table(title="📍 Alle Reisen")
    table.add_column("Von", style="cyan")
    table.add_column("Bis", style="cyan")
    table.add_column("Stopps", style="magenta", justify="right")
    table.add_column("km", style="green", justify="right")

    for trip_item in trips:
        table.add_row(
            trip_item.start_date.isoformat(),
            trip_item.end_date.isoformat(),
            str(trip_item.stop_count),
            str(trip_item.distance_km) if trip_item.distance_km else "-",
        )

    console.print(table)
