import pytest
from camperlog.db import dispose_engines, upgrade_to_head


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Fixture: create a test database (not the real one!)"""
    test_db_path = tmp_path / "test_camperlog.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    upgrade_to_head()
    yield test_db_path
    dispose_engines()
