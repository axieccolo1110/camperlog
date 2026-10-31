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
