import datetime as dt

from camperlog.services.expenses import add_fuel_entry, list_fuel_entries


def test_add_fuel_entry_computes_total_cost(session):
    """A fuel entry is stored correctly, the total cost is liters x price."""
    entry = add_fuel_entry(session, dt.date(2026, 8, 1), 50.0, 1.80, 12500)

    assert entry.id is not None
    assert entry.date == dt.date(2026, 8, 1)
    assert entry.liters == 50.0
    assert entry.price_per_liter == 1.80
    assert entry.odometer == 12500
    assert entry.total_cost == 90.0


def test_list_fuel_entries_newest_first(session):
    """All fuel entries are returned, newest first."""
    add_fuel_entry(session, dt.date(2026, 7, 1), 40.0, 1.80, 10000)
    add_fuel_entry(session, dt.date(2026, 7, 15), 45.0, 1.85, 10500)

    entries = list_fuel_entries(session)

    assert [e.odometer for e in entries] == [10500, 10000]


def test_list_fuel_entries_empty(session):
    """Empty list when no fuel entries exist."""
    assert list_fuel_entries(session) == []
