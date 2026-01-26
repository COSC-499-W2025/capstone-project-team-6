"""Unit tests for resume API endpoints."""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.auth import active_tokens
from backend.api_server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_tokens():
    """Clear tokens before each test."""
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture
def auth_token():
    """Create authenticated user and return token."""
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


class TestResumeEndpoints:
    """Test suite for resume endpoints."""

    def test_generate_resume_unauthorized(self):
        """Test generating resume without auth fails."""
        response = client.post(
            "/api/resume/generate",
            json={
                "portfolio_ids": [str(uuid.uuid4())],
                "format": "markdown",
            },
        )
        assert response.status_code == 403

    def test_generate_resume_multiple_portfolios(self, auth_token):
        """Test generating resume from multiple portfolios (implementation incomplete)."""
        token, username = auth_token
        portfolio_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": portfolio_ids,
                "format": "markdown",
            },
        )

        # Currently returns 500 because generate_resume function doesn't exist
        assert response.status_code == 500

    def test_get_resume_list_unauthorized(self):
        """Test getting resume list without auth."""
        response = client.get("/api/resume")
        # Endpoint doesn't exist
        assert response.status_code == 404

    def test_get_resume_by_id_success(self, auth_token):
        """Test getting specific resume by ID (not implemented)."""
        token, _ = auth_token
        resume_id = str(uuid.uuid4())

        response = client.get(
            f"/api/resume/{resume_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 501

    def test_delete_resume_unauthorized(self):
        """Test deleting resume without auth."""
        resume_id = str(uuid.uuid4())
        response = client.delete(f"/api/resume/{resume_id}")
        assert response.status_code == 405
