"""JSON API under ``/api``. All routes require a login."""

import datetime as dt

from fastapi import APIRouter, Depends

from camperlog.db import Session, get_session
from camperlog.services.expenses import add_fuel_entry, list_fuel_entries
from camperlog.services.trips import add_stop, add_trip, get_trip, list_trips
from camperlog.web.auth import require_login
from camperlog.web.schemas import (
    FuelEntryCreate,
    FuelEntryRead,
    StopCreate,
    StopRead,
    TripCreate,
    TripDetailRead,
    TripRead,
)

router = APIRouter(prefix="/api", dependencies=[Depends(require_login)])


@router.get("/trips", response_model=list[TripRead])
def get_trips(session: Session = Depends(get_session)):
    return [TripRead.model_validate(t) for t in list_trips(session)]


@router.post("/trips", response_model=TripRead, status_code=201)
def create_trip(body: TripCreate, session: Session = Depends(get_session)):
    trip = add_trip(
        session,
        dt.date.fromisoformat(body.start_date),
        dt.date.fromisoformat(body.end_date),
        body.distance_km,
    )
    return TripRead.model_validate(trip)


@router.get("/trips/{trip_id}", response_model=TripDetailRead)
def get_trip_detail(trip_id: int, session: Session = Depends(get_session)):
    return TripDetailRead.model_validate(get_trip(session, trip_id))


@router.post("/trips/{trip_id}/stops", response_model=StopRead, status_code=201)
def create_stop(
    trip_id: int, body: StopCreate, session: Session = Depends(get_session)
):
    stop = add_stop(
        session,
        trip_id,
        dt.date.fromisoformat(body.date),
        body.place_name,
        body.lat,
        body.lon,
    )
    return StopRead.model_validate(stop)


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
