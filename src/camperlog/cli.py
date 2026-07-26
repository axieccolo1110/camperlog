import click
from camperlog.database import init_db, add_trip, get_all_trips
from rich.console import Console
from rich.table import Table
from datetime import datetime

console = Console()


@click.group()
def cli():
    """CamperLog – Dein Reisetagebuch für den Globetrail."""
    init_db()


@cli.command()
@click.option("--from", "origin", required=True, help="Startort")
@click.option("--to", "destination", required=True, help="Zielort")
@click.option("--km", type=int, required=True, help="Kilometer")
@click.option("--date", type=str, required=True, help="Datum (YYYY-MM-DD)")
def trip_add(origin, destination, km, date):
    """Fügt eine neue Reise hinzu."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Fehler: Datum muss im Format YYYY-MM-DD sein[/red]")
        return
    
    trip = add_trip(origin, destination, km, date)
    console.print(f"[green]✓ Reise gespeichert:[/green] {origin} → {destination} ({km} km)")


@cli.command()
def trip_list():
    """Zeigt alle Reisen an."""
    trips = get_all_trips()
    
    if not trips:
        console.print("[yellow]Keine Reisen erfasst.[/yellow]")
        return
    
    table = Table(title="📍 Alle Reisen")
    table.add_column("Datum", style="cyan")
    table.add_column("Von", style="magenta")
    table.add_column("Nach", style="magenta")
    table.add_column("km", style="green", justify="right")
    
    for trip in trips:
        table.add_row(trip.date, trip.origin, trip.destination, str(trip.km))
    
    console.print(table)


if __name__ == "__main__":
    cli()
