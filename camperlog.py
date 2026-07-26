import click

@click.group()
def cli():
    """Camperlog CLI tool for managing camper logs."""
    pass

if __name__ == '__main__':
    cli()

    def add_log_entry():
        """Add a new log entry."""
        date = click.prompt("Enter the date (YYYY-MM-DD)")
        notes = click.prompt("Enter your notes")
        click.echo(f"Log entry added for {date}: {notes}")
        pass

