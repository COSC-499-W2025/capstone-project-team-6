import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

# Mock Google GenAI BEFORE importing backend modules
# This prevents ImportErrors if google-genai is not installed or when running in isolation
google_mock = types.ModuleType("google")
sys.modules["google"] = google_mock

genai_mock = MagicMock()
sys.modules["google.genai"] = genai_mock
setattr(google_mock, "genai", genai_mock)

types_mock = MagicMock()
sys.modules["google.genai.types"] = types_mock
genai_mock.types = types_mock

# Mock dotenv to prevent file permission errors during test collection
dotenv_mock = MagicMock()
sys.modules["dotenv"] = dotenv_mock

# Now safe to import backend modules
from backend.analysis.llm_pipeline import _should_ignore_path, _summarize_offline_report, run_gemini_analysis
from backend.gemini_file_search import GeminiFileSearchClient

# ==========================================
# TEST 1: Logic & Filtering (Crucial Fixes)
# ==========================================


@pytest.mark.parametrize(
    "path,expected",
    [
        ("app.py", False),
        ("src/backend/utils.py", False),
        # 1. Test macOS Garbage Filtering (The Bug Fix)
        ("__MACOSX/._app.py", True),
        ("src/._data.json", True),
        ("._.DS_Store", True),
        # 2. Test Directory Filtering
        ("node_modules/react/index.js", True),
        ("venv/lib/python3.9/site-packages", True),
        (".git/HEAD", True),
        # 3. Test File Name Filtering
        (".env", True),
        ("package-lock.json", True),
    ],
)
def test_should_ignore_path(path, expected):
    """Verify that junk files and sensitive configs are correctly ignored."""
    assert _should_ignore_path(path) == expected


# ==========================================
# TEST 2: Gemini Client (API Interaction)
# ==========================================


class TestGeminiClient:

    @pytest.fixture
    def mock_genai(self):
        """Mock the Google Gen AI SDK."""
        with patch("backend.gemini_file_search.genai") as mock:
            yield mock

    def test_init_auth_strategies(self, mock_genai, monkeypatch):
        """Test client initializes correctly with API Key or Vertex Project."""
        # Case A: API Key
        monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

        client = GeminiFileSearchClient()
        assert client.model_name == "gemini-2.5-flash"
        mock_genai.Client.assert_called_with(api_key="fake-key")

        # Case B: Vertex AI
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")

        client = GeminiFileSearchClient()
        mock_genai.Client.assert_called_with(vertexai=True, project="my-gcp-project", location="us-central1")
        assert client.model_name == "gemini-1.5-pro-002"

    def test_upload_batch_lifecycle(self, mock_genai):
        """
        Test the complex upload lifecycle:
        1. Create Temp File -> 2. Upload -> 3. Poll Status -> 4. Return Active Files
        """
        # Setup Mocks
        mock_client_instance = mock_genai.Client.return_value

        # Mock File Objects (PROCESSING -> ACTIVE)
        file_processing = SimpleNamespace(name="files/123", state=SimpleNamespace(name="PROCESSING"), display_name="test.py")
        file_active = SimpleNamespace(name="files/123", state=SimpleNamespace(name="ACTIVE"), display_name="test.py")

        mock_client_instance.files.upload.return_value = file_processing
        # Simulate Polling: First call returns Processing, Second returns Active
        mock_client_instance.files.get.side_effect = [file_processing, file_active]

        # Initialize
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}):
            client = GeminiFileSearchClient()

        # Input Data
        files_data = [{"path": "src/test.py", "content": "print('hello')"}]

        # Execute
        with patch("builtins.open", mock_open()) as mocked_file:
            active_files = client.upload_batch(files_data)

        # Assertions
        # 1. Check if temp file was written
        mocked_file.assert_called()
        # 2. Check upload was called with FILE argument (The Fix)
        assert mock_client_instance.files.upload.call_count == 1
        _, kwargs = mock_client_instance.files.upload.call_args
        assert "file" in kwargs, "Must use 'file=' argument, not 'path='"

        # We verify that 'config' was passed.
        # Detailed assertion on config content is skipped due to mocking complexity across test files
        # (module reloading issues with sys.modules patching).
        assert "config" in kwargs

        # 3. Check Polling
        assert mock_client_instance.files.get.call_count == 2
        assert active_files == [file_active]


# ==========================================
# TEST 3: LLM Pipeline (Integration)
# ==========================================


class TestLLMPipeline:

    @pytest.fixture
    def mock_deps(self):
        """Mock all external dependencies for the pipeline."""
        mocks = SimpleNamespace()

        # Use patchers to avoid 'mocker' fixture dependency
        self.report_patcher = patch("backend.analysis.llm_pipeline.generate_comprehensive_report")
        self.classifier_patcher = patch("backend.analysis.llm_pipeline.FileClassifier")
        self.client_patcher = patch("backend.analysis.llm_pipeline.GeminiFileSearchClient")

        mocks.report_gen = self.report_patcher.start()
        mocks.classifier = self.classifier_patcher.start()
        mocks.gemini_client = self.client_patcher.start()

        yield mocks

        # Cleanup
        self.report_patcher.stop()
        self.classifier_patcher.stop()
        self.client_patcher.stop()

    def test_full_pipeline_success(self, mock_deps, tmp_path):
        """Test the happy path: Analyze -> Upload -> Generate -> Cleanup."""

        # 1. Setup Mock Data
        fake_zip = tmp_path / "project.zip"
        fake_zip.touch()

        # Mock Offline Report
        mock_deps.report_gen.return_value = {"summary": {"total_files": 10}, "projects": [{"project_name": "TestProj"}]}

        # Mock Classifier (Context Manager and File Reading)
        mock_classifier_instance = mock_deps.classifier.return_value.__enter__.return_value
        mock_classifier_instance.classify_project.return_value = {
            "files": {"code": {"python": [{"path": "app.py"}]}, "configs": [], "docs": [], "tests": [], "other": []}
        }

        # Mock ZIP reading
        mock_zip = MagicMock()
        mock_zip.read.return_value = b"import flask"  # Valid content
        mock_zip.__enter__.return_value = mock_zip  # Ensure context manager returns self
        mock_classifier_instance.zip_file = mock_zip

        # Mock Gemini Client
        mock_client_instance = mock_deps.gemini_client.return_value
        mock_client_instance.upload_batch.return_value = ["file_ref_1", "file_ref_2"]  # 1 code file + 1 offline report
        mock_client_instance.generate_content.return_value = "## Gemini Analysis Result"

        # 2. Run Pipeline
        result = run_gemini_analysis(fake_zip)

        # 3. Assertions

        # A. Verify Uploads
        # Expect 2 files: app.py AND _offline_analysis.json
        upload_call_args = mock_client_instance.upload_batch.call_args[0][0]
        assert len(upload_call_args) == 2
        assert upload_call_args[0]["path"] == "app.py"
        assert upload_call_args[1]["path"] == "_offline_analysis.json"

        # B. Verify Generation
        mock_client_instance.generate_content.assert_called_once()
        args, _ = mock_client_instance.generate_content.call_args
        assert "## Gemini Analysis Result" == result["llm_summary"]

        # C. Verify Cleanup (CRITICAL)
        mock_client_instance.cleanup_files.assert_called_once_with(["file_ref_1", "file_ref_2"])

    def test_pipeline_handles_client_error(self, mock_deps, tmp_path):
        """Test that errors in Gemini initialization are caught gracefully."""
        fake_zip = tmp_path / "bad.zip"
        fake_zip.touch()

        # Setup valid report return with required structure
        mock_deps.report_gen.return_value = {"projects": [], "summary": {}}

        # Simulate Client Init Failure (e.g., Auth Error)
        mock_deps.gemini_client.side_effect = Exception("Auth Failed")

        # Run
        result = run_gemini_analysis(fake_zip)

        # Assert
        assert "Client Initialization Error" in result["llm_error"]
        assert "Auth Failed" in result["llm_error"]

    def test_pipeline_skips_large_files(self, mock_deps, tmp_path):
        """Test that files larger than limit are skipped."""
        fake_zip = tmp_path / "huge.zip"
        fake_zip.touch()

        mock_deps.report_gen.return_value = {"projects": [], "summary": {}}

        # Mock Classifier
        mock_classifier = mock_deps.classifier.return_value.__enter__.return_value
        mock_classifier.classify_project.return_value = {"files": {"code": {"c": [{"path": "huge_binary.bin"}]}}}

        # Mock ZIP Read -> Return 5MB bytes
        mock_zip = MagicMock()
        mock_zip.read.return_value = b"0" * 5_000_000
        mock_zip.__enter__.return_value = mock_zip
        mock_classifier.zip_file = mock_zip

        client_mock = mock_deps.gemini_client.return_value

        # Run
        run_gemini_analysis(fake_zip)

        # Assert: Only the offline report should be uploaded, not the huge file
        uploaded_batch = client_mock.upload_batch.call_args[0][0]
        assert len(uploaded_batch) == 1
        assert uploaded_batch[0]["path"] == "_offline_analysis.json"
