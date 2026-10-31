from datetime import date as _date

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _iso_date(value):
    """Domain objects carry real dates; the API speaks ISO strings."""
    return value.isoformat() if isinstance(value, _date) else value


class TripCreate(BaseModel):
    start_date: str
    end_date: str
    distance_km: int | None = Field(default=None, ge=1)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        _date.fromisoformat(v)
        return v


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: str
    end_date: str
    distance_km: int | None
    stop_count: int

    _dates_to_iso = field_validator("start_date", "end_date", mode="before")(_iso_date)


class StopCreate(BaseModel):
    date: str
    place_name: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        _date.fromisoformat(v)
        return v


class StopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    position: int
    date: str
    place_name: str | None
    lat: float | None
    lon: float | None

    _date_to_iso = field_validator("date", mode="before")(_iso_date)


class TripDetailRead(TripRead):
    stops: list[StopRead]


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
