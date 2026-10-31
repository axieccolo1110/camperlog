from typing import List

from camperlog.models import FuelEntry


def consumption_labels(entries: List[FuelEntry]) -> List[str]:
    """Compute L/100km labels, index-parallel to `entries`.

    Expects `entries` sorted by date descending (newest first), as returned by
    `get_all_fuel()`. The previous odometer reading is therefore found at the
    next (older) entry, not at the preceding one.
    """
    labels: List[str] = []
    for i, entry in enumerate(entries):
        if i == len(entries) - 1:
            labels.append("-")
            continue

        km_diff = entry.odometer - entries[i + 1].odometer
        if km_diff > 0:
            labels.append(f"{(entry.liters / km_diff * 100):.1f}")
        else:
            labels.append("?")

    return labels
