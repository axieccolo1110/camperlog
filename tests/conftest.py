import pytest
from camperlog.database import init_db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Fixture: erstellt eine Test-Datenbank (nicht die echte!)"""
    test_db_path = tmp_path / "test_camperlog.db"
    monkeypatch.setenv("CAMPERLOG_DB_PATH", str(test_db_path))
    init_db()
    yield test_db_path
