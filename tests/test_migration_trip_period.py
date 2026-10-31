"""Data migration 0002: old trips become a trip with a period and two stops."""

import datetime as dt

import pytest
from alembic import command
from sqlalchemy import inspect, text

from camperlog import db


@pytest.fixture
def old_database(tmp_path, monkeypatch):
    """A database at the baseline revision, filled with old-style data."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'old.db'}")
    command.upgrade(db.alembic_config(), "0001_baseline")
    with db.get_engine().begin() as connection:
        connection.execute(
            text(
                "INSERT INTO trips (origin, destination, km, date) VALUES "
                "('München', 'Berlin', 600, '2026-08-01'), "
                "('Berlin', 'Hamburg', 300, '2026-08-05')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO fuel_entries (date, liters, price_per_liter, odometer, "
                "total_cost) VALUES ('2026-08-02', 45.5, 1.879, 12500, 85.4945)"
            )
        )
    yield
    db.dispose_engines()


def _rows(sql):
    with db.get_engine().connect() as connection:
        return [tuple(row) for row in connection.execute(text(sql))]


def test_old_trips_become_trips_with_a_period(old_database):
    db.upgrade_to_head()

    rows = _rows(
        "SELECT start_date, end_date, distance_km FROM trips ORDER BY start_date"
    )
    assert rows == [
        ("2026-08-01", "2026-08-01", 600),
        ("2026-08-05", "2026-08-05", 300),
    ]


def test_old_trips_get_two_free_standing_stops(old_database):
    db.upgrade_to_head()

    rows = _rows(
        "SELECT t.start_date, s.position, s.date, s.place_name, s.lat, s.lon "
        "FROM stops s JOIN trips t ON t.id = s.trip_id "
        "ORDER BY t.start_date, s.position"
    )
    assert rows == [
        ("2026-08-01", 1, "2026-08-01", "München", None, None),
        ("2026-08-01", 2, "2026-08-01", "Berlin", None, None),
        ("2026-08-05", 1, "2026-08-05", "Berlin", None, None),
        ("2026-08-05", 2, "2026-08-05", "Hamburg", None, None),
    ]


def test_old_columns_are_gone_and_fuel_entries_untouched(old_database):
    db.upgrade_to_head()

    columns = {row[1] for row in _rows("PRAGMA table_info(trips)")}
    assert columns == {"id", "start_date", "end_date", "distance_km"}
    assert _rows("SELECT date, liters, odometer FROM fuel_entries") == [
        ("2026-08-02", 45.5, 12500)
    ]


def test_migrated_data_is_readable_through_the_models(old_database):
    from camperlog.services.trips import list_trips

    db.upgrade_to_head()

    with db.session_scope() as session:
        trips = list_trips(session)
        assert [(t.start_date, t.end_date, t.distance_km) for t in trips] == [
            (dt.date(2026, 8, 5), dt.date(2026, 8, 5), 300),
            (dt.date(2026, 8, 1), dt.date(2026, 8, 1), 600),
        ]
        assert [s.place_name for s in trips[1].stops] == ["München", "Berlin"]
        assert trips[1].stop_count == 2


def test_migration_works_on_an_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'empty.db'}")
    try:
        db.upgrade_to_head()
        assert _rows("SELECT * FROM trips") == []
        assert _rows("SELECT * FROM stops") == []
    finally:
        db.dispose_engines()


def test_downgrade_restores_the_old_shape(old_database):
    db.upgrade_to_head()

    command.downgrade(db.alembic_config(), "0001_baseline")

    assert _rows("SELECT origin, destination, km, date FROM trips ORDER BY date") == [
        ("München", "Berlin", 600, "2026-08-01"),
        ("Berlin", "Hamburg", 300, "2026-08-05"),
    ]
    assert "stops" not in {
        row[0] for row in _rows("SELECT name FROM sqlite_master WHERE type='table'")
    }


def test_stops_survive_the_campsite_reference_migration(tmp_path, monkeypatch):
    """0004 rebuilds the stops table (SQLite batch mode): existing stops must stay."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'm4.db'}")
    try:
        command.upgrade(db.alembic_config(), "0003_campsites")
        with db.get_engine().begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO trips (start_date, end_date) "
                    "VALUES ('2026-08-01', '2026-08-10')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO stops (trip_id, position, date, place_name, lat, lon) "
                    "VALUES (1, 1, '2026-08-02', 'Verona', 45.4, 10.9)"
                )
            )

        db.upgrade_to_head()

        assert _rows("SELECT place_name, lat, lon, campsite_id FROM stops") == [
            ("Verona", 45.4, 10.9, None)
        ]
        with db.get_engine().connect() as connection:
            keys = inspect(connection).get_foreign_keys("stops")
        assert {k["referred_table"] for k in keys} == {"trips", "campsites"}

        command.downgrade(db.alembic_config(), "0003_campsites")
        assert _rows("SELECT place_name FROM stops") == [("Verona",)]
    finally:
        db.dispose_engines()
