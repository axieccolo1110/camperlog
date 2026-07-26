from typing import List

from camperlog.models import FuelEntry


def consumption_labels(entries: List[FuelEntry]) -> List[str]:
    """Berechnet L/100km-Labels, Index-parallel zu `entries`.

    Erwartet `entries` absteigend nach Datum sortiert (neueste zuerst), wie
    von `get_all_fuel()` geliefert. Der Vorgänger-km-Stand steht damit beim
    naechsten (aelteren) Eintrag, nicht beim vorherigen.
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
