"""Unit tests for authentication endpoints."""

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.auth import active_tokens, create_access_token, verify_token
from backend.api_server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_tokens():
    """Clear tokens before each test."""
    active_tokens.clear()
    yield
    active_tokens.clear()


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    def test_signup_success(self):
        """Test successful user registration."""
        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        
        response = client.post(
            "/api/auth/signup",
            json={"username": test_username, "password": "password123"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_username
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_signup_duplicate_username(self):
        """Test signup with existing username fails."""
        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        
        # First signup
        client.post(
            "/api/auth/signup",
            json={"username": test_username, "password": "password123"},
        )
        
        response = client.post(
            "/api/auth/signup",
            json={"username": test_username, "password": "password123"},
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_signup_short_username(self):
        """Test signup with username too short fails."""
        response = client.post(
            "/api/auth/signup",
            json={"username": "ab", "password": "password123"},
        )
        
        assert response.status_code == 422  # Validation error

    def test_signup_short_password(self):
        """Test signup with password too short fails."""
        response = client.post(
            "/api/auth/signup",
            json={"username": "testuser", "password": "12345"},
        )
        
        assert response.status_code == 422  # Validation error

    def test_login_success(self):
        """Test successful login."""
        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        password = "password123"
        
        # Signup first
        client.post(
            "/api/auth/signup",
            json={"username": test_username, "password": password},
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={"username": test_username, "password": password},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_username
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_login_wrong_password(self):
        """Test login with wrong password fails."""
        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        
        # Signup
        client.post(
            "/api/auth/signup",
            json={"username": test_username, "password": "password123"},
        )
        
        # Login with wrong password
        response = client.post(
            "/api/auth/login",
            json={"username": test_username, "password": "wrongpassword"},
        )
        
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with non-existent user fails."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )
        
        assert response.status_code == 401

    def test_logout_success(self):
        """Test successful logout."""
        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        
        # Signup
        signup_response = client.post(
            "/api/auth/signup",
            json={"username": test_username, "password": "password123"},
        )
        token = signup_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    def test_logout_removes_token(self):
        """Test logout removes token from active tokens."""
        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        
        # Signup
        signup_response = client.post(
            "/api/auth/signup",
            json={"username": test_username, "password": "password123"},
        )
        token = signup_response.json()["access_token"]
        
        assert token in active_tokens
        
        # Logout
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert token not in active_tokens

    def test_logout_without_token(self):
        """Test logout without token fails."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 403  # Forbidden

    def test_logout_invalid_token(self):
        """Test logout with invalid token fails."""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


class TestTokenFunctions:
    """Test token management functions."""

    def test_create_access_token(self):
        """Test token creation."""
        username = "testuser"
        token = create_access_token(username)
        
        assert token in active_tokens
        assert active_tokens[token]["username"] == username
        assert "expires_at" in active_tokens[token]

    def test_token_expiration_time(self):
        """Test token has 24 hour expiration."""
        username = "testuser"
        token = create_access_token(username)
        
        expires_at = active_tokens[token]["expires_at"]
        created_at = active_tokens[token]["created_at"]
        
        # Should expire in approximately 24 hours
        delta = expires_at - created_at
        assert 23.9 * 3600 <= delta.total_seconds() <= 24.1 * 3600

    def test_expired_token_rejected(self):
        """Test expired tokens are rejected."""
        username = "testuser"
        token = create_access_token(username)
        
        # Manually expire the token
        active_tokens[token]["expires_at"] = datetime.now() - timedelta(hours=1)
        
        # Try to use expired token
        response = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 401
        assert token not in active_tokens  # Should be removed
