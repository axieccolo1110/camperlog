"""Expenses. For now only refuelings; categories and the rest follow in M4."""

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from camperlog.models import FuelEntry


def add_fuel_entry(
    session: Session,
    date: dt.date,
    liters: float,
    price_per_liter: float,
    odometer: int,
) -> FuelEntry:
    entry = FuelEntry(
        date=date,
        liters=liters,
        price_per_liter=price_per_liter,
        odometer=odometer,
        total_cost=liters * price_per_liter,
    )
    session.add(entry)
    session.commit()
    return entry


def list_fuel_entries(session: Session) -> list[FuelEntry]:
    """All refuelings, newest first."""
    return list(session.scalars(select(FuelEntry).order_by(FuelEntry.date.desc())))
