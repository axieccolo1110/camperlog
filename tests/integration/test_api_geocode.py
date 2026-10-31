import pytest

from camperlog.services.geocoding import GeocodingUnavailable, Place, get_geocoder

MERAN = Place("Meran", "Südtirol", "Italien", 46.6697, 11.1594)


class FakeGeocoder:
    """Stands in for Nominatim: the tests never use the network."""

    def __init__(self, places=(), fail=False):
        self.places, self.fail, self.queries = list(places), fail, []

    def search(self, query):
        self.queries.append(query)
        if self.fail:
            raise GeocodingUnavailable("down")
        return self.places


@pytest.fixture
def use_geocoder(api_client):
    def use(fake):
        api_client.app.dependency_overrides[get_geocoder] = lambda: fake
        return fake

    return use


def test_geocode_returns_matches(api_client, use_geocoder):
    fake = use_geocoder(FakeGeocoder([MERAN]))

    r = api_client.get("/api/geocode", params={"q": "Meran"})

    assert r.status_code == 200
    assert r.json() == {
        "results": [
            {
                "name": "Meran",
                "region": "Südtirol",
                "country": "Italien",
                "lat": 46.6697,
                "lon": 11.1594,
                "label": "Meran, Südtirol, Italien",
            }
        ],
        "unavailable": False,
    }
    assert fake.queries == ["Meran"]


def test_geocode_without_a_match(api_client, use_geocoder):
    use_geocoder(FakeGeocoder([]))

    r = api_client.get("/api/geocode", params={"q": "Gibtsnicht"})

    assert r.json() == {"results": [], "unavailable": False}


def test_geocode_reports_an_unreachable_service_without_failing(
    api_client, use_geocoder
):
    use_geocoder(FakeGeocoder(fail=True))

    r = api_client.get("/api/geocode", params={"q": "Meran"})

    assert r.status_code == 200
    assert r.json() == {"results": [], "unavailable": True}


def test_geocode_without_query_is_empty(api_client, use_geocoder):
    use_geocoder(FakeGeocoder([MERAN]))

    assert api_client.get("/api/geocode").status_code == 200


def test_geocode_rejects_an_overlong_query(api_client, use_geocoder):
    fake = use_geocoder(FakeGeocoder([MERAN]))

    r = api_client.get("/api/geocode", params={"q": "x" * 201})

    assert r.status_code == 422
    assert fake.queries == []


def test_geocode_needs_a_login(anon_client):
    assert anon_client.get("/api/geocode", params={"q": "Meran"}).status_code == 401


def test_trip_page_wires_the_lookup_into_both_forms(api_client):
    trip_id = api_client.post(
        "/api/trips", json={"start_date": "2026-08-01", "end_date": "2026-08-22"}
    ).json()["id"]

    html = api_client.get(f"/trips/{trip_id}").text

    assert "attachLookup('stop-place', 'stop-lat', 'stop-lon', 'stop-lookup')" in html
    assert "attachLookup('edit-place', 'edit-lat', 'edit-lon', 'edit-lookup')" in html
    assert 'id="stop-lookup"' in html and 'id="edit-lookup"' in html
    assert "/api/geocode?q=" in html
    assert "https://www.openstreetmap.org/copyright" in html
    assert "OpenStreetMap-Mitwirkende" in html


def test_campsites_page_wires_the_lookup_into_the_form(api_client):
    html = api_client.get("/campsites").text

    assert (
        "attachLookup('campsite-name', 'campsite-lat', 'campsite-lon', "
        "'campsite-lookup')" in html
    )
    assert 'id="campsite-lookup"' in html
    assert "/api/geocode?q=" in html
    assert "https://www.openstreetmap.org/copyright" in html
    assert "OpenStreetMap-Mitwirkende" in html
