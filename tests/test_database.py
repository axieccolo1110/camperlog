from camperlog.database import add_trip, get_all_trips, add_fuel_entry, get_all_fuel


def test_add_trip(test_db):
    """A trip is stored correctly."""
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
    """Empty list when no trips exist."""
    trips = get_all_trips()
    assert len(trips) == 0


def test_add_fuel_entry(test_db):
    """A fuel entry is stored correctly."""
    entry = add_fuel_entry("2026-08-01", 50.5, 1.85, 45000)

    assert entry.id is not None
    assert entry.date == "2026-08-01"
    assert entry.liters == 50.5
    assert entry.price_per_liter == 1.85
    assert entry.odometer == 45000
    assert entry.total_cost == 50.5 * 1.85


def test_get_all_fuel(test_db):
    """All fuel entries are returned."""
    add_fuel_entry("2026-08-01", 50.5, 1.85, 45000)
    add_fuel_entry("2026-08-05", 40.0, 1.90, 45400)

    entries = get_all_fuel()

    assert len(entries) == 2
    assert entries[0].date == "2026-08-05"
    assert entries[1].date == "2026-08-01"


def test_empty_fuel_list(test_db):
    """Empty list when no fuel entries exist."""
    entries = get_all_fuel()
    assert len(entries) == 0
