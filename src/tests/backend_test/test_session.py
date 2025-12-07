"""Tests for session management functionality."""

import json
import os
from pathlib import Path

import pytest

from src.backend.session import (SESSION_FILE, clear_session, get_session,
                                 save_session)


@pytest.fixture
def clean_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
    yield
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def test_save_session(clean_session):
    save_session("testuser")
    assert SESSION_FILE.exists()
    data = json.loads(SESSION_FILE.read_text())
    assert data["logged_in"] is True
    assert data["username"] == "testuser"


def test_clear_session(clean_session):
    save_session("testuser")
    assert SESSION_FILE.exists()
    clear_session()
    assert not SESSION_FILE.exists()


def test_get_session_no_file(clean_session):
    session = get_session()
    assert session["logged_in"] is False
    assert session["username"] is None


def test_get_session_with_data(clean_session):
    save_session("testuser")
    session = get_session()
    assert session["logged_in"] is True
    assert session["username"] == "testuser"
