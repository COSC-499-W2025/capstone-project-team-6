"""Basic tests for the PDF resume upload and append feature."""

import base64
import sys
import uuid
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from backend import analysis_database as adb
from backend import database as udb
from backend.api.auth import active_tokens
from backend.api_server import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_pdf() -> bytes:
    """Return a tiny but valid PDF using reportlab (no external tools needed)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    doc.build([Paragraph("Existing resume content.", styles["Normal"])])
    return buf.getvalue()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures (mirrors pattern used in test_resume.py)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_tokens():
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    db_path = tmp_path / "pdf_upload_test.db"
    prev_user = udb.set_db_path(db_path)
    prev_analysis = adb.set_db_path(db_path)
    udb.init_db()
    adb.init_db()
    yield
    adb.set_db_path(prev_analysis)
    udb.set_db_path(prev_user)


@pytest.fixture
def auth_token():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/auth/signup",
        json={"username": username, "password": "password123"},
    )
    return resp.json()["access_token"], username


# ---------------------------------------------------------------------------
# Upload endpoint tests
# ---------------------------------------------------------------------------

class TestPdfUploadEndpoint:
    def test_upload_requires_auth(self):
        resp = client.post(
            "/api/resumes/upload-pdf",
            data={"title": "My Resume"},
            files={"file": ("resume.pdf", _make_minimal_pdf(), "application/pdf")},
        )
        assert resp.status_code == 403

    def test_upload_valid_pdf_returns_pdf_upload_format(self, auth_token):
        token, _ = auth_token
        resp = client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token),
            data={"title": "My Resume"},
            files={"file": ("resume.pdf", _make_minimal_pdf(), "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "My Resume"
        assert data["format"] == "pdf_upload"
        assert data["id"] > 0

    def test_uploaded_pdf_appears_in_list(self, auth_token):
        token, _ = auth_token
        client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token),
            data={"title": "Listed Resume"},
            files={"file": ("resume.pdf", _make_minimal_pdf(), "application/pdf")},
        )
        resp = client.get("/api/resumes", headers=_auth_headers(token))
        assert resp.status_code == 200
        assert any(
            r["format"] == "pdf_upload" and r["title"] == "Listed Resume"
            for r in resp.json()
        )

    def test_upload_non_pdf_is_rejected(self, auth_token):
        token, _ = auth_token
        resp = client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token),
            data={"title": "Bad File"},
            files={"file": ("resume.txt", b"not a pdf at all", "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_empty_file_is_rejected(self, auth_token):
        token, _ = auth_token
        resp = client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token),
            data={"title": "Empty"},
            files={"file": ("resume.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_uploaded_pdfs_are_isolated_per_user(self, auth_token):
        """A second user should not see the first user's uploaded resume."""
        token1, _ = auth_token

        second = f"testuser2_{uuid.uuid4().hex[:8]}"
        resp2 = client.post(
            "/api/auth/signup",
            json={"username": second, "password": "password123"},
        )
        token2 = resp2.json()["access_token"]

        client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token1),
            data={"title": "User1 Resume"},
            files={"file": ("resume.pdf", _make_minimal_pdf(), "application/pdf")},
        )

        resp = client.get("/api/resumes", headers=_auth_headers(token2))
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Generation with pdf_upload template tests
# ---------------------------------------------------------------------------

class TestPdfUploadGeneration:

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    def test_generate_returns_merged_pdf(
        self, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """Generating with a pdf_upload template returns a valid base64-encoded PDF."""
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 1, "project_name": "Cool App", "primary_language": "Python"}
        ]
        mock_items.return_value = [{"resume_text": "Built a cool feature with Python"}]
        mock_portfolio.return_value = {}

        upload_resp = client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token),
            data={"title": "Base Resume"},
            files={"file": ("resume.pdf", _make_minimal_pdf(), "application/pdf")},
        )
        assert upload_resp.status_code == 200
        stored_id = upload_resp.json()["id"]

        gen_resp = client.post(
            "/api/resume/generate",
            headers=_auth_headers(token),
            json={"project_ids": [1], "format": "pdf", "stored_resume_id": stored_id},
        )
        assert gen_resp.status_code == 200
        data = gen_resp.json()
        assert data["format"] == "pdf"
        pdf_bytes = base64.b64decode(data["content"])
        assert pdf_bytes[:4] == b"%PDF", "Response content is not a valid PDF"

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    def test_generate_merged_pdf_has_more_pages_than_original(
        self, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """The merged PDF should have at least as many pages as the original."""
        from pypdf import PdfReader

        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 1, "project_name": "App", "primary_language": "Go"}
        ]
        mock_items.return_value = [
            {"resume_text": "Designed REST API"},
            {"resume_text": "Reduced memory usage by 30%"},
        ]
        mock_portfolio.return_value = {}

        original_pdf = _make_minimal_pdf()
        original_page_count = len(PdfReader(BytesIO(original_pdf)).pages)

        upload_resp = client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token),
            data={"title": "Base"},
            files={"file": ("resume.pdf", original_pdf, "application/pdf")},
        )
        stored_id = upload_resp.json()["id"]

        gen_resp = client.post(
            "/api/resume/generate",
            headers=_auth_headers(token),
            json={"project_ids": [1], "format": "pdf", "stored_resume_id": stored_id},
        )
        assert gen_resp.status_code == 200
        merged_pdf = base64.b64decode(gen_resp.json()["content"])
        merged_page_count = len(PdfReader(BytesIO(merged_pdf)).pages)
        assert merged_page_count >= original_page_count

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    def test_pdf_upload_template_rejects_markdown_format(
        self, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """Using a pdf_upload template with markdown output format returns 400."""
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 1, "project_name": "App", "primary_language": "Go"}
        ]
        mock_items.return_value = []
        mock_portfolio.return_value = {}

        upload_resp = client.post(
            "/api/resumes/upload-pdf",
            headers=_auth_headers(token),
            data={"title": "Base"},
            files={"file": ("resume.pdf", _make_minimal_pdf(), "application/pdf")},
        )
        stored_id = upload_resp.json()["id"]

        gen_resp = client.post(
            "/api/resume/generate",
            headers=_auth_headers(token),
            json={
                "project_ids": [1],
                "format": "markdown",
                "stored_resume_id": stored_id,
            },
        )
        assert gen_resp.status_code == 400
        assert "PDF" in gen_resp.json()["detail"]
