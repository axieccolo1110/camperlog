from datetime import date as _date

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _iso_date(value):
    """Domain objects carry real dates; the API speaks ISO strings."""
    return value.isoformat() if isinstance(value, _date) else value


class TripCreate(BaseModel):
    origin: str
    destination: str
    km: int = Field(ge=1)
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        _date.fromisoformat(v)
        return v


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origin: str
    destination: str
    km: int
    date: str

    _date_to_iso = field_validator("date", mode="before")(_iso_date)


class FuelEntryCreate(BaseModel):
    date: str
    liters: float = Field(gt=0)
    price_per_liter: float = Field(gt=0)
    odometer: int = Field(ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        _date.fromisoformat(v)
        return v


class FuelEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    liters: float
    price_per_liter: float
    odometer: int
    total_cost: float

    _date_to_iso = field_validator("date", mode="before")(_iso_date)
