import datetime as dt

import pytest

from camperlog.db import session_scope
from camperlog.models import Stop
from camperlog.services.errors import ValidationError
from camperlog.services.trips import add_trip, list_trips

START = dt.date(2026, 8, 1)
END = dt.date(2026, 8, 22)


def test_add_trip(session):
    """A trip is stored with its period and distance."""
    trip = add_trip(session, START, END, 600)

    assert trip.id is not None
    assert trip.start_date == START
    assert trip.end_date == END
    assert trip.distance_km == 600
    assert trip.stop_count == 0


def test_distance_is_optional(session):
    assert add_trip(session, START, END).distance_km is None


def test_one_day_trip_is_allowed(session):
    assert add_trip(session, START, START).end_date == START


def test_end_before_start_is_rejected(session):
    with pytest.raises(ValidationError, match="Enddatum"):
        add_trip(session, END, START)
    assert list_trips(session) == []


@pytest.mark.parametrize("km", [0, -5])
def test_non_positive_distance_is_rejected(session, km):
    with pytest.raises(ValidationError, match="Distanz"):
        add_trip(session, START, END, km)
    assert list_trips(session) == []


def test_list_trips_newest_first(session):
    """All trips are returned, the trip that started last first."""
    add_trip(session, dt.date(2026, 7, 1), dt.date(2026, 7, 10))
    add_trip(session, dt.date(2026, 8, 1), dt.date(2026, 8, 22))

    trips = list_trips(session)

    assert [t.start_date for t in trips] == [dt.date(2026, 8, 1), dt.date(2026, 7, 1)]


def test_list_trips_empty(session):
    """Empty list when no trips exist."""
    assert list_trips(session) == []


def test_trips_survive_a_new_session(session):
    """add_trip commits: another session sees the data."""
    add_trip(session, START, END, 600)

    with session_scope() as other:
        assert len(list_trips(other)) == 1


def test_stops_are_sorted_by_date_then_position(session):
    trip = add_trip(session, START, END)
    session.add_all(
        [
            Stop(trip_id=trip.id, position=3, date=dt.date(2026, 8, 5)),
            Stop(trip_id=trip.id, position=2, date=dt.date(2026, 8, 3)),
            Stop(trip_id=trip.id, position=1, date=dt.date(2026, 8, 3)),
        ]
    )
    session.commit()

    with session_scope() as other:
        [loaded] = list_trips(other)
        assert [(s.date.day, s.position) for s in loaded.stops] == [
            (3, 1),
            (3, 2),
            (5, 3),
        ]
        assert loaded.stop_count == 3


def test_deleting_a_trip_removes_its_stops(session):
    trip = add_trip(session, START, END)
    session.add(Stop(trip_id=trip.id, position=1, date=START, place_name="Berlin"))
    session.commit()

    session.delete(trip)
    session.commit()

    assert session.query(Stop).count() == 0
