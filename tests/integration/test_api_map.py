import datetime as dt

import pytest

CAMPSITE = {"name": "Wiese am See", "lat": 46.668, "lon": 11.159}


def _day(offset: int) -> str:
    return (dt.date.today() + dt.timedelta(days=offset)).isoformat()


def _features(api_client, **params):
    r = api_client.get("/api/map", params=params)
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    return body["features"]


def test_map_is_empty_without_campsites(api_client):
    assert _features(api_client) == []


def test_bookmarked_campsite_is_a_geojson_point_with_longitude_first(api_client):
    api_client.post(
        "/api/campsites",
        json={
            **CAMPSITE,
            "notes": "Ruhig",
            "playground": True,
            "external_url": "https://park4night.com/place/1",
        },
    )

    [feature] = _features(api_client)

    assert feature["type"] == "Feature"
    # GeoJSON order is [longitude, latitude], the reverse of how people say it
    assert feature["geometry"] == {"type": "Point", "coordinates": [11.159, 46.668]}
    props = feature["properties"]
    assert props["name"] == "Wiese am See"
    assert props["status"] == "bookmarked"
    assert props["status_label"] == "vorgemerkt"
    assert props["notes"] == "Ruhig"
    assert props["playground"] is True and props["pets_allowed"] is False
    assert props["external_url"] == "https://park4night.com/place/1"
    assert isinstance(props["id"], int)


def test_bookmark_view_is_the_default(api_client):
    api_client.post("/api/campsites", json=CAMPSITE)

    assert _features(api_client) == _features(api_client, view="bookmarks")


def test_only_bookmarked_campsites_are_on_the_map(api_client):
    api_client.post("/api/campsites", json={**CAMPSITE, "status": "visited"})
    api_client.post("/api/campsites", json={**CAMPSITE, "name": "Vorgemerkt"})

    names = [f["properties"]["name"] for f in _features(api_client)]

    assert names == ["Vorgemerkt"]


def test_a_campsite_leaves_the_bookmark_list_after_a_past_stop(api_client):
    """Bookmarked, then used as a stop: no longer on the bookmark list."""
    trip_id = api_client.post(
        "/api/trips", json={"start_date": _day(-30), "end_date": _day(30)}
    ).json()["id"]
    campsite_id = api_client.post("/api/campsites", json=CAMPSITE).json()["id"]

    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(10), "campsite_id": campsite_id},
    )
    assert len(_features(api_client)) == 1  # a future stop changes nothing

    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "campsite_id": campsite_id},
    )
    assert _features(api_client) == []


def test_features_are_sorted_by_name(api_client):
    for name in ["Zeltplatz", "Almwiese"]:
        api_client.post("/api/campsites", json={**CAMPSITE, "name": name})

    assert [f["properties"]["name"] for f in _features(api_client)] == [
        "Almwiese",
        "Zeltplatz",
    ]


def test_unknown_view_is_rejected(api_client):
    assert api_client.get("/api/map", params={"view": "nope"}).status_code == 422


def test_map_data_needs_a_login(anon_client):
    assert anon_client.get("/api/map").status_code == 401


def test_map_page_loads_leaflet_with_integrity_checks(api_client):
    html = api_client.get("/map").text

    assert 'id="map"' in html
    assert "unpkg.com/leaflet@1.9.4/dist/leaflet.js" in html
    assert "unpkg.com/leaflet@1.9.4/dist/leaflet.css" in html
    assert html.count('integrity="sha256-') == 2
    assert "tile.openstreetmap.org/{z}/{x}/{y}.png" in html
    assert "OpenStreetMap" in html and "openstreetmap.org/copyright" in html
    assert "/api/map?view=${view}" in html
    assert 'data-view="bookmarks"' in html and "Vormerkliste" in html
    assert 'data-view="retrospective"' in html and "Rückschau" in html


def test_map_page_does_not_build_popups_from_html_strings(api_client):
    """Place names and notes come from the user: they must be inserted as text."""
    html = api_client.get("/map").text

    assert "textContent = p.name" in html
    assert "innerHTML" not in html
    assert "bindPopup(popupContent(" in html


def test_map_page_needs_a_login(anon_client):
    r = anon_client.get("/map")

    assert r.status_code == 303 and r.headers["location"] == "/login"


@pytest.mark.parametrize("path", ["/", "/campsites", "/map"])
def test_navigation_links_to_the_map(api_client, path):
    assert 'href="/map"' in api_client.get(path).text


# --- retrospective -------------------------------------------------------------


def _by_kind(api_client, kind):
    r = api_client.get("/api/map", params={"view": "retrospective"})
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    return [f for f in body["features"] if f["properties"]["kind"] == kind]


@pytest.fixture
def journey(api_client):
    """A trip with a free-standing stop, a stop without coordinates and a stop at a
    visited campsite."""
    trip_id = api_client.post(
        "/api/trips", json={"start_date": "2026-08-01", "end_date": "2026-08-21"}
    ).json()["id"]
    campsite_id = api_client.post(
        "/api/campsites", json={**CAMPSITE, "status": "visited"}
    ).json()["id"]
    for payload in [
        {"date": "2026-08-02", "place_name": "Verona", "lat": 45.4, "lon": 10.9},
        {"date": "2026-08-05", "place_name": "Ohne Koordinaten"},
        {"date": "2026-08-09", "campsite_id": campsite_id},
    ]:
        assert (
            api_client.post(f"/api/trips/{trip_id}/stops", json=payload).status_code
            == 201
        )
    return trip_id


def test_retrospective_is_empty_without_data(api_client):
    r = api_client.get("/api/map", params={"view": "retrospective"})

    assert r.json() == {"type": "FeatureCollection", "features": []}


def test_retrospective_has_visited_campsites_stops_and_a_line(api_client, journey):
    r = api_client.get("/api/map", params={"view": "retrospective"})

    kinds = sorted(f["properties"]["kind"] for f in r.json()["features"])
    assert kinds == ["campsite", "route", "stop"]


def test_visited_campsite_pin(api_client, journey):
    [campsite] = _by_kind(api_client, "campsite")

    assert campsite["geometry"]["coordinates"] == [11.159, 46.668]
    assert campsite["properties"]["name"] == "Wiese am See"
    assert campsite["properties"]["status"] == "visited"


def test_free_standing_stop_pin(api_client, journey):
    [stop] = _by_kind(api_client, "stop")

    assert stop["geometry"] == {"type": "Point", "coordinates": [10.9, 45.4]}
    props = stop["properties"]
    assert (props["name"], props["date"], props["trip_id"]) == (
        "Verona",
        "2026-08-02",
        journey,
    )


def test_line_goes_through_the_places_in_order_skipping_the_unlocated_stop(
    api_client, journey
):
    [route] = _by_kind(api_client, "route")

    assert route["geometry"] == {
        "type": "LineString",
        # [lon, lat]: Verona first, then the campsite (the stop without coordinates
        # in between is skipped)
        "coordinates": [[10.9, 45.4], [11.159, 46.668]],
    }
    assert route["properties"]["trip_id"] == journey
    assert route["properties"]["label"] == "2026-08-01 – 2026-08-21"
    assert route["properties"]["places"] == 2


def test_bookmarked_campsites_are_not_in_the_retrospective(api_client):
    api_client.post("/api/campsites", json=CAMPSITE)

    assert _by_kind(api_client, "campsite") == []


def test_both_views_do_not_mix(api_client, journey):
    api_client.post("/api/campsites", json={**CAMPSITE, "name": "Nur vorgemerkt"})

    bookmarks = [f["properties"]["name"] for f in _features(api_client)]

    assert bookmarks == ["Nur vorgemerkt"]


def test_retrospective_needs_a_login(anon_client):
    r = anon_client.get("/api/map", params={"view": "retrospective"})

    assert r.status_code == 401


def test_map_page_can_switch_views_and_toggle_lines(api_client):
    html = api_client.get("/map").text

    assert "#rueckschau" in html and "#vormerkliste" in html
    assert 'id="route-toggles"' in html
    assert "Luftlinie" in html
    assert "zeigen keine Fahrstrecke" in html
    assert "innerHTML" not in html
