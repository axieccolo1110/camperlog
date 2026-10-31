from camperlog.consumption import consumption_labels
from camperlog.models import FuelEntry


def _entry(odometer, liters, date="2026-01-01"):
    return FuelEntry(
        id=1,
        date=date,
        liters=liters,
        price_per_liter=1.80,
        odometer=odometer,
        total_cost=liters * 1.80,
    )


def test_consumption_labels_chronological():
    # newest first, as returned by get_all_fuel()
    entries = [
        _entry(11000, 48.0, "2026-07-26"),
        _entry(10500, 45.0, "2026-07-15"),
        _entry(10000, 50.0, "2026-07-01"),
    ]

    labels = consumption_labels(entries)

    assert labels == ["9.6", "9.0", "-"]


def test_consumption_labels_single_entry():
    entries = [_entry(10000, 50.0)]

    assert consumption_labels(entries) == ["-"]


def test_consumption_labels_empty():
    assert consumption_labels([]) == []


def test_consumption_labels_non_positive_km_diff():
    # a newer entry has a lower or equal odometer reading than the next (older)
    # entry -> data anomaly
    entries = [
        _entry(10000, 40.0, "2026-07-15"),
        _entry(10000, 50.0, "2026-07-01"),
    ]

    assert consumption_labels(entries) == ["?", "-"]
