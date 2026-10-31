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
