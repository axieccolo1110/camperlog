import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    db_file = tmp_path / "test_api.db"
    monkeypatch.setenv("CAMPERLOG_DB_PATH", str(db_file))

    from camperlog.database import init_db
    from camperlog.web.api import app

    init_db()

    with TestClient(app) as client:
        yield client
