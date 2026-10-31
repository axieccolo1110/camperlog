"""``camperlog db``"""

import click

from camperlog.commands.common import console
from camperlog.db import upgrade_to_head


@click.group()
def db():
    """Datenbank verwalten."""
    pass


@db.command("upgrade")
def db_upgrade():
    """Wendet alle ausstehenden Datenbank-Migrationen an."""
    upgrade_to_head()
    console.print("[green]✓ Datenbank ist auf dem neuesten Stand.[/green]")
