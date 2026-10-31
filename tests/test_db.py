import datetime as dt
import os
import subprocess
import sys

import pytest
from alembic import command
from click.testing import CliRunner
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from camperlog import db
from camperlog.cli import cli
from camperlog.db import session_scope
from camperlog.models import Base
from camperlog.services.trips import add_trip, list_trips


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """An empty database file that was never migrated."""
    path = tmp_path / "fresh.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    yield path
    db.dispose_engines()


def test_engine_is_reused_for_the_same_url(fresh_db):
    assert db.get_engine() is db.get_engine()


def test_engine_follows_database_url(fresh_db, tmp_path, monkeypatch):
    first = db.get_engine()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'other.db'}")
    assert db.get_engine() is not first


def test_default_database_is_local_sqlite_file(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(db, "PROJECT_ROOT", tmp_path)
    assert db.get_database_url() == f"sqlite:///{tmp_path / 'data' / 'camperlog.db'}"
    assert (tmp_path / "data").is_dir()


def test_upgrade_creates_the_current_schema(fresh_db):
    db.upgrade_to_head()

    inspector = inspect(db.get_engine())
    assert set(inspector.get_table_names()) >= {"trips", "stops", "fuel_entries"}
    trip_columns = {c["name"] for c in inspector.get_columns("trips")}
    assert trip_columns == {"id", "start_date", "end_date", "distance_km"}
    fuel_columns = {c["name"] for c in inspector.get_columns("fuel_entries")}
    assert fuel_columns == {
        "id",
        "date",
        "liters",
        "price_per_liter",
        "odometer",
        "total_cost",
    }
    assert db.current_revision() == db.head_revision()


def test_upgrade_twice_is_harmless(fresh_db):
    db.upgrade_to_head()
    with session_scope() as session:
        add_trip(session, dt.date(2026, 8, 1), dt.date(2026, 8, 22), 600)

    db.upgrade_to_head()

    with session_scope() as session:
        assert len(list_trips(session)) == 1


def test_unmigrated_database_is_outdated(fresh_db):
    with pytest.raises(db.SchemaOutdatedError, match="camperlog db upgrade"):
        db.require_current_schema()


def test_migrated_database_is_current(fresh_db):
    db.upgrade_to_head()
    db.require_current_schema()


LEGACY_SCHEMA = """
CREATE TABLE trips (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    origin VARCHAR NOT NULL,
    destination VARCHAR NOT NULL,
    km INTEGER NOT NULL,
    date DATE NOT NULL
)
"""


def test_existing_production_database_can_be_stamped_without_data_loss(fresh_db):
    """A database made by the former create_all is stamped, then migrated."""
    with db.get_engine().begin() as connection:
        connection.execute(text(LEGACY_SCHEMA))
        connection.execute(
            text(
                "CREATE TABLE fuel_entries (id INTEGER NOT NULL PRIMARY KEY "
                "AUTOINCREMENT, date DATE NOT NULL, liters FLOAT NOT NULL, "
                "price_per_liter FLOAT NOT NULL, odometer INTEGER NOT NULL, "
                "total_cost FLOAT NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO trips (origin, destination, km, date) "
                "VALUES ('München', 'Berlin', 600, '2026-08-01')"
            )
        )
    with pytest.raises(db.SchemaOutdatedError):
        db.require_current_schema()

    command.stamp(db.alembic_config(), "0001_baseline")
    db.upgrade_to_head()

    db.require_current_schema()
    with session_scope() as session:
        [trip] = list_trips(session)
        assert (trip.start_date, trip.end_date, trip.distance_km) == (
            dt.date(2026, 8, 1),
            dt.date(2026, 8, 1),
            600,
        )
        assert [s.place_name for s in trip.stops] == ["München", "Berlin"]


def test_sqlite_foreign_keys_are_on_after_a_migration(fresh_db):
    """Migrations switch them off temporarily and must switch them back on."""
    db.upgrade_to_head()

    with db.get_engine().connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_orm_tables_match_the_migrated_schema(fresh_db):
    """The baseline revision and the ORM classes describe the same tables."""
    db.upgrade_to_head()
    with db.get_engine().connect() as connection:
        inspector = inspect(connection)
        for table in Base.metadata.sorted_tables:
            migrated = {c["name"] for c in inspector.get_columns(table.name)}
            assert migrated == {c.name for c in table.columns}, table.name


def test_alembic_command_line_works_like_in_the_deployment(tmp_path):
    """``alembic upgrade head`` is what the Railway start and make serve run."""
    path = tmp_path / "cli.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}

    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=db.PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stderr
    assert path.exists()
    engine_tables = subprocess.run(
        [
            sys.executable,
            "-c",
            "from camperlog.db import get_engine; from sqlalchemy import inspect; "
            "print(sorted(inspect(get_engine()).get_table_names()))",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    assert "trips" in engine_tables and "fuel_entries" in engine_tables


def test_cli_aborts_on_outdated_schema_with_hint(fresh_db):
    result = CliRunner().invoke(cli, ["trip", "list"])

    assert result.exit_code != 0
    assert "camperlog db upgrade" in result.output


def test_cli_db_upgrade_fixes_the_schema(fresh_db):
    runner = CliRunner()

    upgrade = runner.invoke(cli, ["db", "upgrade"])
    listing = runner.invoke(cli, ["trip", "list"])

    assert upgrade.exit_code == 0
    assert "neuesten Stand" in upgrade.output
    assert listing.exit_code == 0


def test_serve_aborts_on_outdated_schema(fresh_db, monkeypatch):
    import uvicorn

    monkeypatch.setenv("CAMPERLOG_PASSWORD", "pw")
    monkeypatch.setenv("CAMPERLOG_SECRET_KEY", "key")
    started = []
    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: started.append(1))

    result = CliRunner().invoke(cli, ["serve"])

    assert result.exit_code != 0
    assert "camperlog db upgrade" in result.output
    assert started == []


def test_web_app_refuses_to_start_on_outdated_schema(fresh_db, monkeypatch):
    from camperlog.web.app import create_app

    monkeypatch.setenv("CAMPERLOG_PASSWORD", "pw")
    monkeypatch.setenv("CAMPERLOG_SECRET_KEY", "key")

    with pytest.raises(db.SchemaOutdatedError):
        with TestClient(create_app()):
            pass
