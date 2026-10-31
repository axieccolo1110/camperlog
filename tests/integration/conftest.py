import pytest
from fastapi.testclient import TestClient

PASSWORD = "test-passwort"
SECRET_KEY = "test-secret-key"


@pytest.fixture
def web_env(tmp_path, monkeypatch):
    """Isolierte Umgebung für die Web-App: Test-DB, Passwort, Secret."""
    db_file = tmp_path / "test_api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("CAMPERLOG_PASSWORD", PASSWORD)
    monkeypatch.setenv("CAMPERLOG_SECRET_KEY", SECRET_KEY)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)


@pytest.fixture
def anon_client(web_env):
    """Client ohne Login."""
    from camperlog.web.app import create_app

    with TestClient(create_app(), follow_redirects=False) as client:
        yield client


@pytest.fixture
def api_client(anon_client):
    """Eingeloggter Client (Session-Cookie gesetzt)."""
    r = anon_client.post("/login", data={"password": PASSWORD})
    assert r.status_code == 303
    anon_client.follow_redirects = True
    return anon_client
