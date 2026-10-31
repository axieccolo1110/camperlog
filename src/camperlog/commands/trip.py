"""``camperlog trip``"""

import click
from rich.table import Table

from camperlog.commands.common import console, validate_date
from camperlog.db import session_scope
from camperlog.services.errors import NotFoundError, ValidationError
from camperlog.services.trips import add_stop, add_trip, get_trip, list_trips


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


@trip.command("show")
@click.argument("trip_id", type=int)
def trip_show(trip_id):
    """Zeigt eine Reise mit ihren Stopps."""
    try:
        with session_scope() as session:
            trip_item = get_trip(session, trip_id)
    except NotFoundError as e:
        raise click.ClickException(str(e))

    distance = f", {trip_item.distance_km} km" if trip_item.distance_km else ""
    console.print(
        f"[bold]Reise {trip_item.id}:[/bold] {trip_item.start_date.isoformat()} – "
        f"{trip_item.end_date.isoformat()}{distance}"
    )
    if not trip_item.stops:
        console.print("[yellow]Keine Stopps erfasst.[/yellow]")
        return

    table = Table(title="Stopps")
    table.add_column("Datum", style="cyan")
    table.add_column("Ort", style="magenta")
    table.add_column("Koordinaten", style="green")
    for stop_item in trip_item.stops:
        coordinates = (
            f"{stop_item.lat}, {stop_item.lon}" if stop_item.lat is not None else "-"
        )
        table.add_row(
            stop_item.date.isoformat(), stop_item.place_name or "-", coordinates
        )
    console.print(table)


@trip.group("stop")
def stop():
    """Verwalte die Stopps einer Reise."""
    pass


@stop.command("add")
@click.argument("trip_id", type=int)
@click.option(
    "--date",
    type=str,
    required=True,
    callback=validate_date,
    help="Datum des Stopps (YYYY-MM-DD, innerhalb der Reise)",
)
@click.option("--place", default=None, help="Ortsname (optional)")
@click.option("--lat", type=float, default=None, help="Breite (optional)")
@click.option("--lon", type=float, default=None, help="Länge (optional)")
def stop_add(trip_id, date, place, lat, lon):
    """Fügt einer Reise einen freistehenden Stopp hinzu."""
    try:
        with session_scope() as session:
            add_stop(session, trip_id, date, place, lat, lon)
    except (ValidationError, NotFoundError) as e:
        raise click.ClickException(str(e))
    where = f" in {place}" if place else ""
    console.print(
        f"[green]✓ Stopp gespeichert:[/green] {date.isoformat()}{where} "
        f"(Reise {trip_id})"
    )
