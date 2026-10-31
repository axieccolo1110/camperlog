from datetime import date as _date

from pydantic import BaseModel, Field, field_validator


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
    id: int
    origin: str
    destination: str
    km: int
    date: str


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
    id: int
    date: str
    liters: float
    price_per_liter: float
    odometer: int
    total_cost: float
