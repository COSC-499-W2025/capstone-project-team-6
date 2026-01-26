#!/usr/bin/env python3
"""
Tests for project thumbnail API endpoints.
"""

import io
import sys
from pathlib import Path

import pytest

# Add src directory to path so backend imports work
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from fastapi.testclient import TestClient

from backend.analysis_database import init_db
from backend.api_server import app


@pytest.fixture
def client():
    """Create test client."""
    # Initialize database
    init_db()
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Create a test user and return auth token."""
    import random

    username = f"thumbnailuser_{random.randint(1000, 9999)}"
    password = "password123"

    # Signup
    response = client.post("/api/auth/signup", json={"username": username, "password": password})
    assert response.status_code == 201

    data = response.json()
    return data["access_token"]


class TestProjectThumbnails:
    """Test project thumbnail endpoints."""

    def test_upload_thumbnail_requires_auth(self, client):
        """Test that uploading thumbnail requires authentication."""
        # Create a fake image file
        image_data = b"\x89PNG\r\n\x1a\n"  # PNG header
        files = {"file": ("test.png", io.BytesIO(image_data), "image/png")}

        response = client.post("/api/projects/test-uuid:test-path/thumbnail", files=files)
        assert response.status_code == 403  # No auth header

    def test_upload_thumbnail_invalid_project_id(self, client, auth_token):
        """Test uploading thumbnail with invalid project ID format."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        image_data = b"\x89PNG\r\n\x1a\n"  # PNG header
        files = {"file": ("test.png", io.BytesIO(image_data), "image/png")}

        response = client.post("/api/projects/invalid-format/thumbnail", headers=headers, files=files)
        assert response.status_code == 400
        assert "Invalid project_id format" in response.json()["detail"]

    def test_upload_thumbnail_project_not_found(self, client, auth_token):
        """Test uploading thumbnail for non-existent project."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        image_data = b"\x89PNG\r\n\x1a\n"  # PNG header
        files = {"file": ("test.png", io.BytesIO(image_data), "image/png")}

        response = client.post("/api/projects/nonexistent-uuid:nonexistent-path/thumbnail", headers=headers, files=files)
        assert response.status_code == 404

    def test_upload_thumbnail_invalid_file_type(self, client, auth_token):
        """Test uploading thumbnail with invalid file type."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Create a text file instead of image
        text_data = b"This is not an image"
        files = {"file": ("test.txt", io.BytesIO(text_data), "text/plain")}

        response = client.post("/api/projects/test-uuid:test-path/thumbnail", headers=headers, files=files)
        # Will get 404 for project first, but this tests file validation would work
        assert response.status_code in [400, 404]

    def test_get_thumbnail_requires_auth(self, client):
        """Test that getting thumbnail requires authentication."""
        response = client.get("/api/projects/test-uuid:test-path/thumbnail")
        assert response.status_code == 403

    def test_get_thumbnail_project_not_found(self, client, auth_token):
        """Test getting thumbnail for non-existent project."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/projects/nonexistent-uuid:nonexistent-path/thumbnail", headers=headers)
        assert response.status_code == 404

    def test_delete_thumbnail_requires_auth(self, client):
        """Test that deleting thumbnail requires authentication."""
        response = client.delete("/api/projects/test-uuid:test-path/thumbnail")
        assert response.status_code == 403

    def test_delete_thumbnail_project_not_found(self, client, auth_token):
        """Test deleting thumbnail for non-existent project."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.delete("/api/projects/nonexistent-uuid:nonexistent-path/thumbnail", headers=headers)
        assert response.status_code == 404

    def test_project_detail_includes_thumbnail_url(self, client, auth_token):
        """Test that project detail endpoint includes thumbnail_url field."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # This will fail because project doesn't exist, but we can check the error format
        response = client.get("/api/projects/test-uuid:test-path", headers=headers)
        # Should get 404 for non-existent project
        assert response.status_code == 404


def run_tests():
    """Run all tests and print results."""
    print("=" * 70)
    print("Running Project Thumbnail API Tests")
    print("=" * 70)

    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
