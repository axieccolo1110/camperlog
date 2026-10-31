"""``camperlog fuel``"""

import click
from rich.table import Table

from camperlog.commands.common import POSITIVE_FLOAT, console, validate_date
from camperlog.consumption import consumption_labels
from camperlog.db import session_scope
from camperlog.services.expenses import add_fuel_entry, list_fuel_entries


@click.group()
def fuel():
    """Fuel management."""
    pass


@fuel.command()
@click.option("--liters", type=POSITIVE_FLOAT, required=True, help="Getankte Liter")
@click.option(
    "--price-per-liter", type=POSITIVE_FLOAT, required=True, help="Preis pro Liter"
)
@click.option(
    "--odometer", type=click.IntRange(min=0), required=True, help="Kilometerstand"
)
@click.option(
    "--date",
    type=str,
    required=True,
    callback=validate_date,
    help="Datum (YYYY-MM-DD)",
)
def add(liters, price_per_liter, odometer, date):
    """Tankfüllung erfassen."""
    with session_scope() as session:
        entry = add_fuel_entry(session, date, liters, price_per_liter, odometer)
    console.print(
        f"[green]✓ Tankfüllung gespeichert:[/green] "
        f"{liters}L @ {price_per_liter}€/L = {entry.total_cost:.2f}€"
    )


@fuel.command(name="list")
def fuel_list():
    """Zeigt alle Tankfüllungen mit Verbrauch."""
    with session_scope() as session:
        entries = list_fuel_entries(session)

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

    for entry, consumption in zip(entries, consumption_labels(entries)):
        table.add_row(
            entry.date.isoformat(),
            f"{entry.liters:.1f}",
            f"{entry.price_per_liter:.3f}",
            f"{entry.total_cost:.2f}€",
            str(entry.odometer),
            consumption,
        )

    console.print(table)
