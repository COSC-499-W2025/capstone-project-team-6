# src/tests/backend_test/conftest.py
import sys
from pathlib import Path
import pytest

# .../src/tests/backend_test/conftest.py  -> parents[2] == .../src
SRC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC))

from backend import database


@pytest.fixture
def temp_db(tmp_path):
    """Set up a temporary database for testing."""
    db_file = tmp_path / "test.db"
    previous = database.set_db_path(db_file)
    database.reset_db()
    database.initialize()
    yield db_file
    database.set_db_path(previous)


@pytest.fixture
def test_user(temp_db):
    """Create a test user for integration tests."""
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    database.create_user(username, password)
    yield {"username": username, "password": password}
