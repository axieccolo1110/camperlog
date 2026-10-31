"""Domain classes. Each class is a dataclass and the ORM mapping at the same time.

See docs/adr/0004-domain-classes-are-orm-dataclasses.md.
"""

import datetime as dt

from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Trip(Base):
    """A single drive (becomes a multi-stop journey in M2)."""

    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    origin: Mapped[str]
    destination: Mapped[str]
    km: Mapped[int]
    date: Mapped[dt.date]


class FuelEntry(Base):
    """A refueling."""

    __tablename__ = "fuel_entries"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    date: Mapped[dt.date]
    liters: Mapped[float]
    price_per_liter: Mapped[float]
    odometer: Mapped[int]
    total_cost: Mapped[float]
