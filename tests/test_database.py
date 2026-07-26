from camperlog.database import add_trip, get_all_trips


def test_add_trip(test_db):
    """Test: Eine Reise wird korrekt gespeichert."""
    trip = add_trip("München", "Berlin", 600, "2026-08-01")

    assert trip.id is not None
    assert trip.origin == "München"
    assert trip.destination == "Berlin"
    assert trip.km == 600
    assert trip.date == "2026-08-01"


def test_get_all_trips(test_db):
    """Test: Alle Reisen werden abgerufen."""
    add_trip("München", "Berlin", 600, "2026-08-01")
    add_trip("Berlin", "Hamburg", 300, "2026-08-05")

    trips = get_all_trips()

    assert len(trips) == 2
    assert trips[0].origin == "Berlin"
    assert trips[1].origin == "München"


def test_empty_trips_list(test_db):
    """Test: Leere Liste wenn keine Reisen existieren."""
    trips = get_all_trips()
    assert len(trips) == 0
