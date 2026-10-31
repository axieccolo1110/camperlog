"""Database infrastructure: engine, schema version check and migrations.

One engine exists per process and database URL. Schema changes are rolled out
with Alembic (see ``migrations/``); nothing creates tables implicitly.
"""

import os
import threading
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"

_engines: dict[str, Engine] = {}
_lock = threading.Lock()


class SchemaOutdatedError(RuntimeError):
    """The database schema does not match the code (migrations are pending)."""


def get_database_url() -> str:
    """``DATABASE_URL`` or, without it, the local SQLite file ``data/camperlog.db``."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    sqlite_path = PROJECT_ROOT / "data" / "camperlog.db"
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def get_engine() -> Engine:
    """Return the engine for the current database URL, creating it lazily.

    The cache is keyed by URL, so a process uses exactly one engine per database.
    (Tests point ``DATABASE_URL`` at a fresh file per test and thus get a fresh
    engine.)
    """
    url = get_database_url()
    with _lock:
        engine = _engines.get(url)
        if engine is None:
            engine = create_engine(url)
            _engines[url] = engine
        return engine


def dispose_engines() -> None:
    """Close all pooled connections and forget the engines (used by tests)."""
    with _lock:
        for engine in _engines.values():
            engine.dispose()
        _engines.clear()


def alembic_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    return config


def head_revision() -> str | None:
    """The newest revision known to the code."""
    return ScriptDirectory.from_config(alembic_config()).get_current_head()


def current_revision() -> str | None:
    """The revision the database is at, ``None`` if it was never migrated."""
    with get_engine().connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def upgrade_to_head() -> None:
    """Run all pending migrations (same as ``alembic upgrade head``)."""
    command.upgrade(alembic_config(), "head")


def require_current_schema() -> None:
    """Raise SchemaOutdatedError unless the database is at the newest revision."""
    current, head = current_revision(), head_revision()
    if current != head:
        state = current or "nicht initialisiert"
        raise SchemaOutdatedError(
            f"Das Datenbankschema ist veraltet (Stand: {state}, benötigt: {head}). "
            "Bitte `camperlog db upgrade` ausführen."
        )
