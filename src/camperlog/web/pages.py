"""Private HTML pages. All routes require a login."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from camperlog.consumption import consumption_labels
from camperlog.db import Session, get_session
from camperlog.services.expenses import list_fuel_entries
from camperlog.services.trips import get_trip, list_trips
from camperlog.web.auth import require_login
from camperlog.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])


def _fuel_entries_with_consumption(fuel):
    labels = consumption_labels(fuel)
    return [
        {
            "date": e.date,
            "liters": e.liters,
            "price_per_liter": e.price_per_liter,
            "total_cost": e.total_cost,
            "odometer": e.odometer,
            "consumption": label,
        }
        for e, label in zip(fuel, labels)
    ]


def _avg_price_per_liter(fuel) -> float | None:
    total_liters = sum(e.liters for e in fuel)
    if total_liters <= 0:
        return None
    return sum(e.total_cost for e in fuel) / total_liters


def _avg_consumption(entries: list[dict]) -> float | None:
    values = [
        float(e["consumption"]) for e in entries if e["consumption"] not in ("-", "?")
    ]
    if not values:
        return None
    return sum(values) / len(values)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    trips = list_trips(session)
    fuel = list_fuel_entries(session)

    total_km = sum(t.distance_km or 0 for t in trips)
    total_fuel_cost = round(sum(e.total_cost for e in fuel), 2)

    fuel_chrono = sorted(fuel, key=lambda e: e.date)
    chart_labels = [e.date.isoformat() for e in fuel_chrono]
    chart_costs = [round(e.total_cost, 2) for e in fuel_chrono]

    fuel_entries = _fuel_entries_with_consumption(fuel)[:3]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "show_logout": True,
            "active_nav": "dashboard",
            "trips": trips[:10],
            "fuel_entries": fuel_entries,
            "total_trips": len(trips),
            "total_km": total_km,
            "total_fuel_cost": total_fuel_cost,
            "avg_price_per_liter": _avg_price_per_liter(fuel),
            "chart_labels": chart_labels,
            "chart_costs": chart_costs,
        },
    )


@router.get("/tanken", response_class=HTMLResponse)
def tanken(request: Request, session: Session = Depends(get_session)):
    fuel = list_fuel_entries(session)
    fuel_entries = _fuel_entries_with_consumption(fuel)

    fuel_chrono = sorted(fuel, key=lambda e: e.date)
    chart_labels = [e.date.isoformat() for e in fuel_chrono]
    chart_costs = [round(e.total_cost, 2) for e in fuel_chrono]

    return templates.TemplateResponse(
        request=request,
        name="tanken.html",
        context={
            "show_logout": True,
            "active_nav": "tanken",
            "fuel_entries": fuel_entries,
            "total_cost": round(sum(e.total_cost for e in fuel), 2),
            "avg_price_per_liter": _avg_price_per_liter(fuel),
            "avg_consumption": _avg_consumption(fuel_entries),
            "chart_labels": chart_labels,
            "chart_costs": chart_costs,
        },
    )


@router.get("/trips/{trip_id}", response_class=HTMLResponse)
def trip_detail(
    trip_id: int, request: Request, session: Session = Depends(get_session)
):
    return templates.TemplateResponse(
        request=request,
        name="trip.html",
        context={"show_logout": True, "trip": get_trip(session, trip_id)},
    )
