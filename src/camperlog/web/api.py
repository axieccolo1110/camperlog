"""JSON-API unter ``/api``. Alle Routen setzen einen Login voraus."""

from fastapi import APIRouter, Depends

from camperlog.database import add_fuel_entry, add_trip, get_all_fuel, get_all_trips
from camperlog.web.auth import require_login
from camperlog.web.schemas import FuelEntryCreate, FuelEntryRead, TripCreate, TripRead

router = APIRouter(prefix="/api", dependencies=[Depends(require_login)])


@router.get("/trips", response_model=list[TripRead])
def list_trips():
    return [
        TripRead(
            id=t.id, origin=t.origin, destination=t.destination, km=t.km, date=t.date
        )
        for t in get_all_trips()
    ]


@router.post("/trips", response_model=TripRead, status_code=201)
def create_trip(body: TripCreate):
    t = add_trip(body.origin, body.destination, body.km, body.date)
    return TripRead(
        id=t.id, origin=t.origin, destination=t.destination, km=t.km, date=t.date
    )


@router.get("/fuel", response_model=list[FuelEntryRead])
def list_fuel():
    return [
        FuelEntryRead(
            id=e.id,
            date=e.date,
            liters=e.liters,
            price_per_liter=e.price_per_liter,
            odometer=e.odometer,
            total_cost=e.total_cost,
        )
        for e in get_all_fuel()
    ]


@router.post("/fuel", response_model=FuelEntryRead, status_code=201)
def create_fuel(body: FuelEntryCreate):
    e = add_fuel_entry(body.date, body.liters, body.price_per_liter, body.odometer)
    return FuelEntryRead(
        id=e.id,
        date=e.date,
        liters=e.liters,
        price_per_liter=e.price_per_liter,
        odometer=e.odometer,
        total_cost=e.total_cost,
    )
