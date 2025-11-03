"""Shared fixtures for integration tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Add src to path so we can import backend modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend import database, session


@pytest.fixture
def temp_db(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provide a temporary database for each test.

    This fixture:
    - Creates a temporary database file
    - Sets it as the active database path
    - Initializes the database schema
    - Cleans up after the test
    """
    db_file = tmp_path / "test.db"
    original_path = database.set_db_path(db_file)

    # Initialize the database schema
    database.init_db()
    database.init_uploaded_files_table()

    yield db_file

    # Restore original database path
    database.set_db_path(original_path)

    # Clean up the test database
    if db_file.exists():
        db_file.unlink()


@pytest.fixture
def temp_session_file(tmp_path: Path, monkeypatch) -> Generator[Path, None, None]:
    """
    Provide a temporary session file for each test.

    This fixture:
    - Creates a temporary session file location
    - Monkeypatches the SESSION_FILE constant
    - Ensures clean session state
    - Cleans up after the test
    """
    session_file = tmp_path / "test-session.json"

    # Monkeypatch the SESSION_FILE constant in the session module
    monkeypatch.setattr(session, "SESSION_FILE", session_file)

    yield session_file

    # Clean up session file
    if session_file.exists():
        session_file.unlink()


@pytest.fixture
def cleanup_session(temp_session_file: Path) -> Generator[None, None, None]:
    """
    Ensure session is cleared before and after each test.
    """
    # Clear any existing session before test
    session.clear_session()

    yield

    # Clear session after test
    session.clear_session()


@pytest.fixture
def isolated_test_env(temp_db: Path, temp_session_file: Path, cleanup_session) -> Generator[None, None, None]:
    """
    Combined fixture that provides a completely isolated test environment.

    This fixture combines:
    - Temporary database
    - Temporary session file
    - Session cleanup

    Use this for most integration tests to ensure complete isolation.
    """
    yield


@pytest.fixture
def mock_users(temp_db: Path) -> dict[str, str]:
    """
    Create a set of test users in the database.

    Returns:
        Dictionary mapping usernames to passwords for easy test access
    """
    users = {
        "alice": "password123",
        "bob": "securepass456",
        "carol": "testpass789",
        "dave": "davepass000",
        "eve": "evepass111",
        "frank": "frankpass222",
        "grace": "gracepass333",
        "henry": "henrypass444",
    }

    for username, password in users.items():
        database.create_user(username, password)

    return users


@pytest.fixture
def test_directory(tmp_path: Path) -> Path:
    """
    Create a test directory with some project indicators for traversal tests.

    Returns:
        Path to the test directory
    """
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()

    # Add some project indicators
    (test_dir / ".git").mkdir()
    (test_dir / "README.md").write_text("# Test Project\n")
    (test_dir / "src").mkdir()
    (test_dir / "src" / "main.py").write_text("print('Hello')")

    return test_dir
