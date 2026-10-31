"""JSON API under ``/api``. All routes require a login."""

import datetime as dt
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Response

from camperlog.db import Session, get_session
from camperlog.labels import status_label
from camperlog.services.campsites import (
    add_campsite,
    effective_statuses,
    list_bookmarked_campsites,
    list_campsites,
)
from camperlog.services.expenses import add_fuel_entry, list_fuel_entries
from camperlog.services.geocoding import Geocoder, GeocodingUnavailable, get_geocoder
from camperlog.services.trips import (
    add_stop,
    add_trip,
    delete_stop,
    delete_trip,
    get_trip,
    list_trips,
    update_stop,
    update_trip,
)
from camperlog.web.auth import require_login
from camperlog.web.schemas import (
    CampsiteCreate,
    CampsiteRead,
    FuelEntryCreate,
    FuelEntryRead,
    GeocodeResponse,
    PlaceRead,
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


@router.put("/trips/{trip_id}", response_model=TripRead)
def replace_trip(
    trip_id: int, body: TripCreate, session: Session = Depends(get_session)
):
    trip = update_trip(
        session,
        trip_id,
        dt.date.fromisoformat(body.start_date),
        dt.date.fromisoformat(body.end_date),
        body.distance_km,
    )
    return TripRead.model_validate(trip)


@router.delete("/trips/{trip_id}", status_code=204)
def remove_trip(trip_id: int, session: Session = Depends(get_session)):
    delete_trip(session, trip_id)
    return Response(status_code=204)


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
        body.campsite_id,
    )
    return StopRead.model_validate(stop)


@router.put("/stops/{stop_id}", response_model=StopRead)
def replace_stop(
    stop_id: int, body: StopCreate, session: Session = Depends(get_session)
):
    stop = update_stop(
        session,
        stop_id,
        dt.date.fromisoformat(body.date),
        body.place_name,
        body.lat,
        body.lon,
        body.campsite_id,
    )
    return StopRead.model_validate(stop)


@router.delete("/stops/{stop_id}", status_code=204)
def remove_stop(stop_id: int, session: Session = Depends(get_session)):
    delete_stop(session, stop_id)
    return Response(status_code=204)


@router.get("/campsites", response_model=list[CampsiteRead])
def get_campsites(session: Session = Depends(get_session)):
    statuses = effective_statuses(session)
    return [
        CampsiteRead.model_validate(c).model_copy(
            update={"effective_status": statuses[c.id]}
        )
        for c in list_campsites(session)
    ]


@router.post("/campsites", response_model=CampsiteRead, status_code=201)
def create_campsite(body: CampsiteCreate, session: Session = Depends(get_session)):
    campsite = add_campsite(
        session,
        body.name,
        body.lat,
        body.lon,
        body.status,
        body.notes,
        body.playground,
        body.pets_allowed,
        body.external_url,
    )
    return CampsiteRead.model_validate(campsite).model_copy(
        update={"effective_status": effective_statuses(session)[campsite.id]}
    )


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


@router.get("/geocode", response_model=GeocodeResponse)
def geocode(
    q: str = Query("", max_length=200),
    geocoder: Geocoder = Depends(get_geocoder),
):
    """Look up coordinates for a place name. Never fails: if the service cannot be
    reached the answer says so (``unavailable``) and the form keeps working."""
    try:
        places = geocoder.search(q)
    except GeocodingUnavailable:
        return GeocodeResponse(results=[], unavailable=True)
    return GeocodeResponse(
        results=[
            PlaceRead(
                name=p.name,
                region=p.region,
                country=p.country,
                lat=p.lat,
                lon=p.lon,
                label=p.label,
            )
            for p in places
        ]
    )


def _campsite_feature(campsite: Any, status: str) -> dict[str, Any]:
    """A campsite as a GeoJSON feature. Note: GeoJSON wants [longitude, latitude]."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [campsite.lon, campsite.lat]},
        "properties": {
            "id": campsite.id,
            "name": campsite.name,
            "status": status,
            "status_label": status_label(status),
            "notes": campsite.notes,
            "playground": campsite.playground,
            "pets_allowed": campsite.pets_allowed,
            "external_url": campsite.external_url,
        },
    }


@router.get("/map")
def map_data(
    view: Literal["bookmarks"] = "bookmarks",
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """The data of the map as GeoJSON. ``view=bookmarks``: the campsites that are
    still only bookmarked."""
    return {
        "type": "FeatureCollection",
        "features": [
            _campsite_feature(c, "bookmarked")
            for c in list_bookmarked_campsites(session)
        ],
    }
