"""Campsites."""

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from camperlog.models import CAMPSITE_STATUSES, Campsite, Stop
from camperlog.services.errors import NotFoundError, ValidationError
from camperlog.services.validation import check_coordinate_ranges

MAX_URL_LENGTH = 2000


def _clean_url(url: str | None) -> str | None:
    """Only http(s) links are accepted: the link is rendered as an href."""
    url = (url or "").strip()
    if not url:
        return None
    if len(url) > MAX_URL_LENGTH or any(c.isspace() for c in url):
        raise ValidationError("Der Link ist ungültig.")
    if not url.lower().startswith(("http://", "https://")):
        raise ValidationError("Der Link muss mit http:// oder https:// beginnen.")
    return url


def add_campsite(
    session: Session,
    name: str,
    lat: float,
    lon: float,
    status: str = "bookmarked",
    notes: str | None = None,
    playground: bool = False,
    pets_allowed: bool = False,
    external_url: str | None = None,
) -> Campsite:
    """Create a campsite. Name and coordinates are required."""
    name = (name or "").strip()
    if not name:
        raise ValidationError("Der Name darf nicht leer sein.")
    check_coordinate_ranges(lat, lon)
    if status not in CAMPSITE_STATUSES:
        raise ValidationError("Der Status muss „besucht“ oder „vorgemerkt“ sein.")
    campsite = Campsite(
        name=name,
        lat=lat,
        lon=lon,
        status=status,
        notes=(notes or "").strip() or None,
        playground=playground,
        pets_allowed=pets_allowed,
        external_url=_clean_url(external_url),
    )
    session.add(campsite)
    session.commit()
    return campsite


def list_campsites(session: Session) -> list[Campsite]:
    """All campsites, sorted by name (case-insensitive)."""
    query = select(Campsite).order_by(func.lower(Campsite.name), Campsite.id)
    return list(session.scalars(query.execution_options(populate_existing=True)))


def get_campsite(session: Session, campsite_id: int) -> Campsite:
    """A campsite. Raises NotFoundError if it does not exist."""
    campsite = session.get(Campsite, campsite_id)
    if campsite is None:
        raise NotFoundError(f"Stellplatz {campsite_id} gibt es nicht.")
    return campsite


def effective_statuses(
    session: Session, today: dt.date | None = None
) -> dict[int, str]:
    """The status of every campsite (by id), computed on read.

    A campsite is "visited" if its manual status is "visited" **or** a stop dated
    today or earlier references it. A stop planned in the future changes nothing,
    and the campsite becomes "visited" by itself once that day has come. (Setting
    the status when saving would leave it "bookmarked" after the trip.)
    """
    today = today or dt.date.today()
    visited_by_stops = set(
        session.scalars(
            select(Stop.campsite_id)
            .where(Stop.campsite_id.is_not(None), Stop.date <= today)
            .distinct()
        )
    )
    return {
        c.id: "visited"
        if c.status == "visited" or c.id in visited_by_stops
        else c.status
        for c in list_campsites(session)
    }


def list_bookmarked_campsites(
    session: Session, today: dt.date | None = None
) -> list[Campsite]:
    """The campsites that are still only bookmarked (the effective status counts:
    one that a stop dated today or earlier references is visited already)."""
    statuses = effective_statuses(session, today)
    return [c for c in list_campsites(session) if statuses[c.id] == "bookmarked"]
