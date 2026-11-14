"""``camperlog fuel``"""

import click
from rich.table import Table

from camperlog.commands.common import (
    POSITIVE_FLOAT,
    confirm_delete,
    console,
    validate_date,
    validate_optional_date,
)
from camperlog.consumption import consumption_labels
from camperlog.db import session_scope
from camperlog.services.errors import NotFoundError, ValidationError
from camperlog.services.expenses import (
    add_fuel_entry,
    delete_fuel_entry,
    get_fuel_entry,
    list_fuel_entries,
    update_fuel_entry,
)


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
        f"[green]✓ Tankfüllung gespeichert (Nr. {entry.id}):[/green] "
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
    table.add_column("Nr.", style="dim", justify="right")
    table.add_column("Datum", style="cyan")
    table.add_column("Liter", style="green", justify="right")
    table.add_column("€/L", style="yellow", justify="right")
    table.add_column("Kosten", style="red", justify="right")
    table.add_column("km-Stand", style="magenta", justify="right")
    table.add_column("L/100km", style="blue", justify="right")

    for entry, consumption in zip(entries, consumption_labels(entries)):
        table.add_row(
            str(entry.id),
            entry.date.isoformat(),
            f"{entry.liters:.1f}",
            f"{entry.price_per_liter:.3f}",
            f"{entry.total_cost:.2f}€",
            str(entry.odometer),
            consumption,
        )

    console.print(table)


@fuel.command("edit")
@click.argument("entry_id", type=int)
@click.option(
    "--date",
    type=str,
    default=None,
    callback=validate_optional_date,
    help="Neues Datum (YYYY-MM-DD)",
)
@click.option("--liters", type=POSITIVE_FLOAT, default=None, help="Neue Liter")
@click.option(
    "--price-per-liter", type=POSITIVE_FLOAT, default=None, help="Neuer Preis pro Liter"
)
@click.option(
    "--odometer", type=click.IntRange(min=0), default=None, help="Neuer Kilometerstand"
)
def fuel_edit(entry_id, date, liters, price_per_liter, odometer):
    """Ändert eine Tankfüllung (nur die angegebenen Felder)."""
    if date is None and liters is None and price_per_liter is None and odometer is None:
        raise click.UsageError(
            "Nichts zu ändern: --date, --liters, --price-per-liter oder --odometer."
        )
    try:
        with session_scope() as session:
            current = get_fuel_entry(session, entry_id)
            entry = update_fuel_entry(
                session,
                entry_id,
                date or current.date,
                liters if liters is not None else current.liters,
                (
                    price_per_liter
                    if price_per_liter is not None
                    else current.price_per_liter
                ),
                odometer if odometer is not None else current.odometer,
            )
            summary = (
                f"{entry.date.isoformat()}, {entry.liters}L @ "
                f"{entry.price_per_liter}€/L = {entry.total_cost:.2f}€, "
                f"{entry.odometer} km"
            )
    except (ValidationError, NotFoundError) as e:
        raise click.ClickException(str(e))
    console.print(f"[green]✓ Tankfüllung {entry_id} geändert:[/green] {summary}")


@fuel.command("delete")
@click.argument("entry_id", type=int)
@click.option("--yes", is_flag=True, help="Ohne Rückfrage löschen")
def fuel_delete(entry_id, yes):
    """Löscht eine Tankfüllung."""
    try:
        with session_scope() as session:
            item = get_fuel_entry(session, entry_id)
            confirm_delete(
                f"Tankfüllung vom {item.date.isoformat()} "
                f"({item.liters}L, {item.odometer} km) wirklich löschen?",
                yes,
            )
            delete_fuel_entry(session, entry_id)
    except NotFoundError as e:
        raise click.ClickException(str(e))
    console.print(f"[green]✓ Tankfüllung {entry_id} gelöscht.[/green]")
