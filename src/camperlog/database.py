import sqlite3
from pathlib import Path
from dataclasses import dataclass

from typing import List

# Korrekt: data/ im Projekt-Root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "camperlog.db"


@dataclass
class Trip:
    """Datenklasse für eine Reise."""

    id: int
    origin: str
    destination: str
    km: int
    date: str  # Format: YYYY-MM-DD


def init_db():
    """Initialisiert die Datenbank (beim ersten Mal)."""
    # Stelle sicher, dass data/ existiert
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
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

    conn.commit()
    conn.close()


def add_trip(origin: str, destination: str, km: int, date: str) -> Trip:
    """Speichert eine neue Reise in der Datenbank."""
    conn = sqlite3.connect(DB_PATH)
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

    return Trip(id=trip_id, origin=origin, destination=destination, km=km, date=date)


def get_all_trips() -> List[Trip]:
    """Lädt alle Reisen aus der Datenbank."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, origin, destination, km, date FROM trips ORDER BY date DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        Trip(id=row[0], origin=row[1], destination=row[2], km=row[3], date=row[4])
        for row in rows
    ]
