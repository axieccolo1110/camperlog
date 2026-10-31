"""What the map shows. The web turns these plain objects into GeoJSON."""

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from camperlog.models import Campsite
from camperlog.services.campsites import effective_statuses, list_campsites
from camperlog.services.trips import list_trips


@dataclass(frozen=True)
class StopPin:
    """A free-standing stop with coordinates."""

    stop_id: int
    trip_id: int
    date: dt.date
    place_name: str | None
    lat: float
    lon: float


@dataclass(frozen=True)
class Route:
    """The straight line through the places of one trip, in order.

    Not a calculated route: it connects the points as the crow flies (ADR 0001).
    """

    trip_id: int
    start_date: dt.date
    end_date: dt.date
    points: list[tuple[float, float]]  # (lat, lon)


@dataclass(frozen=True)
class Retrospective:
    campsites: list[Campsite]  # visited
    stops: list[StopPin]
    routes: list[Route]


def retrospective(session: Session, today: dt.date | None = None) -> Retrospective:
    """Visited campsites, free-standing stops with coordinates and, per trip, the
    line through its places.

    - A stop without coordinates is left out, and the line simply goes on with the
      next stop that has some.
    - A stop tied to a campsite contributes the campsite's coordinates to the
      line. It gets no pin of its own: the campsite is the pin (once it counts as
      visited, see ``effective_statuses``).
    - A trip with fewer than two places has no line.
    """
    statuses = effective_statuses(session, today)
    campsites = [c for c in list_campsites(session) if statuses[c.id] == "visited"]
    stops: list[StopPin] = []
    routes: list[Route] = []
    for trip in sorted(list_trips(session), key=lambda t: (t.start_date, t.id)):
        points: list[tuple[float, float]] = []
        for stop in trip.stops:  # sorted by date, then position
            lat, lon = stop.effective_lat, stop.effective_lon
            if lat is None or lon is None:
                continue
            points.append((lat, lon))
            if stop.campsite_id is None:
                stops.append(
                    StopPin(stop.id, trip.id, stop.date, stop.place_name, lat, lon)
                )
        if len(points) >= 2:
            routes.append(Route(trip.id, trip.start_date, trip.end_date, points))
    return Retrospective(campsites, stops, routes)
