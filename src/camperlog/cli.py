import click
from camperlog.database import (
    init_db,
    add_trip,
    get_all_trips,
    add_fuel_entry,
    get_all_fuel,
)
from rich.console import Console
from rich.table import Table
from datetime import datetime


console = Console()


@click.group()
def cli():
    """CamperLog – Dein Reisetagebuch für den Globetrail."""
    init_db()


@cli.group()
def trip():
    """Verwalte deine Reisen."""
    pass


@trip.command("add")
@click.option("--from", "origin", required=True, help="Startort")
@click.option("--to", "destination", required=True, help="Zielort")
@click.option("--km", type=int, required=True, help="Kilometer")
@click.option("--date", type=str, required=True, help="Datum (YYYY-MM-DD)")
def trip_add(origin, destination, km, date):
    """Fügt eine neue Reise hinzu."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise click.BadParameter("Datum muss im Format YYYY-MM-DD sein")

    add_trip(origin, destination, km, date)
    msg = (
        f"[green]✓ Reise gespeichert:[/green] "
        f"{origin} → {destination} ({km} km)"
    )
    console.print(msg)


@trip.command("list")
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

    for trip_item in trips:
        table.add_row(
            trip_item.date,
            trip_item.origin,
            trip_item.destination,
            str(trip_item.km),
        )

    console.print(table)


@cli.group()
def fuel():
    """Fuel management."""
    pass


@fuel.command()
@click.option("--liters", type=float, required=True, help="Getankte Liter")
@click.option(
    "--price-per-liter", type=float, required=True, help="Preis pro Liter"
)
@click.option("--odometer", type=int, required=True, help="Kilometerstand")
@click.option("--date", type=str, required=True, help="Datum (YYYY-MM-DD)")
def add(liters, price_per_liter, odometer, date):
    """Tankfüllung erfassen."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        msg = "[red]Fehler: Datum muss im Format " "YYYY-MM-DD sein[/red]"
        console.print(msg)
        return

    entry = add_fuel_entry(date, liters, price_per_liter, odometer)
    console.print(
        f"[green]✓ Tankfüllung gespeichert:[/green] "
        f"{liters}L @ {price_per_liter}€/L = {entry.total_cost:.2f}€"
    )


@fuel.command(name="list")
def fuel_list():
    """Zeigt alle Tankfüllungen mit Verbrauch."""
    entries = get_all_fuel()

    if not entries:
        console.print("[yellow]Keine Tankfüllungen erfasst.[/yellow]")
        return

    table = Table(title="⛽ Tankfüllungen")
    table.add_column("Datum", style="cyan")
    table.add_column("Liter", style="green", justify="right")
    table.add_column("€/L", style="yellow", justify="right")
    table.add_column("Kosten", style="red", justify="right")
    table.add_column("km-Stand", style="magenta", justify="right")
    table.add_column("L/100km", style="blue", justify="right")

    for i, entry in enumerate(entries):
        # Verbrauch berechnen ab zweitem Eintrag
        if i == 0:
            consumption = "-"
        else:
            km_diff = entry.odometer - entries[i - 1].odometer
            if km_diff > 0:
                consumption = f"{(entry.liters / km_diff * 100):.1f}"
            else:
                consumption = "?"

        table.add_row(
            entry.date,
            f"{entry.liters:.1f}",
            f"{entry.price_per_liter:.3f}",
            f"{entry.total_cost:.2f}€",
            str(entry.odometer),
            consumption,
        )

    console.print(table)


if __name__ == "__main__":
    cli()
