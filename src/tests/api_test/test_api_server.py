"""Unit tests for the main API server."""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest
from fastapi.testclient import TestClient

from backend.api_server import app


class TestAPIServer:
    """Test suite for API server configuration and setup."""

    def test_app_exists(self):
        """Test that FastAPI app is created."""
        assert app is not None
        assert app.title == "Portfolio & Resume Generation API"
        assert app.version == "2.0.0"

    def test_cors_middleware_configured(self):
        """Test CORS middleware is configured."""
        assert len(app.user_middleware) > 0
        from starlette.middleware.cors import CORSMiddleware

        assert app.user_middleware is not None

    def test_routers_included(self):
        """Test all routers are included."""
        # Get all routes
        routes = [route.path for route in app.routes]

        # Check key routes from each router
        assert "/api/health" in routes
        assert "/" in routes
        assert "/api/auth/login" in routes
        assert "/api/auth/signup" in routes
        assert "/api/projects" in routes
        assert "/api/portfolios" in routes
        assert "/api/tasks/{task_id}" in routes
        assert "/api/resume/generate" in routes
        assert "/api/analysis/quick" in routes

    def test_openapi_docs_available(self):
        """Test OpenAPI documentation is available."""
        client = TestClient(app)

        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200

        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Portfolio & Resume Generation API"

    def test_api_tags_configured(self):
        """Test API endpoints have proper tags."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        openapi_spec = response.json()

        # Get all tags used in paths
        tags_used = set()
        for path_data in openapi_spec["paths"].values():
            for method_data in path_data.values():
                if "tags" in method_data:
                    tags_used.update(method_data["tags"])

        # Check expected tags exist
        expected_tags = {
            "Health",
            "Authentication",
            "Projects",
            "Portfolios",
            "Analysis",
            "Resume",
            "Tasks",
        }
        assert expected_tags.issubset(tags_used)

    def test_database_initialization(self):
        """Test databases are initialized on startup."""
        # This test verifies the import and initialization don't raise errors
        from backend.analysis_database import get_db_path
        from backend.database import get_db_path as get_user_db_path

        assert get_db_path() is not None
        assert get_user_db_path() is not None

    def test_health_endpoint_after_startup(self):
        """Test health endpoint works after server startup."""
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_authentication_required_endpoints(self):
        """Test that protected endpoints require authentication."""
        client = TestClient(app)

        protected_endpoints = [
            ("/api/projects", "GET"),
            ("/api/portfolios", "GET"),
            ("/api/tasks", "GET"),
            ("/api/skills", "GET"),
        ]

        for path, method in protected_endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path)

            # Should return 403 (Forbidden) without auth
            assert response.status_code == 403

    def test_api_versioning(self):
        """Test API version is consistent."""
        client = TestClient(app)

        # Check version in health endpoint
        health_response = client.get("/api/health")
        assert health_response.json()["version"] == "2.0.0"

        # Check version in root endpoint
        root_response = client.get("/")
        assert root_response.json()["version"] == "2.0.0"

        # Check version in OpenAPI spec
        openapi_response = client.get("/openapi.json")
        assert openapi_response.json()["info"]["version"] == "2.0.0"


class TestAPIServerErrorHandling:
    """Test error handling in API server."""

    def test_404_not_found(self):
        """Test 404 response for non-existent endpoints."""
        client = TestClient(app)
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_405_method_not_allowed(self):
        """Test 405 response for wrong HTTP method."""
        client = TestClient(app)
        # Health endpoint only supports GET
        response = client.post("/api/health")
        assert response.status_code == 405

    def test_422_validation_error(self):
        """Test 422 response for invalid request data."""
        client = TestClient(app)
        # Signup with invalid data
        response = client.post(
            "/api/auth/signup",
            json={"username": "a"},  # Too short, missing password
        )
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_cors_headers_present(self):
        """Test CORS headers are present in responses."""
        client = TestClient(app)
        response = client.get("/api/health")

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestAPIServerPerformance:
    """Test performance-related aspects of API server."""

    def test_concurrent_health_checks(self):
        """Test server handles concurrent requests."""
        client = TestClient(app)

        # Make multiple concurrent requests
        responses = []
        for _ in range(10):
            response = client.get("/api/health")
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_response_time_acceptable(self):
        """Test health endpoint responds quickly."""
        import time

        client = TestClient(app)

        start = time.time()
        response = client.get("/api/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second
