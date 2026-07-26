import os
from pathlib import Path
from typing import List

from sqlalchemy import (
    Column,
    Date,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    desc,
)
from sqlalchemy.orm import DeclarativeBase, Session

from camperlog.models import FuelEntry, Trip

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_engine():
    url = os.environ.get("DATABASE_URL")
    if url:
        return create_engine(url)
    sqlite_path = PROJECT_ROOT / "data" / "camperlog.db"
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{sqlite_path}")


class Base(DeclarativeBase):
    pass


class TripRow(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    km = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)


class FuelEntryRow(Base):
    __tablename__ = "fuel_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    liters = Column(Float, nullable=False)
    price_per_liter = Column(Float, nullable=False)
    odometer = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)


def init_db():
    """Initialisiert die Datenbank (beim ersten Mal)."""
    engine = _get_engine()
    Base.metadata.create_all(engine)
    engine.dispose()


def add_trip(origin: str, destination: str, km: int, date: str) -> Trip:
    """Speichert eine neue Reise in der Datenbank."""
    from datetime import date as date_type

    parsed_date = date_type.fromisoformat(date)
    engine = _get_engine()
    with Session(engine) as session:
        row = TripRow(
            origin=origin, destination=destination, km=km, date=parsed_date
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return Trip(
            id=row.id,
            origin=row.origin,
            destination=row.destination,
            km=row.km,
            date=str(row.date),
        )


def get_all_trips() -> List[Trip]:
    """Lädt alle Reisen aus der Datenbank."""
    engine = _get_engine()
    with Session(engine) as session:
        rows = session.query(TripRow).order_by(desc(TripRow.date)).all()
        return [
            Trip(
                id=r.id,
                origin=r.origin,
                destination=r.destination,
                km=r.km,
                date=str(r.date),
            )
            for r in rows
        ]


def add_fuel_entry(
    date: str, liters: float, price_per_liter: float, odometer: int
) -> FuelEntry:
    """Speichert einen neuen Tankvorgang in der Datenbank."""
    from datetime import date as date_type

    parsed_date = date_type.fromisoformat(date)
    total_cost = liters * price_per_liter
    engine = _get_engine()
    with Session(engine) as session:
        row = FuelEntryRow(
            date=parsed_date,
            liters=liters,
            price_per_liter=price_per_liter,
            odometer=odometer,
            total_cost=total_cost,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return FuelEntry(
            id=row.id,
            date=str(row.date),
            liters=row.liters,
            price_per_liter=row.price_per_liter,
            odometer=row.odometer,
            total_cost=row.total_cost,
        )


def get_all_fuel() -> List[FuelEntry]:
    """Lädt alle Tankvorgänge aus der Datenbank."""
    engine = _get_engine()
    with Session(engine) as session:
        rows = (
            session.query(FuelEntryRow).order_by(desc(FuelEntryRow.date)).all()
        )
        return [
            FuelEntry(
                id=r.id,
                date=str(r.date),
                liters=r.liters,
                price_per_liter=r.price_per_liter,
                odometer=r.odometer,
                total_cost=r.total_cost,
            )
            for r in rows
        ]
