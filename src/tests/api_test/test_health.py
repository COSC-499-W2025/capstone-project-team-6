"""Unit tests for health check endpoints."""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest
from fastapi.testclient import TestClient

from backend.api_server import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_health_check_success(self):
        """Test health check returns healthy status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data

    def test_health_check_returns_iso_timestamp(self):
        """Test health check returns ISO formatted timestamp."""
        response = client.get("/api/health")
        data = response.json()
        
        # Verify timestamp format
        timestamp = data["timestamp"]
        assert "T" in timestamp  # ISO format includes T
        assert isinstance(timestamp, str)

    def test_root_endpoint_success(self):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MDA Portfolio API"
        assert data["version"] == "2.0.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/health"

    def test_root_endpoint_structure(self):
        """Test root endpoint returns all required fields."""
        response = client.get("/")
        data = response.json()
        
        required_fields = ["name", "version", "docs", "health"]
        for field in required_fields:
            assert field in data
            assert isinstance(data[field], str)

    def test_health_check_no_authentication_required(self):
        """Test health check doesn't require authentication."""
        # Should work without any auth headers
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_root_no_authentication_required(self):
        """Test root endpoint doesn't require authentication."""
        # Should work without any auth headers
        response = client.get("/")
        assert response.status_code == 200

    def test_health_check_consistent_version(self):
        """Test health check version matches root endpoint."""
        health_response = client.get("/api/health")
        root_response = client.get("/")
        
        assert health_response.json()["version"] == root_response.json()["version"]
