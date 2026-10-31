"""The geocoder is tested against httpx.MockTransport: no network, no real service."""

import httpx
import pytest

from camperlog.services import geocoding
from camperlog.services.geocoding import (
    GeocodingUnavailable,
    NominatimGeocoder,
    Place,
)

MERAN = {
    "lat": "46.6697",
    "lon": "11.1594",
    "name": "Meran",
    "display_name": "Meran, Südtirol, Italien",
    "address": {"state": "Südtirol", "country": "Italien"},
}


class Clock:
    """A clock the test controls, and a sleep that only moves it."""

    def __init__(self):
        self.now = 1000.0
        self.slept: list[float] = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def make(handler, clock=None):
    clock = clock or Clock()
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return NominatimGeocoder(client, clock=clock, sleep=clock.sleep), clock


def answering(items, requests=None):
    def handler(request):
        if requests is not None:
            requests.append(request)
        return httpx.Response(200, json=items)

    return handler


def test_returns_the_matches_with_a_label():
    geocoder, _ = make(answering([MERAN]))

    [place] = geocoder.search("Meran")

    assert place == Place("Meran", "Südtirol", "Italien", 46.6697, 11.1594)
    assert place.label == "Meran, Südtirol, Italien"


def test_label_leaves_out_missing_parts():
    assert Place("Irgendwo", None, "Italien", 1.0, 2.0).label == "Irgendwo, Italien"
    assert Place("Irgendwo", None, None, 1.0, 2.0).label == "Irgendwo"


def test_request_identifies_the_app_and_asks_politely():
    requests = []
    geocoder, _ = make(answering([MERAN], requests))

    geocoder.search("  Meran  ")

    [request] = requests
    assert request.url.host == "nominatim.openstreetmap.org"
    assert request.headers["user-agent"].startswith("CamperLog/")
    assert "github.com/axieccolo1110/camperlog" in request.headers["user-agent"]
    params = request.url.params
    assert params["q"] == "meran"
    assert params["format"] == "jsonv2"
    assert params["limit"] == "5"
    assert params["accept-language"].startswith("de")


def test_no_match_is_an_empty_list_not_an_error():
    geocoder, _ = make(answering([]))

    assert geocoder.search("Gibtsnicht") == []


def test_duplicates_are_merged_and_the_list_is_limited():
    items = [MERAN, {**MERAN, "lat": "46.7"}]  # the same place twice
    items += [
        {**MERAN, "name": f"Meran {i}", "display_name": f"Meran {i}"} for i in range(8)
    ]
    geocoder, _ = make(answering(items))

    places = geocoder.search("Meran")

    assert len(places) == 5
    assert [p.name for p in places].count("Meran") == 1


def test_items_without_usable_data_are_skipped():
    items = [{"lat": "x", "lon": "1", "display_name": "Kaputt"}, {"foo": 1}, 7, MERAN]
    geocoder, _ = make(answering(items))

    assert [p.name for p in geocoder.search("Meran")] == ["Meran"]


def test_out_of_range_coordinates_are_skipped():
    geocoder, _ = make(answering([{**MERAN, "lat": "95"}]))

    assert geocoder.search("Meran") == []


def test_name_falls_back_to_the_first_part_of_display_name():
    item = {"lat": "1", "lon": "2", "display_name": "Dorf, Landkreis, Land"}
    geocoder, _ = make(answering([item]))

    assert geocoder.search("Dorf")[0].name == "Dorf"


@pytest.mark.parametrize("query", ["", " ", "a", " a "])
def test_too_short_queries_do_not_reach_the_service(query):
    requests = []
    geocoder, _ = make(answering([MERAN], requests))

    assert geocoder.search(query) == []
    assert requests == []


def test_same_query_is_answered_from_the_cache():
    requests = []
    geocoder, _ = make(answering([MERAN], requests))

    geocoder.search("Meran")
    geocoder.search("  MERAN ")

    assert len(requests) == 1


def test_cache_expires():
    requests = []
    geocoder, clock = make(answering([MERAN], requests))

    geocoder.search("Meran")
    clock.now += geocoding.CACHE_TTL + 1
    geocoder.search("Meran")

    assert len(requests) == 2


def test_cache_is_bounded(monkeypatch):
    monkeypatch.setattr(geocoding, "CACHE_SIZE", 2)
    requests = []
    geocoder, _ = make(answering([MERAN], requests))

    for query in ["aa", "bb", "cc"]:
        geocoder.search(query)
    geocoder.search("aa")  # was evicted, asks again

    assert len(requests) == 4


def test_at_most_one_request_per_second():
    geocoder, clock = make(answering([MERAN]))

    geocoder.search("Meran")
    clock.now += 0.3
    geocoder.search("Bozen")
    clock.now += 5
    geocoder.search("Brixen")

    assert clock.slept == [pytest.approx(0.7)]


def test_cached_answers_do_not_count_against_the_rate_limit():
    geocoder, clock = make(answering([MERAN]))

    geocoder.search("Meran")
    geocoder.search("Meran")
    geocoder.search("Meran")

    assert clock.slept == []


@pytest.mark.parametrize(
    "handler",
    [
        lambda request: httpx.Response(503),
        lambda request: httpx.Response(429),
        lambda request: httpx.Response(200, text="<html>not json</html>"),
        lambda request: httpx.Response(200, json={"error": "x"}),
        lambda request: (_ for _ in ()).throw(httpx.ConnectTimeout("slow")),
        lambda request: (_ for _ in ()).throw(httpx.ConnectError("down")),
    ],
)
def test_failures_become_geocoding_unavailable(handler):
    geocoder, _ = make(handler)

    with pytest.raises(GeocodingUnavailable):
        geocoder.search("Meran")


def test_failures_are_not_cached():
    answers = iter([httpx.Response(503), httpx.Response(200, json=[MERAN])])
    geocoder, _ = make(lambda request: next(answers))

    with pytest.raises(GeocodingUnavailable):
        geocoder.search("Meran")

    assert [p.name for p in geocoder.search("Meran")] == ["Meran"]


def test_the_shared_geocoder_is_one_instance():
    assert geocoding.get_geocoder() is geocoding.get_geocoder()
