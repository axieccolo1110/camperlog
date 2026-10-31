"""``camperlog trip``"""

import click
from rich.table import Table

from camperlog.commands.common import console, validate_date, validate_optional_date
from camperlog.db import session_scope
from camperlog.services.errors import NotFoundError, ValidationError
from camperlog.services.trips import (
    add_stop,
    add_trip,
    delete_stop,
    delete_trip,
    get_stop,
    get_trip,
    list_trips,
    update_stop,
    update_trip,
)


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
    table.add_column("Nr.", style="dim", justify="right")
    table.add_column("Datum", style="cyan")
    table.add_column("Ort", style="magenta")
    table.add_column("Koordinaten", style="green")
    for stop_item in trip_item.stops:
        lat, lon = stop_item.effective_lat, stop_item.effective_lon
        coordinates = f"{lat}, {lon}" if lat is not None else "-"
        place_name = stop_item.effective_place_name or "-"
        if stop_item.campsite_id:
            place_name += f" ⛺ (Stellplatz {stop_item.campsite_id})"
        table.add_row(
            str(stop_item.id),
            stop_item.date.isoformat(),
            place_name,
            coordinates,
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
@click.option(
    "--campsite",
    "campsite_id",
    type=int,
    default=None,
    help="Nr. eines Stellplatzes (der Stopp übernimmt dessen Ort)",
)
def stop_add(trip_id, date, place, lat, lon, campsite_id):
    """Fügt einer Reise einen Stopp hinzu (freistehend oder an einem Stellplatz)."""
    try:
        with session_scope() as session:
            stop_item = add_stop(session, trip_id, date, place, lat, lon, campsite_id)
            name = stop_item.effective_place_name
    except (ValidationError, NotFoundError) as e:
        raise click.ClickException(str(e))
    where = f" in {name}" if name else ""
    console.print(
        f"[green]✓ Stopp gespeichert:[/green] {date.isoformat()}{where} "
        f"(Reise {trip_id})"
    )


def _confirm(question: str, yes: bool) -> None:
    """Ask for confirmation before deleting; ``--yes`` skips the question."""
    if yes or click.confirm(question):
        return
    console.print("[yellow]Abgebrochen. Nichts wurde gelöscht.[/yellow]")
    raise click.exceptions.Exit(1)


@trip.command("edit")
@click.argument("trip_id", type=int)
@click.option(
    "--start",
    type=str,
    default=None,
    callback=validate_optional_date,
    help="Neues Startdatum (YYYY-MM-DD)",
)
@click.option(
    "--end",
    type=str,
    default=None,
    callback=validate_optional_date,
    help="Neues Enddatum (YYYY-MM-DD)",
)
@click.option(
    "--km", type=click.IntRange(min=1), default=None, help="Neue Distanz in km"
)
@click.option("--clear-km", is_flag=True, help="Distanz entfernen")
def trip_edit(trip_id, start, end, km, clear_km):
    """Ändert Zeitraum oder Distanz einer Reise."""
    if start is None and end is None and km is None and not clear_km:
        raise click.UsageError(
            "Nichts zu ändern: --start, --end, --km oder --clear-km."
        )
    if km is not None and clear_km:
        raise click.UsageError("--km und --clear-km schließen sich aus.")
    try:
        with session_scope() as session:
            current = get_trip(session, trip_id)
            distance = (
                None if clear_km else (km if km is not None else current.distance_km)
            )
            update_trip(
                session,
                trip_id,
                start or current.start_date,
                end or current.end_date,
                distance,
            )
    except (ValidationError, NotFoundError) as e:
        raise click.ClickException(str(e))
    console.print(f"[green]✓ Reise {trip_id} geändert.[/green]")


@trip.command("delete")
@click.argument("trip_id", type=int)
@click.option("--yes", is_flag=True, help="Ohne Rückfrage löschen")
def trip_delete(trip_id, yes):
    """Löscht eine Reise samt ihren Stopps."""
    try:
        with session_scope() as session:
            item = get_trip(session, trip_id)
            count = item.stop_count
            stops = "1 Stopp" if count == 1 else f"{count} Stopps"
            question = (
                f"Reise {item.start_date.isoformat()} – {item.end_date.isoformat()} "
                f"mit {stops} wirklich löschen?"
            )
            _confirm(question, yes)
            delete_trip(session, trip_id)
    except NotFoundError as e:
        raise click.ClickException(str(e))
    console.print(f"[green]✓ Reise {trip_id} gelöscht.[/green]")


@stop.command("edit")
@click.argument("stop_id", type=int)
@click.option(
    "--date",
    type=str,
    default=None,
    callback=validate_optional_date,
    help="Neues Datum (YYYY-MM-DD, innerhalb der Reise)",
)
@click.option("--place", default=None, help="Neuer Ortsname (leer lassen entfernt ihn)")
@click.option("--lat", type=float, default=None, help="Neue Breite")
@click.option("--lon", type=float, default=None, help="Neue Länge")
@click.option("--clear-coordinates", is_flag=True, help="Koordinaten entfernen")
@click.option(
    "--campsite",
    "campsite_id",
    type=int,
    default=None,
    help="Stopp an diesen Stellplatz binden (ersetzt Ortsname und Koordinaten)",
)
@click.option(
    "--clear-campsite",
    is_flag=True,
    help="Stellplatz lösen (danach gilt ein eigener Ort, z. B. mit --place)",
)
def stop_edit(
    stop_id, date, place, lat, lon, clear_coordinates, campsite_id, clear_campsite
):
    """Ändert Datum, Ort, Koordinaten oder Stellplatz eines Stopps."""
    if (
        date is None
        and place is None
        and lat is None
        and lon is None
        and not clear_coordinates
        and campsite_id is None
        and not clear_campsite
    ):
        raise click.UsageError(
            "Nichts zu ändern: --date, --place, --lat/--lon, --clear-coordinates, "
            "--campsite oder --clear-campsite."
        )
    if clear_coordinates and (lat is not None or lon is not None):
        raise click.UsageError(
            "--clear-coordinates und --lat/--lon schließen sich aus."
        )
    if campsite_id is not None and clear_campsite:
        raise click.UsageError("--campsite und --clear-campsite schließen sich aus.")
    if campsite_id is not None and (
        place is not None or lat is not None or lon is not None or clear_coordinates
    ):
        raise click.UsageError(
            "--campsite übernimmt den Ort des Stellplatzes: "
            "--place, --lat, --lon und --clear-coordinates passen nicht dazu."
        )
    try:
        with session_scope() as session:
            current = get_stop(session, stop_id)
            if campsite_id is not None:
                # Tying the stop to a campsite replaces its own place.
                new_place, new_lat, new_lon = None, None, None
            else:
                new_place = current.place_name if place is None else place
                if clear_coordinates:
                    new_lat = new_lon = None
                else:
                    new_lat = lat if lat is not None else current.lat
                    new_lon = lon if lon is not None else current.lon
                if current.campsite_id is not None and not clear_campsite:
                    # Still tied to its campsite: only the date can change.
                    if place is not None or lat is not None or lon is not None:
                        raise ValidationError(
                            "Der Stopp gehört zu einem Stellplatz. "
                            "Mit --clear-campsite lösen, dann gilt ein eigener Ort."
                        )
                    campsite_id = current.campsite_id
            update_stop(
                session,
                stop_id,
                date or current.date,
                new_place,
                new_lat,
                new_lon,
                campsite_id,
            )
    except (ValidationError, NotFoundError) as e:
        raise click.ClickException(str(e))
    console.print(f"[green]✓ Stopp {stop_id} geändert.[/green]")


@stop.command("delete")
@click.argument("stop_id", type=int)
@click.option("--yes", is_flag=True, help="Ohne Rückfrage löschen")
def stop_delete(stop_id, yes):
    """Löscht einen Stopp."""
    try:
        with session_scope() as session:
            item = get_stop(session, stop_id)
            where = f" in {item.place_name}" if item.place_name else ""
            _confirm(f"Stopp vom {item.date.isoformat()}{where} wirklich löschen?", yes)
            delete_stop(session, stop_id)
    except NotFoundError as e:
        raise click.ClickException(str(e))
    console.print(f"[green]✓ Stopp {stop_id} gelöscht.[/green]")
