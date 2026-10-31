import pytest

TRIP = {"start_date": "2026-08-01", "end_date": "2026-08-22", "distance_km": 600}


def test_list_trips_empty(api_client):
    r = api_client.get("/api/trips")
    assert r.status_code == 200
    assert r.json() == []


def test_create_trip(api_client):
    r = api_client.post("/api/trips", json=TRIP)
    assert r.status_code == 201
    body = r.json()
    assert body["start_date"] == "2026-08-01"
    assert body["end_date"] == "2026-08-22"
    assert body["distance_km"] == 600
    assert body["stop_count"] == 0
    assert "id" in body


def test_create_trip_without_distance(api_client):
    r = api_client.post(
        "/api/trips", json={"start_date": "2026-08-01", "end_date": "2026-08-01"}
    )
    assert r.status_code == 201
    assert r.json()["distance_km"] is None


@pytest.mark.parametrize("field", ["start_date", "end_date"])
def test_create_trip_invalid_date(api_client, field):
    r = api_client.post("/api/trips", json={**TRIP, field: "not-a-date"})
    assert r.status_code == 422


def test_create_trip_rejects_end_before_start(api_client):
    r = api_client.post(
        "/api/trips",
        json={**TRIP, "start_date": "2026-08-22", "end_date": "2026-08-01"},
    )
    assert r.status_code == 422
    assert "Enddatum" in r.json()["detail"]
    assert api_client.get("/api/trips").json() == []


@pytest.mark.parametrize("km", [0, -5])
def test_create_trip_rejects_non_positive_distance(api_client, km):
    r = api_client.post("/api/trips", json={**TRIP, "distance_km": km})
    assert r.status_code == 422
    assert api_client.get("/api/trips").json() == []


def test_list_trips_after_create(api_client):
    api_client.post("/api/trips", json=TRIP)
    r = api_client.get("/api/trips")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["start_date"] == "2026-08-01"


def test_dashboard_loads(api_client):
    r = api_client.get("/")
    assert r.status_code == 200
    assert "CamperLog" in r.text
    assert "Dashboard" in r.text


def test_dashboard_shows_trip_period_and_distance(api_client):
    api_client.post("/api/trips", json=TRIP)
    r = api_client.get("/")
    assert r.status_code == 200
    assert "2026-08-01" in r.text and "2026-08-22" in r.text
    assert "600" in r.text


# --- stops -------------------------------------------------------------------


def _trip_id(api_client):
    return api_client.post("/api/trips", json=TRIP).json()["id"]


def test_create_stop(api_client):
    trip_id = _trip_id(api_client)

    r = api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": "2026-08-10", "place_name": "Verona", "lat": 45.4, "lon": 10.9},
    )

    assert r.status_code == 201
    body = r.json()
    assert body["trip_id"] == trip_id
    assert body["date"] == "2026-08-10"
    assert body["place_name"] == "Verona"
    assert (body["lat"], body["lon"]) == (45.4, 10.9)
    assert body["position"] == 1


def test_create_stop_with_date_only(api_client):
    trip_id = _trip_id(api_client)

    r = api_client.post(f"/api/trips/{trip_id}/stops", json={"date": "2026-08-10"})

    assert r.status_code == 201
    assert r.json()["place_name"] is None


def test_create_stop_outside_the_period_is_422(api_client):
    trip_id = _trip_id(api_client)

    r = api_client.post(f"/api/trips/{trip_id}/stops", json={"date": "2026-09-01"})

    assert r.status_code == 422
    assert "Zeitraum der Reise" in r.json()["detail"]
    assert api_client.get(f"/api/trips/{trip_id}").json()["stops"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {"date": "not-a-date"},
        {"date": "2026-08-10", "lat": 91, "lon": 10},
        {"date": "2026-08-10", "lat": 45, "lon": 181},
        {"date": "2026-08-10", "lat": 45},
    ],
)
def test_create_stop_rejects_invalid_input(api_client, payload):
    trip_id = _trip_id(api_client)

    r = api_client.post(f"/api/trips/{trip_id}/stops", json=payload)

    assert r.status_code == 422


def test_create_stop_for_unknown_trip_is_404(api_client):
    r = api_client.post("/api/trips/999/stops", json={"date": "2026-08-10"})

    assert r.status_code == 404


def test_trip_detail_lists_stops_in_date_order(api_client):
    trip_id = _trip_id(api_client)
    for day in ("2026-08-20", "2026-08-02"):
        api_client.post(f"/api/trips/{trip_id}/stops", json={"date": day})

    body = api_client.get(f"/api/trips/{trip_id}").json()

    assert [s["date"] for s in body["stops"]] == ["2026-08-02", "2026-08-20"]
    assert body["stop_count"] == 2


def test_trip_detail_unknown_trip_is_404(api_client):
    assert api_client.get("/api/trips/999").status_code == 404


def test_stop_routes_need_a_login(anon_client):
    assert anon_client.get("/api/trips/1").status_code == 401
    r = anon_client.post("/api/trips/1/stops", json={"date": "2026-08-10"})
    assert r.status_code == 401


def test_trip_page_shows_stops_and_the_form(api_client):
    trip_id = _trip_id(api_client)
    api_client.post(
        f"/api/trips/{trip_id}/stops",
        json={"date": "2026-08-10", "place_name": "Verona", "lat": 45.4, "lon": 10.9},
    )

    r = api_client.get(f"/trips/{trip_id}")

    assert r.status_code == 200
    assert "Verona" in r.text
    assert "45.4, 10.9" in r.text
    assert 'id="stop-form"' in r.text
    assert 'min="2026-08-01"' in r.text and 'max="2026-08-22"' in r.text


def test_trip_page_unknown_trip_is_404(api_client):
    assert api_client.get("/trips/999").status_code == 404


def test_trip_page_needs_a_login(anon_client):
    r = anon_client.get("/trips/1")
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_dashboard_links_to_the_trip_page(api_client):
    trip_id = _trip_id(api_client)

    assert f'href="/trips/{trip_id}"' in api_client.get("/").text


def test_three_week_trip_with_six_stops_via_the_api(api_client):
    """Scenario from the issue: three weeks, six stops, two free-standing."""
    trip_id = api_client.post(
        "/api/trips",
        json={
            "start_date": "2026-08-01",
            "end_date": "2026-08-21",
            "distance_km": 2800,
        },
    ).json()["id"]
    stops = [
        ("2026-08-01", "München", 48.137, 11.575),
        ("2026-08-04", "Verona", 45.438, 10.992),
        ("2026-08-08", "Rimini", 44.06, 12.568),
        ("2026-08-12", None, None, None),  # free-standing, no place at all
        ("2026-08-16", "Nizza", 43.71, 7.262),
        ("2026-08-21", None, None, None),  # free-standing, no place at all
    ]
    for day, place, lat, lon in stops:
        r = api_client.post(
            f"/api/trips/{trip_id}/stops",
            json={"date": day, "place_name": place, "lat": lat, "lon": lon},
        )
        assert r.status_code == 201

    body = api_client.get(f"/api/trips/{trip_id}").json()

    assert body["stop_count"] == 6
    assert [s["date"] for s in body["stops"]] == [s[0] for s in stops]
    assert api_client.get("/api/trips").json()[0]["stop_count"] == 6


# --- editing and deleting ----------------------------------------------------


def _stop_id(api_client, trip_id, day="2026-08-10", place="Verona"):
    r = api_client.post(
        f"/api/trips/{trip_id}/stops", json={"date": day, "place_name": place}
    )
    return r.json()["id"]


def test_update_trip(api_client):
    trip_id = _trip_id(api_client)

    r = api_client.put(
        f"/api/trips/{trip_id}",
        json={"start_date": "2026-07-30", "end_date": "2026-09-01"},
    )

    assert r.status_code == 200
    assert r.json()["start_date"] == "2026-07-30"
    assert r.json()["distance_km"] is None
    assert api_client.get(f"/api/trips/{trip_id}").json()["end_date"] == "2026-09-01"


def test_update_trip_that_excludes_a_stop_is_422(api_client):
    trip_id = _trip_id(api_client)
    _stop_id(api_client, trip_id, "2026-08-20")

    r = api_client.put(
        f"/api/trips/{trip_id}",
        json={"start_date": "2026-08-01", "end_date": "2026-08-10"},
    )

    assert r.status_code == 422
    assert "2026-08-20" in r.json()["detail"]
    assert api_client.get(f"/api/trips/{trip_id}").json()["end_date"] == "2026-08-22"


@pytest.mark.parametrize(
    "payload",
    [
        {"start_date": "2026-08-22", "end_date": "2026-08-01"},
        {"start_date": "2026-08-01", "end_date": "2026-08-22", "distance_km": 0},
        {"start_date": "nope", "end_date": "2026-08-22"},
    ],
)
def test_update_trip_rejects_invalid_input(api_client, payload):
    trip_id = _trip_id(api_client)

    assert api_client.put(f"/api/trips/{trip_id}", json=payload).status_code == 422


def test_update_unknown_trip_is_404(api_client):
    r = api_client.put("/api/trips/999", json=TRIP)

    assert r.status_code == 404


def test_delete_trip_removes_its_stops(api_client):
    trip_id = _trip_id(api_client)
    _stop_id(api_client, trip_id)

    r = api_client.delete(f"/api/trips/{trip_id}")

    assert r.status_code == 204
    assert api_client.get(f"/api/trips/{trip_id}").status_code == 404
    assert api_client.get("/api/trips").json() == []


def test_delete_unknown_trip_is_404(api_client):
    assert api_client.delete("/api/trips/999").status_code == 404


def test_update_stop(api_client):
    trip_id = _trip_id(api_client)
    stop_id = _stop_id(api_client, trip_id)

    r = api_client.put(
        f"/api/stops/{stop_id}",
        json={"date": "2026-08-12", "place_name": "Rimini", "lat": 44.0, "lon": 12.5},
    )

    assert r.status_code == 200
    assert r.json()["place_name"] == "Rimini"
    stops = api_client.get(f"/api/trips/{trip_id}").json()["stops"]
    assert [(s["date"], s["place_name"]) for s in stops] == [("2026-08-12", "Rimini")]


def test_update_stop_outside_the_period_is_422(api_client):
    trip_id = _trip_id(api_client)
    stop_id = _stop_id(api_client, trip_id)

    r = api_client.put(f"/api/stops/{stop_id}", json={"date": "2026-09-30"})

    assert r.status_code == 422
    assert "Zeitraum der Reise" in r.json()["detail"]


def test_update_unknown_stop_is_404(api_client):
    r = api_client.put("/api/stops/999", json={"date": "2026-08-10"})

    assert r.status_code == 404


def test_delete_stop(api_client):
    trip_id = _trip_id(api_client)
    stop_id = _stop_id(api_client, trip_id)

    r = api_client.delete(f"/api/stops/{stop_id}")

    assert r.status_code == 204
    assert api_client.get(f"/api/trips/{trip_id}").json()["stops"] == []


def test_delete_unknown_stop_is_404(api_client):
    assert api_client.delete("/api/stops/999").status_code == 404


def test_edit_and_delete_routes_need_a_login(anon_client):
    assert anon_client.put("/api/trips/1", json=TRIP).status_code == 401
    assert anon_client.delete("/api/trips/1").status_code == 401
    assert (
        anon_client.put("/api/stops/1", json={"date": "2026-08-10"}).status_code == 401
    )
    assert anon_client.delete("/api/stops/1").status_code == 401


def test_trip_page_offers_edit_and_delete(api_client):
    trip_id = _trip_id(api_client)
    _stop_id(api_client, trip_id)

    html = api_client.get(f"/trips/{trip_id}").text

    assert 'id="trip-edit-form"' in html
    assert 'value="2026-08-01"' in html and 'value="2026-08-22"' in html
    assert 'id="delete-trip"' in html
    assert 'class="btn btn-secondary btn-small edit-stop"' in html
    assert 'class="btn btn-danger btn-small delete-stop"' in html
    assert 'data-place="Verona"' in html


def test_trip_page_keeps_adding_and_editing_stops_in_separate_forms(api_client):
    """Regression: one form that switched into edit mode overwrote the edited
    stop when the user meant to add a new one."""
    trip_id = _trip_id(api_client)
    _stop_id(api_client, trip_id)

    html = api_client.get(f"/trips/{trip_id}").text

    assert 'id="stop-form"' in html  # always there, only ever creates
    assert 'id="stop-edit-form"' in html  # only edits
    assert 'id="stop-edit-card" hidden' in html  # hidden until "Bearbeiten"
    assert "/api/trips/${TRIP_ID}/stops" in html  # the add form POSTs
    assert "/api/stops/${editingStopId}" in html  # the edit form PUTs
