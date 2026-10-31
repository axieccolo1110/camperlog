"""Trips."""

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from camperlog.models import Trip


def add_trip(
    session: Session, origin: str, destination: str, km: int, date: dt.date
) -> Trip:
    trip = Trip(origin=origin, destination=destination, km=km, date=date)
    session.add(trip)
    session.commit()
    return trip


def list_trips(session: Session) -> list[Trip]:
    """All trips, newest first."""
    return list(session.scalars(select(Trip).order_by(Trip.date.desc())))
