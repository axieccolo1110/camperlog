from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from camperlog.consumption import consumption_labels
from camperlog.database import (
    add_fuel_entry,
    add_trip,
    get_all_fuel,
    get_all_trips,
    init_db,
)
from camperlog.web.schemas import FuelEntryCreate, FuelEntryRead, TripCreate, TripRead

TEMPLATES_DIR = Path(__file__).parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CamperLog API", version="0.1.0", lifespan=lifespan)
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/api/trips", response_model=list[TripRead])
def list_trips():
    return [
        TripRead(
            id=t.id, origin=t.origin, destination=t.destination, km=t.km, date=t.date
        )
        for t in get_all_trips()
    ]


@app.post("/api/trips", response_model=TripRead, status_code=201)
def create_trip(body: TripCreate):
    t = add_trip(body.origin, body.destination, body.km, body.date)
    return TripRead(
        id=t.id, origin=t.origin, destination=t.destination, km=t.km, date=t.date
    )


@app.get("/api/fuel", response_model=list[FuelEntryRead])
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


@app.post("/api/fuel", response_model=FuelEntryRead, status_code=201)
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
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
            "trips": trips[:10],
            "fuel_entries": fuel_entries,
            "total_trips": len(trips),
            "total_km": total_km,
            "total_fuel_cost": total_fuel_cost,
            "chart_labels": chart_labels,
            "chart_costs": chart_costs,
        },
    )
