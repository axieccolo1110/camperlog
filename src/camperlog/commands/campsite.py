"""``camperlog campsite``"""

import click
from rich.table import Table

from camperlog.commands.common import console
from camperlog.db import session_scope
from camperlog.labels import STATUS_LABELS
from camperlog.services.campsites import add_campsite, list_campsites
from camperlog.services.errors import ValidationError

# CLI users type the German words, the database stores the English values.
STATUS_BY_LABEL = {label: status for status, label in STATUS_LABELS.items()}


@click.group()
def campsite():
    """Verwalte deine Stellplätze."""
    pass


@campsite.command("add")
@click.option("--name", required=True, help="Name des Stellplatzes")
@click.option("--lat", type=float, required=True, help="Breite")
@click.option("--lon", type=float, required=True, help="Länge")
@click.option(
    "--status",
    type=click.Choice(sorted(STATUS_BY_LABEL)),
    default="vorgemerkt",
    show_default=True,
    help="Status",
)
@click.option("--notes", default=None, help="Notizen (Freitext)")
@click.option("--playground", is_flag=True, help="Spielplatz vorhanden")
@click.option("--pets", is_flag=True, help="Haustiere erlaubt")
@click.option("--url", default=None, help="Externer Link, z. B. Park4Night")
def campsite_add(name, lat, lon, status, notes, playground, pets, url):
    """Legt einen neuen Stellplatz an."""
    try:
        with session_scope() as session:
            add_campsite(
                session,
                name,
                lat,
                lon,
                STATUS_BY_LABEL[status],
                notes,
                playground,
                pets,
                url,
            )
    except ValidationError as e:
        raise click.ClickException(str(e))
    console.print(f"[green]✓ Stellplatz gespeichert:[/green] {name.strip()} ({status})")


@campsite.command("list")
def campsite_list():
    """Zeigt alle Stellplätze an."""
    with session_scope() as session:
        campsites = list_campsites(session)

    if not campsites:
        console.print("[yellow]Keine Stellplätze erfasst.[/yellow]")
        return

    table = Table(title="⛺ Alle Stellplätze")
    table.add_column("Nr.", style="dim", justify="right")
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="cyan")
    table.add_column("Koordinaten", style="green")
    table.add_column("Spielplatz", justify="center")
    table.add_column("Haustiere", justify="center")

    for item in campsites:
        table.add_row(
            str(item.id),
            item.name,
            STATUS_LABELS[item.status],
            f"{item.lat}, {item.lon}",
            "✓" if item.playground else "-",
            "✓" if item.pets_allowed else "-",
        )

    console.print(table)
