import datetime as dt

import pytest

from camperlog.db import session_scope
from camperlog.models import Stop
from camperlog.services.errors import NotFoundError, ValidationError
from camperlog.services.trips import (
    add_stop,
    add_trip,
    delete_stop,
    delete_trip,
    get_stop,
    get_trip,
    list_trips,
    update_stop,
    update_trip,
)

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


# --- editing and deleting trips ----------------------------------------------


def test_update_trip_period_and_distance(session, trip):
    updated = update_trip(
        session, trip.id, dt.date(2026, 7, 30), dt.date(2026, 9, 1), 900
    )

    assert (updated.start_date, updated.end_date, updated.distance_km) == (
        dt.date(2026, 7, 30),
        dt.date(2026, 9, 1),
        900,
    )
    with session_scope() as other:
        assert get_trip(other, trip.id).distance_km == 900


def test_update_trip_can_remove_the_distance(session):
    trip = add_trip(session, START, END, 600)

    assert update_trip(session, trip.id, START, END, None).distance_km is None


def test_new_period_must_include_all_stops(session, trip):
    add_stop(session, trip.id, dt.date(2026, 8, 5))
    add_stop(session, trip.id, dt.date(2026, 8, 20))

    with pytest.raises(ValidationError, match="2026-08-20"):
        update_trip(session, trip.id, START, dt.date(2026, 8, 10), None)

    unchanged = get_trip(session, trip.id)
    assert unchanged.end_date == END


def test_new_period_may_end_exactly_on_a_stop(session, trip):
    add_stop(session, trip.id, dt.date(2026, 8, 5))
    add_stop(session, trip.id, dt.date(2026, 8, 20))

    updated = update_trip(
        session, trip.id, dt.date(2026, 8, 5), dt.date(2026, 8, 20), 1
    )

    assert updated.stop_count == 2


@pytest.mark.parametrize(
    "start, end, km, message",
    [
        (END, START, None, "Enddatum"),
        (START, END, 0, "Distanz"),
    ],
)
def test_update_trip_validates_like_add_trip(session, trip, start, end, km, message):
    with pytest.raises(ValidationError, match=message):
        update_trip(session, trip.id, start, end, km)


def test_update_unknown_trip(session):
    with pytest.raises(NotFoundError):
        update_trip(session, 999, START, END, None)


def test_delete_trip_removes_its_stops_only(session, trip):
    other = add_trip(session, START, END)
    add_stop(session, trip.id, START, "gone")
    add_stop(session, other.id, START, "stays")

    delete_trip(session, trip.id)

    assert [t.id for t in list_trips(session)] == [other.id]
    assert [s.place_name for s in session.query(Stop).all()] == ["stays"]


def test_delete_unknown_trip(session):
    with pytest.raises(NotFoundError):
        delete_trip(session, 999)


# --- editing and deleting stops ----------------------------------------------


def test_update_stop(session, trip):
    stop = add_stop(session, trip.id, START, "Verona", 45.4, 10.9)

    updated = update_stop(session, stop.id, dt.date(2026, 8, 3), "Rimini", 44.0, 12.5)

    assert (updated.date, updated.place_name, updated.lat, updated.lon) == (
        dt.date(2026, 8, 3),
        "Rimini",
        44.0,
        12.5,
    )
    assert updated.position == stop.position


def test_update_stop_can_remove_place_and_coordinates(session, trip):
    stop = add_stop(session, trip.id, START, "Verona", 45.4, 10.9)

    updated = update_stop(session, stop.id, START, "  ", None, None)

    assert (updated.place_name, updated.lat, updated.lon) == (None, None, None)


def test_update_stop_keeps_the_rules_of_a_new_stop(session, trip):
    stop = add_stop(session, trip.id, START, "Verona")

    with pytest.raises(ValidationError, match="Zeitraum der Reise"):
        update_stop(session, stop.id, END + dt.timedelta(days=1), "Verona", None, None)
    with pytest.raises(ValidationError, match="Breite und Länge"):
        update_stop(session, stop.id, START, "Verona", 45.4, None)

    assert get_stop(session, stop.id).date == START


def test_update_stop_reorders_by_date(session, trip):
    early = add_stop(session, trip.id, dt.date(2026, 8, 2), "early")
    add_stop(session, trip.id, dt.date(2026, 8, 9), "late")

    update_stop(session, early.id, dt.date(2026, 8, 15), "early", None, None)

    assert [s.place_name for s in get_trip(session, trip.id).stops] == ["late", "early"]


def test_delete_stop(session, trip):
    keep = add_stop(session, trip.id, START, "keep")
    gone = add_stop(session, trip.id, START, "gone")

    delete_stop(session, gone.id)

    assert [s.id for s in get_trip(session, trip.id).stops] == [keep.id]


def test_unknown_stop(session):
    with pytest.raises(NotFoundError, match="999"):
        get_stop(session, 999)
    with pytest.raises(NotFoundError):
        update_stop(session, 999, START, None, None, None)
    with pytest.raises(NotFoundError):
        delete_stop(session, 999)


# --- stops tied to a campsite -------------------------------------------------

from camperlog.services.campsites import add_campsite  # noqa: E402


@pytest.fixture
def campsite(session):
    return add_campsite(session, "Wiese am See", 46.668, 11.159)


def test_stop_takes_over_the_place_of_its_campsite(session, trip, campsite):
    stop = add_stop(session, trip.id, START, campsite_id=campsite.id)

    loaded = get_trip(session, trip.id).stops[0]
    assert loaded.id == stop.id
    assert loaded.campsite_id == campsite.id
    assert (
        loaded.effective_place_name,
        loaded.effective_lat,
        loaded.effective_lon,
    ) == (
        "Wiese am See",
        46.668,
        11.159,
    )
    assert (loaded.place_name, loaded.lat, loaded.lon) == (None, None, None)


def test_free_standing_stop_uses_its_own_place(session, trip):
    stop = add_stop(session, trip.id, START, "Verona", 45.4, 10.9)

    assert (stop.effective_place_name, stop.effective_lat, stop.effective_lon) == (
        "Verona",
        45.4,
        10.9,
    )


def test_stop_with_campsite_is_readable_after_the_session_closed(
    session, trip, campsite
):
    add_stop(session, trip.id, START, campsite_id=campsite.id)

    with session_scope() as other:
        stops = list_trips(other)[0].stops
    assert stops[0].effective_place_name == "Wiese am See"  # no lazy load needed


@pytest.mark.parametrize(
    "extra", [{"place_name": "Verona"}, {"lat": 45.4, "lon": 10.9}, {"lat": 45.4}]
)
def test_campsite_and_own_place_exclude_each_other(session, trip, campsite, extra):
    with pytest.raises(ValidationError, match="Stellplatz"):
        add_stop(session, trip.id, START, campsite_id=campsite.id, **extra)
    assert get_trip(session, trip.id).stop_count == 0


def test_unknown_campsite(session, trip):
    with pytest.raises(NotFoundError, match="Stellplatz 999"):
        add_stop(session, trip.id, START, campsite_id=999)
    assert get_trip(session, trip.id).stop_count == 0


def test_stop_with_campsite_still_obeys_the_trip_period(session, trip, campsite):
    with pytest.raises(ValidationError, match="Zeitraum der Reise"):
        add_stop(session, trip.id, END + dt.timedelta(days=1), campsite_id=campsite.id)


def test_update_stop_ties_it_to_a_campsite_and_back(session, trip, campsite):
    stop = add_stop(session, trip.id, START, "Verona", 45.4, 10.9)

    tied = update_stop(session, stop.id, START, None, None, None, campsite.id)
    assert tied.campsite_id == campsite.id
    assert (tied.place_name, tied.lat, tied.lon) == (None, None, None)

    freed = update_stop(session, stop.id, START, "Rimini", 44.0, 12.5, None)
    assert freed.campsite_id is None
    assert freed.effective_place_name == "Rimini"


def test_update_stop_rejects_campsite_plus_own_place(session, trip, campsite):
    stop = add_stop(session, trip.id, START, "Verona")

    with pytest.raises(ValidationError, match="Stellplatz"):
        update_stop(session, stop.id, START, "Verona", None, None, campsite.id)
    assert get_stop(session, stop.id).campsite_id is None


def test_update_stop_with_unknown_campsite(session, trip):
    stop = add_stop(session, trip.id, START, "Verona")

    with pytest.raises(NotFoundError):
        update_stop(session, stop.id, START, None, None, None, 999)


def test_a_campsite_can_be_used_by_stops_of_several_trips(session, campsite):
    first = add_trip(session, START, END)
    second = add_trip(session, START, END)

    add_stop(session, first.id, START, campsite_id=campsite.id)
    add_stop(session, second.id, START, campsite_id=campsite.id)

    assert get_trip(session, first.id).stops[0].campsite_id == campsite.id
    assert get_trip(session, second.id).stops[0].campsite_id == campsite.id
