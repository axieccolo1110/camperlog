"""JSON API under ``/api``. All routes require a login."""

import datetime as dt

from fastapi import APIRouter, Depends

from camperlog.db import Session, get_session
from camperlog.services.expenses import add_fuel_entry, list_fuel_entries
from camperlog.services.trips import add_trip, list_trips
from camperlog.web.auth import require_login
from camperlog.web.schemas import FuelEntryCreate, FuelEntryRead, TripCreate, TripRead

router = APIRouter(prefix="/api", dependencies=[Depends(require_login)])


@router.get("/trips", response_model=list[TripRead])
def get_trips(session: Session = Depends(get_session)):
    return [TripRead.model_validate(t) for t in list_trips(session)]


@router.post("/trips", response_model=TripRead, status_code=201)
def create_trip(body: TripCreate, session: Session = Depends(get_session)):
    trip = add_trip(
        session,
        body.origin,
        body.destination,
        body.km,
        dt.date.fromisoformat(body.date),
    )
    return TripRead.model_validate(trip)


@router.get("/fuel", response_model=list[FuelEntryRead])
def get_fuel(session: Session = Depends(get_session)):
    return [FuelEntryRead.model_validate(e) for e in list_fuel_entries(session)]


@router.post("/fuel", response_model=FuelEntryRead, status_code=201)
def create_fuel(body: FuelEntryCreate, session: Session = Depends(get_session)):
    entry = add_fuel_entry(
        session,
        dt.date.fromisoformat(body.date),
        body.liters,
        body.price_per_liter,
        body.odometer,
    )
    return FuelEntryRead.model_validate(entry)
