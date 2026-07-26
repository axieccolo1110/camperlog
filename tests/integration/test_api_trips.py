TRIP = {"origin": "München", "destination": "Berlin", "km": 600, "date": "2026-08-01"}


def test_list_trips_empty(api_client):
    r = api_client.get("/api/trips")
    assert r.status_code == 200
    assert r.json() == []


def test_create_trip(api_client):
    r = api_client.post("/api/trips", json=TRIP)
    assert r.status_code == 201
    body = r.json()
    assert body["origin"] == "München"
    assert body["destination"] == "Berlin"
    assert body["km"] == 600
    assert body["date"] == "2026-08-01"
    assert "id" in body


def test_create_trip_invalid_date(api_client):
    r = api_client.post("/api/trips", json={**TRIP, "date": "not-a-date"})
    assert r.status_code == 422


def test_list_trips_after_create(api_client):
    api_client.post("/api/trips", json=TRIP)
    r = api_client.get("/api/trips")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["origin"] == "München"


def test_dashboard_loads(api_client):
    r = api_client.get("/")
    assert r.status_code == 200
    assert "CamperLog" in r.text
    assert "Dashboard" in r.text
