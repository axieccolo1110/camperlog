"""Private HTML pages. All routes require a login."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from camperlog.consumption import consumption_labels
from camperlog.database import get_all_fuel, get_all_trips
from camperlog.web.auth import require_login
from camperlog.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    trips = get_all_trips()
    fuel = get_all_fuel()

    total_km = sum(t.km for t in trips)
    total_fuel_cost = round(sum(e.total_cost for e in fuel), 2)

    fuel_chrono = sorted(fuel, key=lambda e: e.date)
    chart_labels = [e.date for e in fuel_chrono]
    chart_costs = [round(e.total_cost, 2) for e in fuel_chrono]

    labels = consumption_labels(fuel)
    fuel_entries = [
        {
            "date": e.date,
            "liters": e.liters,
            "price_per_liter": e.price_per_liter,
            "total_cost": e.total_cost,
            "odometer": e.odometer,
            "consumption": label,
        }
        for e, label in zip(fuel, labels)
    ][:10]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "show_logout": True,
            "trips": trips[:10],
            "fuel_entries": fuel_entries,
            "total_trips": len(trips),
            "total_km": total_km,
            "total_fuel_cost": total_fuel_cost,
            "chart_labels": chart_labels,
            "chart_costs": chart_costs,
        },
    )
