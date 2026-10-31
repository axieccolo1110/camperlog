"""``camperlog serve``"""

import click

from camperlog.config import ConfigError, require_web_config
from camperlog.db import SchemaOutdatedError, require_current_schema


@click.command("serve")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind-Adresse")
@click.option("--port", default=8000, show_default=True, help="Port")
@click.option("--reload", is_flag=True, default=False, help="Auto-Reload (Entwicklung)")
def serve(host, port, reload):
    """Starte den Web-Server (FastAPI + Dashboard)."""
    import uvicorn

    try:
        require_web_config()
    except ConfigError as e:
        raise click.ClickException(str(e))
    try:
        require_current_schema()
    except SchemaOutdatedError as e:
        raise click.ClickException(str(e))

    uvicorn.run("camperlog.web.app:app", host=host, port=port, reload=reload)
