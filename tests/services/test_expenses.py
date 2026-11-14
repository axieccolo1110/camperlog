import datetime as dt

import pytest

from camperlog.services.errors import NotFoundError, ValidationError
from camperlog.services.expenses import (
    add_fuel_entry,
    delete_fuel_entry,
    get_fuel_entry,
    list_fuel_entries,
    update_fuel_entry,
)


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


def _three_entries(session):
    """Three refuelings with readings 10000, 10500, 11000 (oldest first)."""
    return [
        add_fuel_entry(session, dt.date(2026, 7, 1), 40.0, 1.80, 10000),
        add_fuel_entry(session, dt.date(2026, 7, 15), 45.0, 1.85, 10500),
        add_fuel_entry(session, dt.date(2026, 7, 26), 48.0, 1.90, 11000),
    ]


def test_list_fuel_entries_same_date_later_entry_first(session):
    first = add_fuel_entry(session, dt.date(2026, 7, 1), 40.0, 1.80, 10000)
    second = add_fuel_entry(session, dt.date(2026, 7, 1), 30.0, 1.80, 10300)

    assert [e.id for e in list_fuel_entries(session)] == [second.id, first.id]


def test_update_fuel_entry_replaces_fields_and_recomputes_total(session):
    _, middle, _ = _three_entries(session)

    entry = update_fuel_entry(
        session, middle.id, dt.date(2026, 7, 16), 50.0, 2.0, 10600
    )

    assert entry.date == dt.date(2026, 7, 16)
    assert (entry.liters, entry.price_per_liter, entry.odometer) == (50.0, 2.0, 10600)
    assert entry.total_cost == 100.0
    assert get_fuel_entry(session, middle.id).total_cost == 100.0


def test_update_fuel_entry_unknown_entry(session):
    with pytest.raises(NotFoundError, match="42"):
        update_fuel_entry(session, 42, dt.date(2026, 7, 1), 40.0, 1.8, 10000)


@pytest.mark.parametrize("odometer", [10000, 9000])
def test_update_fuel_entry_reading_must_exceed_the_previous_one(session, odometer):
    _, middle, _ = _three_entries(session)

    with pytest.raises(ValidationError, match="vorherigen.*10000 km am 2026-07-01"):
        update_fuel_entry(session, middle.id, middle.date, 45.0, 1.85, odometer)

    assert get_fuel_entry(session, middle.id).odometer == 10500


@pytest.mark.parametrize("odometer", [11000, 12000])
def test_update_fuel_entry_reading_must_stay_below_the_next_one(session, odometer):
    _, middle, _ = _three_entries(session)

    with pytest.raises(ValidationError, match="nächsten.*11000 km am 2026-07-26"):
        update_fuel_entry(session, middle.id, middle.date, 45.0, 1.85, odometer)


def test_update_fuel_entry_newest_and_oldest_have_only_one_neighbor(session):
    oldest, _, newest = _three_entries(session)

    update_fuel_entry(session, oldest.id, oldest.date, 40.0, 1.8, 1)
    update_fuel_entry(session, newest.id, newest.date, 48.0, 1.9, 99999)

    with pytest.raises(ValidationError):
        update_fuel_entry(session, newest.id, newest.date, 48.0, 1.9, 10500)


def test_update_fuel_entry_new_date_is_checked_against_the_new_neighbors(session):
    oldest, _, _ = _three_entries(session)

    # Moved behind the entry with 10500 km, but its own reading is lower.
    with pytest.raises(ValidationError):
        update_fuel_entry(session, oldest.id, dt.date(2026, 7, 20), 40.0, 1.8, 10000)

    # Moved between the 10500 and 11000 entries with a fitting reading.
    moved = update_fuel_entry(
        session, oldest.id, dt.date(2026, 7, 20), 40.0, 1.8, 10700
    )
    assert [e.odometer for e in list_fuel_entries(session)] == [11000, 10700, 10500]
    assert moved.date == dt.date(2026, 7, 20)


def test_update_fuel_entry_other_field_on_an_out_of_order_entry_is_allowed(session):
    """Fixing a price must work even if the entry's reading was never consistent."""
    add_fuel_entry(session, dt.date(2026, 7, 1), 40.0, 1.80, 10000)
    odd = add_fuel_entry(session, dt.date(2026, 7, 15), 45.0, 1.85, 9000)

    entry = update_fuel_entry(session, odd.id, odd.date, 45.0, 1.90, 9000)

    assert entry.price_per_liter == 1.90


def test_delete_fuel_entry_removes_it(session):
    first, middle, last = _three_entries(session)

    delete_fuel_entry(session, middle.id)

    assert [e.id for e in list_fuel_entries(session)] == [last.id, first.id]


def test_delete_fuel_entry_unknown_entry(session):
    with pytest.raises(NotFoundError, match="42"):
        delete_fuel_entry(session, 42)
