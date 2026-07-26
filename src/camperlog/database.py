import os
import sqlite3
from pathlib import Path

from typing import List

from camperlog.models import Trip, FuelEntry

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_db_path() -> Path:
    env = os.environ.get("CAMPERLOG_DB_PATH")
    if env:
        return Path(env)
    return PROJECT_ROOT / "data" / "camperlog.db"


def add_trip(origin: str, destination: str, km: int, date: str) -> Trip:
    """Speichert eine neue Reise in der Datenbank."""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO trips (origin, destination, km, date)
        VALUES (?, ?, ?, ?)
    """,
        (origin, destination, km, date),
    )

    trip_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return Trip(
        id=int(trip_id) if trip_id else 0,
        origin=origin,
        destination=destination,
        km=km,
        date=date,
    )


def get_all_trips() -> List[Trip]:
    """Lädt alle Reisen aus der Datenbank."""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()

    cursor.execute(
        """SELECT id, origin, destination, km, date FROM trips
        ORDER BY date DESC"""
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        Trip(
            id=row[0],
            origin=row[1],
            destination=row[2],
            km=row[3],
            date=row[4],
        )
        for row in rows
    ]


def init_db():
    """Initialisiert die Datenbank (beim ersten Mal)."""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            km INTEGER NOT NULL,
            date TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fuel_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            liters REAL NOT NULL,
            price_per_liter REAL NOT NULL,
            odometer INTEGER NOT NULL,
            total_cost REAL NOT NULL
        )
    """
    )

    conn.commit()
    conn.close()


def add_fuel_entry(
    date: str, liters: float, price_per_liter: float, odometer: int
) -> FuelEntry:
    """Speichert einen neuen Tankvorgang in der Datenbank."""
    total_cost = liters * price_per_liter

    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO fuel_entries
        (date, liters, price_per_liter, odometer, total_cost)
        VALUES (?, ?, ?, ?, ?)
    """,
        (date, liters, price_per_liter, odometer, total_cost),
    )

    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return FuelEntry(
        id=int(entry_id) if entry_id else 0,
        date=date,
        liters=liters,
        price_per_liter=price_per_liter,
        odometer=odometer,
        total_cost=total_cost,
    )


def get_all_fuel() -> List[FuelEntry]:
    """Lädt alle Tankvorgänge aus der Datenbank."""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()

    cursor.execute(
        """SELECT id, date, liters, price_per_liter, odometer,
        total_cost FROM fuel_entries ORDER BY date DESC"""
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        FuelEntry(
            id=row[0],
            date=row[1],
            liters=row[2],
            price_per_liter=row[3],
            odometer=row[4],
            total_cost=row[5],
        )
        for row in rows
    ]
