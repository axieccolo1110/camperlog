# Domain classes are also the ORM mapping (MappedAsDataclass)

Until now every object existed three times: as a plain `@dataclass` in `models.py`, as an ORM class (`TripRow`, `FuelEntryRow`) in `database.py` and as a Pydantic schema at the web boundary, with hand-written conversion between all three. The realignment adds Stop, Campsite, Expense, Category and ShareLink. We therefore use `MappedAsDataclass` from SQLAlchemy 2: one class is both a dataclass and an ORM mapping. Pydantic stays at the web boundary only. We knowingly give up the former separation "plain data without ORM coupling". The coupling to SQLAlchemy is limited to `models.py` and `services/`; the entry points only see services.

## Considered Options

- Keep the triple representation — rejected, because every new column would have to be maintained in three places plus two conversions.
- Pydantic models as domain classes (e.g. SQLModel) — rejected, because that additionally couples a validation and a persistence library and adds another dependency without simplifying the web boundary.
