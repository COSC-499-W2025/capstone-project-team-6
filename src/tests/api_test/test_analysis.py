"""Unit tests for analysis API endpoints."""

import sys
from pathlib import Path
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


class TestAnalysisEndpoints:
    """Test suite for analysis endpoints."""

    @patch("backend.api.analysis.get_analysis_by_uuid")
    @patch("backend.api.analysis.check_user_consent")
    def test_reanalyze_portfolio_not_implemented(
        self, mock_consent, mock_get_analysis, auth_token
    ):
        """Test re-analyzing returns not implemented."""
        token, username = auth_token
        portfolio_id = str(uuid.uuid4())
        
        mock_consent.return_value = True
        mock_get_analysis.return_value = {"zip_file": "/path/to/test.zip"}
        
        response = client.post(
            f"/api/analysis/portfolios/{portfolio_id}/reanalyze",
            headers={"Authorization": f"Bearer {token}"},
            data={"analysis_type": "llm"},
        )
        
        # Endpoint returns 501 Not Implemented
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"].lower()

    @patch("backend.api.analysis.check_user_consent")
    @patch("backend.api.analysis.get_analysis_by_uuid")
    def test_reanalyze_portfolio_no_consent(self, mock_get_analysis, mock_consent, auth_token):
        """Test re-analyzing without consent fails."""
        token, _ = auth_token
        mock_consent.return_value = False
        mock_get_analysis.return_value = {"zip_file": "/path/to/test.zip"}
        portfolio_id = str(uuid.uuid4())
        
        response = client.post(
            f"/api/analysis/portfolios/{portfolio_id}/reanalyze",
            headers={"Authorization": f"Bearer {token}"},
            data={"analysis_type": "llm"},
        )
        
        assert response.status_code == 403
        assert "consent" in response.json()["detail"].lower()

    @patch("backend.api.analysis.check_user_consent")
    @patch("backend.api.analysis.get_analysis_by_uuid")
    def test_reanalyze_portfolio_not_found(self, mock_get_analysis, mock_consent, auth_token):
        """Test re-analyzing non-existent portfolio fails."""
        token, _ = auth_token
        mock_consent.return_value = True
        mock_get_analysis.return_value = None
        portfolio_id = str(uuid.uuid4())
        
        response = client.post(
            f"/api/analysis/portfolios/{portfolio_id}/reanalyze",
            headers={"Authorization": f"Bearer {token}"},
            data={"analysis_type": "llm"},
        )
        
        assert response.status_code == 404

    def test_reanalyze_portfolio_unauthorized(self):
        """Test re-analyzing without auth fails."""
        portfolio_id = str(uuid.uuid4())
        response = client.post(
            f"/api/analysis/portfolios/{portfolio_id}/reanalyze",
            data={"analysis_type": "llm"},
        )
        assert response.status_code == 403

    @patch("backend.api.analysis.check_user_consent")
    def test_quick_analyze_no_consent(self, mock_consent, auth_token):
        """Test quick analysis without consent fails."""
        token, _ = auth_token
        mock_consent.return_value = False
        
        files = {"file": ("test.zip", b"test content", "application/zip")}
        
        response = client.post(
            "/api/analysis/quick",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data={"analysis_type": "non_llm"},
        )
        
        assert response.status_code == 403

    def test_quick_analyze_no_file(self, auth_token):
        """Test quick analysis without file fails."""
        token, _ = auth_token
        
        response = client.post(
            "/api/analysis/quick",
            headers={"Authorization": f"Bearer {token}"},
            data={"analysis_type": "non_llm"},
        )
        
        assert response.status_code == 422  # Validation error

    def test_get_analysis_status(self, auth_token):
        """Test getting analysis status."""
        token, _ = auth_token
        
        response = client.get(
            "/api/analysis/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "statistics" in data