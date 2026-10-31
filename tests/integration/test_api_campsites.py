import pytest

CAMPSITE = {"name": "Wiese am See", "lat": 46.668, "lon": 11.159}


def test_list_campsites_empty(api_client):
    r = api_client.get("/api/campsites")
    assert r.status_code == 200
    assert r.json() == []


def test_create_campsite_with_defaults(api_client):
    r = api_client.post("/api/campsites", json=CAMPSITE)

    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Wiese am See"
    assert (body["lat"], body["lon"]) == (46.668, 11.159)
    assert body["status"] == "bookmarked"
    assert body["playground"] is False and body["pets_allowed"] is False
    assert body["notes"] is None and body["external_url"] is None


def test_create_campsite_with_everything(api_client):
    r = api_client.post(
        "/api/campsites",
        json={
            **CAMPSITE,
            "status": "visited",
            "notes": "Ruhig",
            "playground": True,
            "pets_allowed": True,
            "external_url": "https://park4night.com/place/1",
        },
    )

    assert r.status_code == 201
    assert r.json()["status"] == "visited"
    assert r.json()["external_url"] == "https://park4night.com/place/1"
    assert api_client.get("/api/campsites").json()[0]["notes"] == "Ruhig"


@pytest.mark.parametrize(
    "change",
    [
        {"name": ""},
        {"name": "   "},
        {"lat": 91},
        {"lon": -181},
        {"status": "planned"},
        {"external_url": "javascript:alert(1)"},
        {"external_url": "park4night.com"},
    ],
)
def test_create_campsite_rejects_invalid_input(api_client, change):
    r = api_client.post("/api/campsites", json={**CAMPSITE, **change})

    assert r.status_code == 422
    assert api_client.get("/api/campsites").json() == []


@pytest.mark.parametrize("missing", ["name", "lat", "lon"])
def test_create_campsite_needs_name_and_coordinates(api_client, missing):
    payload = {k: v for k, v in CAMPSITE.items() if k != missing}

    assert api_client.post("/api/campsites", json=payload).status_code == 422


def test_campsite_routes_need_a_login(anon_client):
    assert anon_client.get("/api/campsites").status_code == 401
    assert anon_client.post("/api/campsites", json=CAMPSITE).status_code == 401
    r = anon_client.get("/campsites")
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_campsites_page_lists_campsites_in_german(api_client):
    api_client.post(
        "/api/campsites",
        json={
            **CAMPSITE,
            "status": "visited",
            "notes": "Ruhig",
            "playground": True,
            "external_url": "https://park4night.com/place/1",
        },
    )

    html = api_client.get("/campsites").text

    assert "Wiese am See" in html
    assert "besucht" in html
    assert "46.668, 11.159" in html
    assert 'href="https://park4night.com/place/1"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "Ruhig" in html
    assert 'id="campsite-form"' in html


def test_campsites_page_escapes_user_text(api_client):
    api_client.post(
        "/api/campsites",
        json={**CAMPSITE, "name": "<script>alert(1)</script>", "notes": "<b>x</b>"},
    )

    html = api_client.get("/campsites").text

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>x</b>" not in html


def test_campsites_page_empty_state(api_client):
    assert "Noch keine Stellplätze" in api_client.get("/campsites").text


def test_navigation_links_to_the_campsites(api_client):
    html = api_client.get("/").text

    assert 'href="/campsites"' in html


# --- stops tied to a campsite -------------------------------------------------

import datetime as dt  # noqa: E402


def _day(offset: int) -> str:
    return (dt.date.today() + dt.timedelta(days=offset)).isoformat()


@pytest.fixture
def trip_and_campsite(api_client):
    trip_id = api_client.post(
        "/api/trips", json={"start_date": _day(-30), "end_date": _day(30)}
    ).json()["id"]
    campsite_id = api_client.post("/api/campsites", json=CAMPSITE).json()["id"]
    return trip_id, campsite_id


def test_create_stop_with_a_campsite(api_client, trip_and_campsite):
    trip_id, campsite_id = trip_and_campsite

    r = api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "campsite_id": campsite_id},
    )

    assert r.status_code == 201
    body = r.json()
    assert body["campsite_id"] == campsite_id
    assert (body["place_name"], body["lat"], body["lon"]) == (None, None, None)
    assert body["effective_place_name"] == "Wiese am See"
    assert (body["effective_lat"], body["effective_lon"]) == (46.668, 11.159)


def test_free_standing_stop_has_its_own_effective_place(api_client, trip_and_campsite):
    trip_id, _ = trip_and_campsite

    body = api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "place_name": "Verona", "lat": 45.4, "lon": 10.9},
    ).json()

    assert body["campsite_id"] is None
    assert body["effective_place_name"] == "Verona"
    assert (body["effective_lat"], body["effective_lon"]) == (45.4, 10.9)


def test_campsite_and_own_place_are_rejected(api_client, trip_and_campsite):
    trip_id, campsite_id = trip_and_campsite

    r = api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "campsite_id": campsite_id, "place_name": "Verona"},
    )

    assert r.status_code == 422
    assert "übernimmt dessen Ort" in r.json()["detail"]
    assert api_client.get(f"/api/trips/{trip_id}").json()["stops"] == []


def test_unknown_campsite_is_404(api_client, trip_and_campsite):
    trip_id, _ = trip_and_campsite

    r = api_client.post(
        f"/api/trips/{trip_id}/stops", json={"date": _day(-5), "campsite_id": 999}
    )

    assert r.status_code == 404


def test_trip_detail_shows_the_campsite_place(api_client, trip_and_campsite):
    trip_id, campsite_id = trip_and_campsite
    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "campsite_id": campsite_id},
    )

    [stop] = api_client.get(f"/api/trips/{trip_id}").json()["stops"]

    assert stop["effective_place_name"] == "Wiese am See"


def test_update_stop_ties_to_a_campsite_and_back(api_client, trip_and_campsite):
    trip_id, campsite_id = trip_and_campsite
    stop_id = api_client.post(
        f"/api/trips/{trip_id}/stops", json={"date": _day(-5), "place_name": "Verona"}
    ).json()["id"]

    tied = api_client.put(
        f"/api/stops/{stop_id}", json={"date": _day(-5), "campsite_id": campsite_id}
    )
    assert tied.json()["effective_place_name"] == "Wiese am See"

    freed = api_client.put(
        f"/api/stops/{stop_id}", json={"date": _day(-5), "place_name": "Rimini"}
    )
    assert freed.json()["campsite_id"] is None
    assert freed.json()["effective_place_name"] == "Rimini"


def test_effective_status_in_the_campsite_list(api_client, trip_and_campsite):
    """Bookmarked, a future stop changes nothing, a past stop makes it visited."""
    trip_id, campsite_id = trip_and_campsite

    def status():
        [c] = api_client.get("/api/campsites").json()
        return c["status"], c["effective_status"]

    assert status() == ("bookmarked", "bookmarked")

    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(10), "campsite_id": campsite_id},
    )
    assert status() == ("bookmarked", "bookmarked")

    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "campsite_id": campsite_id},
    )
    assert status() == ("bookmarked", "visited")  # the manual status stays as it was


def test_created_campsite_reports_its_effective_status(api_client):
    r = api_client.post("/api/campsites", json={**CAMPSITE, "status": "visited"})

    assert r.json()["effective_status"] == "visited"


def test_campsites_page_shows_the_effective_status(api_client, trip_and_campsite):
    trip_id, campsite_id = trip_and_campsite
    bookmarked = '<td data-label="Status">vorgemerkt</td>'
    visited = '<td data-label="Status">besucht</td>'
    before = api_client.get("/campsites").text
    assert bookmarked in before and visited not in before

    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "campsite_id": campsite_id},
    )

    after = api_client.get("/campsites").text
    assert visited in after and bookmarked not in after


def test_trip_page_offers_the_campsites_and_marks_stops_tied_to_one(
    api_client, trip_and_campsite
):
    trip_id, campsite_id = trip_and_campsite
    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": _day(-5), "campsite_id": campsite_id},
    )

    html = api_client.get(f"/trips/{trip_id}").text

    assert 'id="stop-campsite"' in html and 'id="edit-campsite"' in html
    assert f'<option value="{campsite_id}">Wiese am See</option>' in html
    assert 'class="badge">Stellplatz</span>' in html
    assert f'data-campsite-id="{campsite_id}"' in html
    assert "46.668, 11.159" in html
    assert "campsite_id: addCampsite.campsiteId()" in html
