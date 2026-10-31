import pytest
from camperlog.database import init_db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Fixture: create a test database (not the real one!)"""
    test_db_path = tmp_path / "test_camperlog.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    init_db()
    yield test_db_path
