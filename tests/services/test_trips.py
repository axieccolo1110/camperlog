import datetime as dt

from camperlog.services.trips import add_trip, list_trips


def test_add_trip(session):
    """A trip is stored correctly."""
    trip = add_trip(session, "München", "Berlin", 600, dt.date(2026, 8, 1))

    assert trip.id is not None
    assert trip.origin == "München"
    assert trip.destination == "Berlin"
    assert trip.km == 600
    assert trip.date == dt.date(2026, 8, 1)


def test_list_trips_newest_first(session):
    """All trips are returned, newest first."""
    add_trip(session, "München", "Berlin", 600, dt.date(2026, 8, 1))
    add_trip(session, "Berlin", "Hamburg", 300, dt.date(2026, 8, 5))

    trips = list_trips(session)

    assert [t.destination for t in trips] == ["Hamburg", "Berlin"]


def test_list_trips_empty(session):
    """Empty list when no trips exist."""
    assert list_trips(session) == []


def test_trips_survive_a_new_session(session):
    """add_trip commits: another session sees the data."""
    from camperlog.db import session_scope

    add_trip(session, "München", "Berlin", 600, dt.date(2026, 8, 1))

    with session_scope() as other:
        assert len(list_trips(other)) == 1
