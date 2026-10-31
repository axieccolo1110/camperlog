"""Look up coordinates for a place name (OpenStreetMap Nominatim, ADR 0006).

The lookup is a convenience: every failure ends in ``GeocodingUnavailable`` or an
empty result, never in anything that could block the caller.

Rules of the Nominatim usage policy that this module keeps (as far as known when it
was written, check https://operations.osmfoundation.org/policies/nominatim/ when
changing it): an identifying User-Agent, at most one request per second, cached
results, no search while typing (the caller searches once per finished input).
"""

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import Protocol

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "CamperLog/0.1 (+https://github.com/axieccolo1110/camperlog)"
MIN_INTERVAL = 1.0  # seconds between two requests to the service
TIMEOUT = 3.0  # seconds before a lookup is given up
MAX_RESULTS = 5
MIN_QUERY_LENGTH = 2
CACHE_SIZE = 256
CACHE_TTL = 24 * 60 * 60  # seconds


@dataclass(frozen=True)
class Place:
    name: str
    region: str | None
    country: str | None
    lat: float
    lon: float

    @property
    def label(self) -> str:
        """For choosing between matches, e.g. "Meran, Südtirol, Italien"."""
        return ", ".join(
            part for part in (self.name, self.region, self.country) if part
        )


class GeocodingUnavailable(RuntimeError):
    """The service did not answer in time or answered with something unusable."""


class Geocoder(Protocol):
    def search(self, query: str) -> list[Place]:
        ...


def _parse(items: object) -> list[Place]:
    """Turn the answer of Nominatim into places (without duplicates)."""
    if not isinstance(items, list):
        raise GeocodingUnavailable("Unerwartete Antwort der Ortssuche.")
    places: list[Place] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        try:
            lat, lon = float(item["lat"]), float(item["lon"])
            address = item.get("address") or {}
            name = (item.get("name") or item["display_name"].split(",")[0]).strip()
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if not name or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            continue
        region = address.get("state") or address.get("region") or address.get("county")
        country = address.get("country")
        key = (name.casefold(), (region or "").casefold(), (country or "").casefold())
        if key in seen:
            continue
        seen.add(key)
        places.append(Place(name, region, country, lat, lon))
    return places[:MAX_RESULTS]


class NominatimGeocoder:
    """Asks OpenStreetMap Nominatim. One instance is shared by the whole process,
    so the cache and the rate limit apply to all requests."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client or httpx.Client(timeout=TIMEOUT)
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last_request: float | None = None
        self._cache: OrderedDict[str, tuple[float, list[Place]]] = OrderedDict()

    def search(self, query: str) -> list[Place]:
        """Up to five matches for a place name, best first. Empty if none."""
        key = " ".join(query.split()).casefold()
        if len(key) < MIN_QUERY_LENGTH:
            return []
        with self._lock:
            cached = self._cache.get(key)
            if cached and self._clock() - cached[0] < CACHE_TTL:
                self._cache.move_to_end(key)
                return list(cached[1])
            places = self._request(key)
            self._cache[key] = (self._clock(), places)
            while len(self._cache) > CACHE_SIZE:
                self._cache.popitem(last=False)
            return list(places)

    def _request(self, query: str) -> list[Place]:
        if self._last_request is not None:
            wait = MIN_INTERVAL - (self._clock() - self._last_request)
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()
        try:
            response = self._client.get(
                NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": MAX_RESULTS,
                    "addressdetails": 1,
                    "accept-language": "de,en",
                },
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            return _parse(response.json())
        except (httpx.HTTPError, ValueError) as e:
            raise GeocodingUnavailable(str(e)) from e


@cache
def get_geocoder() -> Geocoder:
    """The shared geocoder (a FastAPI dependency, tests replace it with a fake)."""
    return NominatimGeocoder()
