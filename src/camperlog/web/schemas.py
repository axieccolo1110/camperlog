from datetime import date as _date

from pydantic import BaseModel, field_validator


class TripCreate(BaseModel):
    origin: str
    destination: str
    km: int
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        _date.fromisoformat(v)
        return v


class TripRead(BaseModel):
    id: int
    origin: str
    destination: str
    km: int
    date: str


class FuelEntryCreate(BaseModel):
    date: str
    liters: float
    price_per_liter: float
    odometer: int

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        _date.fromisoformat(v)
        return v


class FuelEntryRead(BaseModel):
    id: int
    date: str
    liters: float
    price_per_liter: float
    odometer: int
    total_cost: float
