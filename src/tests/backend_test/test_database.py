"""Tests for SQLite database helper module."""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from src.backend import database


@pytest.fixture
def temp_db_path(tmp_path):
    db_file = tmp_path / "auth_test.db"
    previous = database.set_db_path(db_file)
    database.reset_db()
    yield db_file
    database.set_db_path(previous)


def test_initialize_creates_users_table(temp_db_path):
    with database.get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        assert cursor.fetchone() is not None


def test_create_user_inserts_record(temp_db_path):
    new_id = database.create_user("alice", "secret")
    assert isinstance(new_id, int)

    user = database.get_user("alice")
    assert user is not None
    assert user["username"] == "alice"
    assert user["password_hash"] != "secret"


def test_duplicate_username_raises(temp_db_path):
    database.create_user("bob", "secret1")
    with pytest.raises(database.UserAlreadyExistsError):
        database.create_user("bob", "secret2")


def test_authenticate_user(temp_db_path):
    database.create_user("carol", "mypassword")

    assert database.authenticate_user("carol", "mypassword") is True
    assert database.authenticate_user("carol", "wrong") is False
    assert database.authenticate_user("unknown", "mypassword") is False


def test_uploaded_files_table_created(temp_db_path):
    """Ensure uploaded_files table exists."""
    with database.get_connection() as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_files';")
        assert cur.fetchone() is not None


def test_save_uploaded_file_inserts_record(temp_db_path):
    """Verify that file and extracted text are inserted correctly."""
    file_name = "example.png"
    text = "Detected OCR text"
    row_id = database.save_uploaded_file(file_name, text, datetime.now())
    assert isinstance(row_id, int)

    with sqlite3.connect(temp_db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT file_name, extracted_text FROM uploaded_files WHERE id=?",
            (row_id,),
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == file_name
        assert "ocr" in row[1].lower()
