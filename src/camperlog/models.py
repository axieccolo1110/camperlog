"""Domain classes. Each class is a dataclass and the ORM mapping at the same time.

See docs/adr/0004-domain-classes-are-orm-dataclasses.md.
"""

import datetime as dt

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Trip(Base):
    """A journey over a period, made of an ordered list of stops."""

    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    start_date: Mapped[dt.date]
    end_date: Mapped[dt.date]
    # Distance in km, entered by hand.
    distance_km: Mapped[int | None] = mapped_column(default=None)
    # Sorted by date; for the same date, by position (order of entry).
    stops: Mapped[list["Stop"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="[Stop.date, Stop.position]",
        default_factory=list,
        init=False,
    )

    @property
    def stop_count(self) -> int:
        return len(self.stops)


class Stop(Base):
    """A station of a trip. For now always free-standing (campsites come in M3)."""

    __tablename__ = "stops"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"))
    position: Mapped[int]
    date: Mapped[dt.date]
    place_name: Mapped[str | None] = mapped_column(default=None)
    lat: Mapped[float | None] = mapped_column(default=None)
    lon: Mapped[float | None] = mapped_column(default=None)
    trip: Mapped[Trip] = relationship(back_populates="stops", init=False, repr=False)


class FuelEntry(Base):
    """A refueling."""

    __tablename__ = "fuel_entries"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    date: Mapped[dt.date]
    liters: Mapped[float]
    price_per_liter: Mapped[float]
    odometer: Mapped[int]
    total_cost: Mapped[float]
