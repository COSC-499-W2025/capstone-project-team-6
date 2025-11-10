# src/tests/backend_test/conftest.py
import json
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

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


@pytest.fixture(autouse=True)
def fake_session(tmp_path, monkeypatch):
    """Simulate a logged-in user for tests."""
    import json

    from backend import session

    session_path = tmp_path / ".mda-session.json"
    session_data = {"logged_in": True, "username": "testuser"}
    session_path.write_text(json.dumps(session_data))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(session, "SESSION_FILE", session_path)

    yield


@pytest.fixture(scope="session", autouse=True)
def setup_vector_db():
    """Create vector database tables before any tests run."""
    if not os.getenv("VECTOR_DB_URL"):  # skip if not testing vector DB
        yield
        return

    from backend.database_vector import Base, engine

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(engine)
    print("\n Vector database tables created")
    yield
