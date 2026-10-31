import datetime as dt

import pytest

from camperlog.db import session_scope
from camperlog.models import Stop
from camperlog.services.errors import NotFoundError, ValidationError
from camperlog.services.trips import add_stop, add_trip, get_trip, list_trips

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


# --- stops -------------------------------------------------------------------


@pytest.fixture
def trip(session):
    return add_trip(session, START, END)


def test_add_stop_inside_the_period(session, trip):
    stop = add_stop(session, trip.id, dt.date(2026, 8, 10), "Verona", 45.438, 10.992)

    assert stop.id is not None
    assert (stop.date, stop.place_name, stop.lat, stop.lon) == (
        dt.date(2026, 8, 10),
        "Verona",
        45.438,
        10.992,
    )


def test_stop_needs_neither_place_nor_coordinates(session, trip):
    stop = add_stop(session, trip.id, START)

    assert (stop.place_name, stop.lat, stop.lon) == (None, None, None)


def test_blank_place_name_becomes_none(session, trip):
    assert add_stop(session, trip.id, START, "   ").place_name is None


@pytest.mark.parametrize("day", [START, END])
def test_period_boundaries_are_inclusive(session, trip, day):
    assert add_stop(session, trip.id, day).date == day


@pytest.mark.parametrize(
    "day", [START - dt.timedelta(days=1), END + dt.timedelta(days=1)]
)
def test_stop_outside_the_period_is_rejected(session, trip, day):
    with pytest.raises(ValidationError, match="Zeitraum der Reise"):
        add_stop(session, trip.id, day)
    assert get_trip(session, trip.id).stop_count == 0


def test_unknown_trip_is_not_found(session):
    with pytest.raises(NotFoundError, match="999"):
        add_stop(session, 999, START)
    with pytest.raises(NotFoundError):
        get_trip(session, 999)


@pytest.mark.parametrize(
    "lat, lon, message",
    [
        (45.0, None, "Breite und Länge"),
        (None, 10.0, "Breite und Länge"),
        (91.0, 10.0, "Breite"),
        (-91.0, 10.0, "Breite"),
        (45.0, 181.0, "Länge"),
        (45.0, -181.0, "Länge"),
    ],
)
def test_invalid_coordinates_are_rejected(session, trip, lat, lon, message):
    with pytest.raises(ValidationError, match=message):
        add_stop(session, trip.id, START, lat=lat, lon=lon)
    assert get_trip(session, trip.id).stop_count == 0


def test_a_new_stop_goes_to_the_end_of_its_day(session, trip):
    day = dt.date(2026, 8, 3)
    add_stop(session, trip.id, day, "first")
    add_stop(session, trip.id, dt.date(2026, 8, 9), "later day")
    add_stop(session, trip.id, day, "second")

    stops = get_trip(session, trip.id).stops

    assert [s.place_name for s in stops] == ["first", "second", "later day"]
    assert [s.position for s in stops] == [1, 3, 2]


def test_stops_sort_by_date_even_if_entered_out_of_order(session, trip):
    add_stop(session, trip.id, dt.date(2026, 8, 20), "end")
    add_stop(session, trip.id, dt.date(2026, 8, 2), "start")

    assert [s.place_name for s in get_trip(session, trip.id).stops] == ["start", "end"]


def test_stops_of_other_trips_do_not_interfere(session, trip):
    other = add_trip(session, START, END)
    add_stop(session, other.id, START, "other")

    assert add_stop(session, trip.id, START, "mine").position == 1
