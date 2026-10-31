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
    """A station of a trip.

    Either free-standing (own place name and coordinates, both optional) or tied to
    a campsite, in which case the campsite's place applies.
    """

    __tablename__ = "stops"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"))
    position: Mapped[int]
    date: Mapped[dt.date]
    place_name: Mapped[str | None] = mapped_column(default=None)
    lat: Mapped[float | None] = mapped_column(default=None)
    lon: Mapped[float | None] = mapped_column(default=None)
    campsite_id: Mapped[int | None] = mapped_column(
        ForeignKey("campsites.id"), default=None
    )
    trip: Mapped[Trip] = relationship(back_populates="stops", init=False, repr=False)
    # No ``default``: a default of None would be assigned in __init__ and would
    # reset campsite_id to NULL when the stop is saved.
    campsite: Mapped["Campsite | None"] = relationship(init=False, repr=False)

    @property
    def effective_place_name(self) -> str | None:
        """The name of the campsite if there is one, else the stop's own place."""
        return self.campsite.name if self.campsite else self.place_name

    @property
    def effective_lat(self) -> float | None:
        return self.campsite.lat if self.campsite else self.lat

    @property
    def effective_lon(self) -> float | None:
        return self.campsite.lon if self.campsite else self.lon


class FuelEntry(Base):
    """A refueling."""

    __tablename__ = "fuel_entries"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    date: Mapped[dt.date]
    liters: Mapped[float]
    price_per_liter: Mapped[float]
    odometer: Mapped[int]
    total_cost: Mapped[float]


CAMPSITE_STATUSES = ("visited", "bookmarked")


class Campsite(Base):
    """A place of its own, independent of any trip (Stellplatz)."""

    __tablename__ = "campsites"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str]
    lat: Mapped[float]
    lon: Mapped[float]
    # Manual status. The effective status also depends on past stops (F3.2).
    status: Mapped[str] = mapped_column(default="bookmarked")
    notes: Mapped[str | None] = mapped_column(default=None)
    playground: Mapped[bool] = mapped_column(default=False)
    pets_allowed: Mapped[bool] = mapped_column(default=False)
    external_url: Mapped[str | None] = mapped_column(default=None)
