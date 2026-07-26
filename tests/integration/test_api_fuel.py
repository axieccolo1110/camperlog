ENTRY = {"date": "2026-08-01", "liters": 45.5, "price_per_liter": 1.879, "odometer": 12500}


def test_list_fuel_empty(api_client):
    r = api_client.get("/api/fuel")
    assert r.status_code == 200
    assert r.json() == []


def test_create_fuel_entry(api_client):
    r = api_client.post("/api/fuel", json=ENTRY)
    assert r.status_code == 201
    body = r.json()
    assert body["liters"] == 45.5
    assert body["odometer"] == 12500
    assert "total_cost" in body
    assert round(body["total_cost"], 2) == round(45.5 * 1.879, 2)
    assert "id" in body


def test_create_fuel_entry_invalid_date(api_client):
    r = api_client.post("/api/fuel", json={**ENTRY, "date": "01.08.2026"})
    assert r.status_code == 422


def test_list_fuel_after_create(api_client):
    api_client.post("/api/fuel", json=ENTRY)
    r = api_client.get("/api/fuel")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["odometer"] == 12500
