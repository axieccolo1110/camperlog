import pytest
import sqlite3
from pathlib import Path
from camperlog.database import DB_PATH, init_db

@pytest.fixture
def test_db(tmp_path):
    """Fixture: erstellt eine Test-Datenbank (nicht die echte!)"""
    test_db_path = tmp_path / "test_camperlog.db"
    
    # Monkey-patch: DB_PATH zeigt auf Test-DB statt echte
    import camperlog.database
    original_db_path = camperlog.database.DB_PATH
    camperlog.database.DB_PATH = test_db_path
    
    init_db()
    
    yield test_db_path
    
    # Cleanup
    camperlog.database.DB_PATH = original_db_path
