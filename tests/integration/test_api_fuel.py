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


def _create(api_client, **changes):
    r = api_client.post("/api/fuel", json={**ENTRY, **changes})
    assert r.status_code == 201
    return r.json()["id"]


def test_replace_fuel_entry(api_client):
    entry_id = _create(api_client)

    r = api_client.put(
        f"/api/fuel/{entry_id}",
        json={**ENTRY, "liters": 50.0, "price_per_liter": 2.0, "odometer": 12600},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == entry_id
    assert body["liters"] == 50.0 and body["odometer"] == 12600
    assert body["total_cost"] == 100.0
    assert api_client.get("/api/fuel").json()[0]["total_cost"] == 100.0


def test_replace_fuel_entry_unknown_entry(api_client):
    assert api_client.put("/api/fuel/999", json=ENTRY).status_code == 404


def test_replace_fuel_entry_rejects_a_reading_out_of_order(api_client):
    _create(api_client, date="2026-07-01", odometer=10000)
    entry_id = _create(api_client, date="2026-07-15", odometer=10500)

    r = api_client.put(
        f"/api/fuel/{entry_id}", json={**ENTRY, "date": "2026-07-15", "odometer": 9000}
    )

    assert r.status_code == 422
    assert "vorherigen" in r.json()["detail"]


@pytest.mark.parametrize(
    "field, value", [("liters", 0), ("price_per_liter", -1), ("odometer", -1)]
)
def test_replace_fuel_entry_rejects_invalid_numbers(api_client, field, value):
    entry_id = _create(api_client)

    r = api_client.put(f"/api/fuel/{entry_id}", json={**ENTRY, field: value})

    assert r.status_code == 422


def test_delete_fuel_entry(api_client):
    entry_id = _create(api_client)

    assert api_client.delete(f"/api/fuel/{entry_id}").status_code == 204
    assert api_client.get("/api/fuel").json() == []


def test_delete_fuel_entry_unknown_entry(api_client):
    assert api_client.delete("/api/fuel/999").status_code == 404


def test_fuel_edit_and_delete_need_a_login(anon_client):
    assert anon_client.put("/api/fuel/1", json=ENTRY).status_code == 401
    assert anon_client.delete("/api/fuel/1").status_code == 401


def test_tanken_page_offers_edit_and_delete_for_every_entry(api_client):
    entry_id = _create(api_client)

    r = api_client.get("/tanken")

    assert r.status_code == 200
    assert f'data-fuel-id="{entry_id}"' in r.text
    assert 'id="fuel-edit-form"' in r.text
    assert "/api/fuel/${" in r.text
