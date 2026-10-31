import pytest

ENTRY = {
    "date": "2026-08-01",
    "liters": 45.5,
    "price_per_liter": 1.879,
    "odometer": 12500,
}


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


@pytest.mark.parametrize(
    "field, value",
    [
        ("liters", 0),
        ("liters", -10),
        ("price_per_liter", 0),
        ("price_per_liter", -1.5),
        ("odometer", -1),
    ],
)
def test_create_fuel_entry_rejects_invalid_numbers(api_client, field, value):
    r = api_client.post("/api/fuel", json={**ENTRY, field: value})
    assert r.status_code == 422
    assert api_client.get("/api/fuel").json() == []


def test_create_fuel_entry_accepts_zero_odometer(api_client):
    r = api_client.post("/api/fuel", json={**ENTRY, "odometer": 0})
    assert r.status_code == 201


def test_list_fuel_after_create(api_client):
    api_client.post("/api/fuel", json=ENTRY)
    r = api_client.get("/api/fuel")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["odometer"] == 12500


def test_dashboard_shows_fuel_consumption(api_client):
    api_client.post(
        "/api/fuel", json={**ENTRY, "date": "2026-07-01", "odometer": 10000}
    )
    api_client.post(
        "/api/fuel",
        json={**ENTRY, "date": "2026-07-15", "odometer": 10500, "liters": 45.0},
    )
    api_client.post(
        "/api/fuel",
        json={**ENTRY, "date": "2026-07-26", "odometer": 11000, "liters": 48.0},
    )

    r = api_client.get("/")

    assert r.status_code == 200
    assert "L/100km" in r.text
    # 2026-07-26: 48L seit 10500km -> 9.6, 2026-07-15: 45L seit 10000km -> 9.0
    assert "9.6" in r.text
    assert "9.0" in r.text
