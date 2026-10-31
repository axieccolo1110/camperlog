import datetime as dt

import pytest

from camperlog.services.campsites import add_campsite
from camperlog.services.map_data import retrospective
from camperlog.services.trips import add_stop, add_trip

TODAY = dt.date(2026, 10, 31)
D = dt.date


def _trip(session, start=D(2026, 8, 1), end=D(2026, 8, 31)):
    return add_trip(session, start, end)


def test_nothing_recorded_gives_nothing(session):
    result = retrospective(session, TODAY)

    assert (result.campsites, result.stops, result.routes) == ([], [], [])


def test_only_visited_campsites_are_pins(session):
    visited = add_campsite(session, "Besucht", 45.0, 10.0, "visited")
    add_campsite(session, "Vorgemerkt", 46.0, 11.0)

    assert [c.id for c in retrospective(session, TODAY).campsites] == [visited.id]


def test_a_campsite_becomes_a_pin_once_a_stop_is_in_the_past(session):
    campsite = add_campsite(session, "Wiese", 45.0, 10.0)
    trip = _trip(session)
    add_stop(session, trip.id, D(2026, 8, 10), campsite_id=campsite.id)

    assert retrospective(session, D(2026, 8, 1)).campsites == []
    assert [c.id for c in retrospective(session, D(2026, 8, 11)).campsites] == [
        campsite.id
    ]


def test_free_standing_stops_with_coordinates_are_pins(session):
    trip = _trip(session)
    stop = add_stop(session, trip.id, D(2026, 8, 5), "Verona", 45.4, 10.9)

    [pin] = retrospective(session, TODAY).stops

    assert (pin.stop_id, pin.trip_id, pin.date) == (stop.id, trip.id, D(2026, 8, 5))
    assert (pin.place_name, pin.lat, pin.lon) == ("Verona", 45.4, 10.9)


def test_stops_without_coordinates_are_no_pins(session):
    trip = _trip(session)
    add_stop(session, trip.id, D(2026, 8, 5), "Irgendwo")
    add_stop(session, trip.id, D(2026, 8, 6))

    assert retrospective(session, TODAY).stops == []


def test_stops_at_campsites_are_not_pins_of_their_own(session):
    campsite = add_campsite(session, "Wiese", 45.0, 10.0, "visited")
    trip = _trip(session)
    add_stop(session, trip.id, D(2026, 8, 5), campsite_id=campsite.id)

    result = retrospective(session, TODAY)

    assert result.stops == []
    assert [c.id for c in result.campsites] == [campsite.id]


def test_the_route_connects_the_places_in_order(session):
    trip = _trip(session)
    add_stop(session, trip.id, D(2026, 8, 20), "C", 3.0, 30.0)
    add_stop(session, trip.id, D(2026, 8, 2), "A", 1.0, 10.0)
    add_stop(session, trip.id, D(2026, 8, 10), "B", 2.0, 20.0)

    [route] = retrospective(session, TODAY).routes

    assert route.points == [(1.0, 10.0), (2.0, 20.0), (3.0, 30.0)]
    assert (route.trip_id, route.start_date, route.end_date) == (
        trip.id,
        D(2026, 8, 1),
        D(2026, 8, 31),
    )


def test_stops_on_the_same_day_keep_the_order_of_entry(session):
    trip = _trip(session)
    add_stop(session, trip.id, D(2026, 8, 5), "first", 1.0, 10.0)
    add_stop(session, trip.id, D(2026, 8, 5), "second", 2.0, 20.0)

    [route] = retrospective(session, TODAY).routes

    assert route.points == [(1.0, 10.0), (2.0, 20.0)]


def test_stops_without_coordinates_do_not_interrupt_the_line(session):
    trip = _trip(session)
    add_stop(session, trip.id, D(2026, 8, 2), "A", 1.0, 10.0)
    add_stop(session, trip.id, D(2026, 8, 5), "ohne Koordinaten")
    add_stop(session, trip.id, D(2026, 8, 8))
    add_stop(session, trip.id, D(2026, 8, 10), "B", 2.0, 20.0)

    [route] = retrospective(session, TODAY).routes

    assert route.points == [(1.0, 10.0), (2.0, 20.0)]


def test_campsite_stops_contribute_the_campsite_coordinates(session):
    campsite = add_campsite(session, "Wiese", 5.0, 50.0)  # still only bookmarked
    trip = _trip(session)
    add_stop(session, trip.id, D(2026, 8, 2), "A", 1.0, 10.0)
    add_stop(session, trip.id, D(2026, 8, 5), campsite_id=campsite.id)
    add_stop(session, trip.id, D(2026, 8, 9), "B", 2.0, 20.0)

    [route] = retrospective(session, TODAY).routes

    assert route.points == [(1.0, 10.0), (5.0, 50.0), (2.0, 20.0)]


@pytest.mark.parametrize("places", [0, 1])
def test_fewer_than_two_places_have_no_line(session, places):
    trip = _trip(session)
    for i in range(places):
        add_stop(session, trip.id, D(2026, 8, 2), "A", 1.0, 10.0)
    add_stop(session, trip.id, D(2026, 8, 9))  # no coordinates

    assert retrospective(session, TODAY).routes == []


def test_every_trip_gets_its_own_line_oldest_first(session):
    later = add_trip(session, D(2026, 9, 1), D(2026, 9, 10))
    earlier = add_trip(session, D(2026, 7, 1), D(2026, 7, 10))
    for trip, base in ((later, 20.0), (earlier, 10.0)):
        add_stop(session, trip.id, trip.start_date, "a", base, base)
        add_stop(session, trip.id, trip.end_date, "b", base + 1, base + 1)

    routes = retrospective(session, TODAY).routes

    assert [r.trip_id for r in routes] == [earlier.id, later.id]
    assert routes[0].points == [(10.0, 10.0), (11.0, 11.0)]
    assert routes[1].points == [(20.0, 20.0), (21.0, 21.0)]


def test_stops_in_the_future_are_part_of_the_picture(session):
    """The PRD does not limit the retrospective to the past: nothing is invented."""
    trip = add_trip(session, D(2026, 11, 1), D(2026, 11, 10))
    add_stop(session, trip.id, D(2026, 11, 2), "A", 1.0, 10.0)
    add_stop(session, trip.id, D(2026, 11, 5), "B", 2.0, 20.0)

    result = retrospective(session, TODAY)

    assert len(result.stops) == 2 and len(result.routes) == 1
