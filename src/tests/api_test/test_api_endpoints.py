#!/usr/bin/env python3
"""
Tests for API endpoints (without requiring a running server).
"""

import sys
from pathlib import Path

import pytest

# Add src directory to path so backend imports work
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from fastapi.testclient import TestClient

from backend.api.auth import active_tokens, create_access_token, verify_token
from backend.api_server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Test user credentials."""
    return {"username": "testuser_api", "password": "testpass123"}


class TestHealthEndpoints:
    """Test health check and info endpoints."""

    def test_health_check(self, client):
        """Test GET /api/health returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test GET /api/info returns API info."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MDA Portfolio API"
        assert data["version"] == "2.0.0"
        assert data["docs"] == "/docs"


class TestAuthentication:
    """Test authentication endpoints."""

    def test_signup_success(self, client):
        """Test POST /api/auth/signup with valid credentials."""
        import random

        username = f"newuser_{random.randint(1000, 9999)}"

        response = client.post("/api/auth/signup", json={"username": username, "password": "password123"})

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert data["username"] == username

    def test_signup_short_password(self, client):
        """Test signup rejects password less than 6 characters."""
        response = client.post("/api/auth/signup", json={"username": "testuser", "password": "12345"})
        assert response.status_code == 422  # Validation error

    def test_signup_short_username(self, client):
        """Test signup rejects username less than 3 characters."""
        response = client.post("/api/auth/signup", json={"username": "ab", "password": "password123"})
        assert response.status_code == 422  # Validation error

    def test_signup_duplicate_user(self, client):
        """Test signup fails for existing username."""
        import random

        username = f"dupuser_{random.randint(1000, 9999)}"

        # Create user first time
        response1 = client.post("/api/auth/signup", json={"username": username, "password": "password123"})
        assert response1.status_code == 201

        # Try to create same user again
        response2 = client.post("/api/auth/signup", json={"username": username, "password": "password123"})
        assert response2.status_code == 409  # Conflict

    def test_login_success(self, client):
        """Test POST /api/auth/login with valid credentials."""
        import random

        username = f"loginuser_{random.randint(1000, 9999)}"
        password = "password123"

        # Create user first
        client.post("/api/auth/signup", json={"username": username, "password": password})

        # Try to login
        response = client.post("/api/auth/login", json={"username": username, "password": password})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert data["username"] == username

    def test_login_wrong_password(self, client):
        """Test login fails with wrong password."""
        import random

        username = f"wrongpass_{random.randint(1000, 9999)}"

        # Create user
        client.post("/api/auth/signup", json={"username": username, "password": "correctpass"})

        # Try to login with wrong password
        response = client.post("/api/auth/login", json={"username": username, "password": "wrongpass"})
        assert response.status_code == 401  # Unauthorized

    def test_login_nonexistent_user(self, client):
        """Test login fails for nonexistent user."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent_user_xyz", "password": "password123"},
        )
        assert response.status_code == 401


class TestTokenManagement:
    """Test token creation and verification."""

    def test_create_access_token(self):
        """Test token creation returns valid token."""
        token = create_access_token("testuser")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_expires(self):
        """Test token has expiration time."""
        token = create_access_token("testuser_expire")
        assert token in active_tokens
        assert "expires_at" in active_tokens[token]
        assert "created_at" in active_tokens[token]


class TestRequestValidation:
    """Test request validation and error handling."""

    def test_missing_username(self, client):
        """Test signup fails without username."""
        response = client.post("/api/auth/signup", json={"password": "password123"})
        assert response.status_code == 422

    def test_missing_password(self, client):
        """Test signup fails without password."""
        response = client.post("/api/auth/signup", json={"username": "testuser"})
        assert response.status_code == 422

    def test_invalid_json(self, client):
        """Test endpoints reject invalid JSON."""
        response = client.post("/api/auth/signup", content="not json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_missing_auth_header(self, client):
        """Test protected endpoints require auth header."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 403  # Forbidden (no auth header)

    def test_invalid_token_format(self, client):
        """Test endpoints reject invalid token format."""
        response = client.post("/api/auth/logout", headers={"Authorization": "Bearer invalid_token_xyz"})
        assert response.status_code == 401  # Unauthorized


class TestPortfolioEndpoints:
    """Test portfolio endpoints (will fail due to missing DB functions)."""

    def test_list_portfolios_requires_auth(self, client):
        """Test GET /api/portfolios requires authentication."""
        response = client.get("/api/portfolios")
        assert response.status_code == 403  # No auth header

    def test_list_portfolios_with_invalid_token(self, client):
        """Test portfolio list rejects invalid token."""
        response = client.get("/api/portfolios", headers={"Authorization": "Bearer fake_token"})
        assert response.status_code == 401


class TestAnalysisEndpoints:
    def give_consent(self, client, token):
        resp = client.post(
            "/api/user/consent",
            json={"has_consented": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_quick_analysis_requires_file(self, client):
        import uuid

        username = f"testuser_{uuid.uuid4().hex[:8]}"
        password = "testpass123"
        signup = client.post("/api/auth/signup", json={"username": username, "password": password})
        token = signup.json()["access_token"]
        self.give_consent(client, token)
        resp = client.post("/api/analysis/quick", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 422

    def test_reanalyze_portfolio_not_found(self, client):
        import uuid

        username = f"testuser_{uuid.uuid4().hex[:8]}"
        password = "testpass123"
        signup = client.post("/api/auth/signup", json={"username": username, "password": password})
        token = signup.json()["access_token"]
        self.give_consent(client, token)
        resp = client.post(
            "/api/analysis/portfolios/doesnotexist/reanalyze",
            data={"analysis_type": "llm"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (404, 501)


class TestCurationEndpoints:
    def test_get_curation_settings_unauth(self, client):
        resp = client.get("/api/curation/settings")
        assert resp.status_code in (401, 403)


class TestResumeEndpoints:
    def test_resume_unauthenticated(self, client):
        resp = client.get("/api/resume/1")
        assert resp.status_code in (401, 403)


class TestTasksEndpoints:
    def test_get_task_status_unauth(self, client):
        resp = client.get("/api/tasks/123/status")
        assert resp.status_code in (401, 403)

    def test_list_tasks_unauth(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code in (401, 403)


def test_api_documentation():
    """Test that API documentation is accessible."""
    client = TestClient(app)

    # OpenAPI JSON
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()


def run_tests():
    """Run all tests and print results."""
    print("=" * 70)
    print("Running API Endpoint Tests")
    print("=" * 70)

    # Run with pytest
    exit_code = pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-k",
            "not test_list_portfolios",  # Skip tests that need DB
        ]
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
