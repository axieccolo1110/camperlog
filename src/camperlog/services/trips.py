"""Trips and their stops."""

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from camperlog.models import Stop, Trip
from camperlog.services.errors import NotFoundError, ValidationError


def _check_trip_fields(
    start_date: dt.date, end_date: dt.date, distance_km: int | None
) -> None:
    """The end must not lie before the start, the distance must be positive."""
    if end_date < start_date:
        raise ValidationError("Das Enddatum darf nicht vor dem Startdatum liegen.")
    if distance_km is not None and distance_km < 1:
        raise ValidationError("Die Distanz muss mindestens 1 km betragen.")


def _check_stop_fields(
    trip: Trip, date: dt.date, lat: float | None, lon: float | None
) -> None:
    """The date lies within the trip (ends included), coordinates come as a pair."""
    if not trip.start_date <= date <= trip.end_date:
        raise ValidationError(
            f"Das Datum eines Stopps muss im Zeitraum der Reise liegen "
            f"({trip.start_date.isoformat()} bis {trip.end_date.isoformat()})."
        )
    if (lat is None) != (lon is None):
        raise ValidationError("Koordinaten brauchen Breite und Länge.")
    if lat is not None and not -90 <= lat <= 90:
        raise ValidationError("Die Breite muss zwischen -90 und 90 liegen.")
    if lon is not None and not -180 <= lon <= 180:
        raise ValidationError("Die Länge muss zwischen -180 und 180 liegen.")


def _clean_place(place_name: str | None) -> str | None:
    return (place_name or "").strip() or None


def add_trip(
    session: Session,
    start_date: dt.date,
    end_date: dt.date,
    distance_km: int | None = None,
) -> Trip:
    """Create a trip."""
    _check_trip_fields(start_date, end_date, distance_km)
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
        .execution_options(populate_existing=True)
    )
    return list(session.scalars(query))


def get_trip(session: Session, trip_id: int) -> Trip:
    """A trip with its stops. Raises NotFoundError if it does not exist."""
    # populate_existing: a trip already loaded in this session must not keep a
    # stale stop list (stops are inserted by trip_id, not through the collection).
    query = (
        select(Trip)
        .options(selectinload(Trip.stops))
        .where(Trip.id == trip_id)
        .execution_options(populate_existing=True)
    )
    trip = session.scalars(query).one_or_none()
    if trip is None:
        raise NotFoundError(f"Reise {trip_id} gibt es nicht.")
    return trip


def update_trip(
    session: Session,
    trip_id: int,
    start_date: dt.date,
    end_date: dt.date,
    distance_km: int | None,
) -> Trip:
    """Replace period and distance of a trip (``None`` removes the distance).

    The new period must include all existing stops.
    """
    trip = get_trip(session, trip_id)
    _check_trip_fields(start_date, end_date, distance_km)
    outside = [s.date for s in trip.stops if not start_date <= s.date <= end_date]
    if outside:
        days = ", ".join(sorted({d.isoformat() for d in outside}))
        raise ValidationError(
            f"Der neue Zeitraum muss alle Stopps einschließen. "
            f"Stopps außerhalb: {days}."
        )
    trip.start_date = start_date
    trip.end_date = end_date
    trip.distance_km = distance_km
    session.commit()
    return trip


def delete_trip(session: Session, trip_id: int) -> None:
    """Delete a trip together with its stops."""
    session.delete(get_trip(session, trip_id))
    session.commit()


def add_stop(
    session: Session,
    trip_id: int,
    date: dt.date,
    place_name: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> Stop:
    """Add a free-standing stop to a trip.

    The date must lie within the period of the trip (both ends included).
    Coordinates are given as a pair or not at all. A new stop goes to the end of
    its day: stops sort by date, and ``position`` (order of entry) decides only for
    the same date.
    """
    trip = get_trip(session, trip_id)
    _check_stop_fields(trip, date, lat, lon)
    last_position = session.scalar(
        select(func.max(Stop.position)).where(Stop.trip_id == trip_id)
    )
    stop = Stop(
        trip_id=trip_id,
        position=(last_position or 0) + 1,
        date=date,
        place_name=_clean_place(place_name),
        lat=lat,
        lon=lon,
    )
    session.add(stop)
    session.commit()
    return stop


def get_stop(session: Session, stop_id: int) -> Stop:
    """A stop. Raises NotFoundError if it does not exist."""
    stop = session.scalars(
        select(Stop).where(Stop.id == stop_id).execution_options(populate_existing=True)
    ).one_or_none()
    if stop is None:
        raise NotFoundError(f"Stopp {stop_id} gibt es nicht.")
    return stop


def update_stop(
    session: Session,
    stop_id: int,
    date: dt.date,
    place_name: str | None,
    lat: float | None,
    lon: float | None,
) -> Stop:
    """Replace date, place name and coordinates of a stop.

    The date still has to lie within the trip. The position (order of entry) stays.
    """
    stop = get_stop(session, stop_id)
    trip = get_trip(session, stop.trip_id)
    _check_stop_fields(trip, date, lat, lon)
    stop.date = date
    stop.place_name = _clean_place(place_name)
    stop.lat = lat
    stop.lon = lon
    session.commit()
    return stop


def delete_stop(session: Session, stop_id: int) -> None:
    session.delete(get_stop(session, stop_id))
    session.commit()
