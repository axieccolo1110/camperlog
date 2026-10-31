"""Trips."""

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from camperlog.models import Trip
from camperlog.services.errors import ValidationError


def add_trip(
    session: Session,
    start_date: dt.date,
    end_date: dt.date,
    distance_km: int | None = None,
) -> Trip:
    """Create a trip. The end must not lie before the start, the distance must be
    positive if given."""
    if end_date < start_date:
        raise ValidationError("Das Enddatum darf nicht vor dem Startdatum liegen.")
    if distance_km is not None and distance_km < 1:
        raise ValidationError("Die Distanz muss mindestens 1 km betragen.")
    trip = Trip(start_date=start_date, end_date=end_date, distance_km=distance_km)
    session.add(trip)
    session.commit()
    return trip


def list_trips(session: Session) -> list[Trip]:
    """All trips with their stops, newest first."""
    query = (
        select(Trip)
        .options(selectinload(Trip.stops))
        .order_by(Trip.start_date.desc(), Trip.id.desc())
    )
    return list(session.scalars(query))
