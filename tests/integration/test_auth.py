import pytest

from camperlog.web.app import create_app
from tests.integration.conftest import PASSWORD

API_ROUTES = ["/api/trips", "/api/fuel"]


def test_dashboard_without_login_redirects_to_login(anon_client):
    r = anon_client.get("/")
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


@pytest.mark.parametrize("path", API_ROUTES)
def test_api_get_without_login_is_401(anon_client, path):
    assert anon_client.get(path).status_code == 401


@pytest.mark.parametrize("path", API_ROUTES)
def test_api_post_without_login_is_401(anon_client, path):
    assert anon_client.post(path, json={}).status_code == 401


def test_health_is_open(anon_client):
    r = anon_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_page_is_open_and_responsive(anon_client):
    r = anon_client.get("/login")
    assert r.status_code == 200
    assert 'type="password"' in r.text
    assert 'name="viewport"' in r.text


def test_wrong_password_shows_error_and_sets_no_cookie(anon_client):
    r = anon_client.post("/login", data={"password": "falsch"})
    assert r.status_code == 401
    assert "Falsches Passwort" in r.text
    assert "set-cookie" not in r.headers
    assert len(anon_client.cookies) == 0
    # und es ist weiterhin alles gesperrt
    assert anon_client.get("/api/trips").status_code == 401


def test_empty_password_is_rejected(anon_client):
    r = anon_client.post("/login", data={"password": ""})
    assert r.status_code == 401
    assert "set-cookie" not in r.headers


def test_non_ascii_password_does_not_crash(anon_client):
    r = anon_client.post("/login", data={"password": "pässwörd-✓"})
    assert r.status_code == 401


def test_login_is_impossible_without_configured_password(anon_client, monkeypatch):
    monkeypatch.delenv("CAMPERLOG_PASSWORD")
    r = anon_client.post("/login", data={"password": ""})
    assert r.status_code == 401
    assert "set-cookie" not in r.headers


def test_correct_password_opens_dashboard(anon_client):
    r = anon_client.post("/login", data={"password": PASSWORD})
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    assert "session" in anon_client.cookies

    dashboard = anon_client.get("/")
    assert dashboard.status_code == 200
    assert "Dashboard" in dashboard.text
    assert 'action="/logout"' in dashboard.text
    assert anon_client.get("/api/trips").status_code == 200


def test_login_page_redirects_when_already_logged_in(api_client):
    api_client.follow_redirects = False
    r = api_client.get("/login")
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_logout_locks_everything_again(api_client):
    api_client.follow_redirects = False
    assert api_client.get("/").status_code == 200

    r = api_client.post("/logout")
    assert r.status_code == 303
    assert r.headers["location"] == "/login"

    assert api_client.get("/").status_code == 303
    assert api_client.get("/api/trips").status_code == 401
    assert api_client.post("/api/fuel", json={}).status_code == 401


def test_tampered_cookie_is_not_accepted(anon_client):
    anon_client.cookies.set("session", "eyJsb2dnZWRfaW4iOiB0cnVlfQ==.abc.def")
    assert anon_client.get("/api/trips").status_code == 401


def test_cookie_signed_with_other_secret_is_rejected(anon_client, monkeypatch):
    anon_client.post("/login", data={"password": PASSWORD})
    cookie = anon_client.cookies["session"]

    monkeypatch.setenv("CAMPERLOG_SECRET_KEY", "ein-anderes-secret")
    from fastapi.testclient import TestClient

    with TestClient(create_app()) as other:
        other.cookies.set("session", cookie)
        assert other.get("/api/trips").status_code == 401


def test_session_cookie_is_secure_on_railway(web_env, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    with TestClient(create_app(), base_url="https://testserver") as client:
        r = client.post("/login", data={"password": PASSWORD}, follow_redirects=False)
    cookie = r.headers["set-cookie"].lower()
    assert "secure" in cookie
    assert "httponly" in cookie


def test_session_cookie_is_not_secure_locally(anon_client):
    r = anon_client.post("/login", data={"password": PASSWORD})
    cookie = r.headers["set-cookie"].lower()
    assert "secure" not in cookie
    assert "httponly" in cookie
