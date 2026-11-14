"""Expenses. For now only refuelings; categories and the rest follow in M4."""

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from camperlog.models import FuelEntry
from camperlog.services.errors import NotFoundError, ValidationError


def add_fuel_entry(
    session: Session,
    date: dt.date,
    liters: float,
    price_per_liter: float,
    odometer: int,
) -> FuelEntry:
    entry = FuelEntry(
        date=date,
        liters=liters,
        price_per_liter=price_per_liter,
        odometer=odometer,
        total_cost=liters * price_per_liter,
    )
    session.add(entry)
    session.commit()
    return entry


def list_fuel_entries(session: Session) -> list[FuelEntry]:
    """All refuelings, newest first (on the same date the later entry comes first)."""
    query = select(FuelEntry).order_by(FuelEntry.date.desc(), FuelEntry.id.desc())
    return list(session.scalars(query.execution_options(populate_existing=True)))


def get_fuel_entry(session: Session, entry_id: int) -> FuelEntry:
    """A refueling. Raises NotFoundError if it does not exist."""
    entry = session.get(FuelEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"Tankfüllung {entry_id} gibt es nicht.")
    return entry


def _check_odometer_between_neighbors(
    session: Session, entry: FuelEntry, date: dt.date, odometer: int
) -> None:
    """The odometer reading must lie between the entries before and after it.

    Neighbors are taken in the order date, then entry number. The consumption of
    the next refueling is computed from this reading, so a reading out of order
    would turn it into nonsense.
    """
    others = list(
        session.scalars(
            select(FuelEntry)
            .where(FuelEntry.id != entry.id)
            .order_by(FuelEntry.date, FuelEntry.id)
        )
    )
    key = (date, entry.id)
    before = [e for e in others if (e.date, e.id) < key]
    after = [e for e in others if (e.date, e.id) > key]
    previous = before[-1] if before else None
    following = after[0] if after else None
    if previous is not None and odometer <= previous.odometer:
        raise ValidationError(
            f"Der Kilometerstand muss über dem der vorherigen Tankfüllung liegen "
            f"({previous.odometer} km am {previous.date.isoformat()})."
        )
    if following is not None and odometer >= following.odometer:
        raise ValidationError(
            f"Der Kilometerstand muss unter dem der nächsten Tankfüllung liegen "
            f"({following.odometer} km am {following.date.isoformat()})."
        )


def update_fuel_entry(
    session: Session,
    entry_id: int,
    date: dt.date,
    liters: float,
    price_per_liter: float,
    odometer: int,
) -> FuelEntry:
    """Replace all fields of a refueling; the total cost is recomputed.

    If date or odometer reading change, the reading must stay between the
    neighboring refuelings. Otherwise it is not checked, so a wrong price can be
    fixed even on an entry that was already out of order.
    """
    entry = get_fuel_entry(session, entry_id)
    if (date, odometer) != (entry.date, entry.odometer):
        _check_odometer_between_neighbors(session, entry, date, odometer)
    entry.date = date
    entry.liters = liters
    entry.price_per_liter = price_per_liter
    entry.odometer = odometer
    entry.total_cost = liters * price_per_liter
    session.commit()
    return entry


def delete_fuel_entry(session: Session, entry_id: int) -> None:
    session.delete(get_fuel_entry(session, entry_id))
    session.commit()
