"""
Tests for the LLM Pipeline.
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Mock missing Google dependencies globally
# We need to construct a proper package structure for google.genai
google_mock = types.ModuleType("google")
sys.modules["google"] = google_mock

genai_mock = MagicMock()
sys.modules["google.genai"] = genai_mock
setattr(google_mock, "genai", genai_mock)

types_mock = MagicMock()
sys.modules["google.genai.types"] = types_mock
genai_mock.types = types_mock

# Mock other google modules if needed
sys.modules["google.auth"] = MagicMock()
sys.modules["google.auth.transport"] = MagicMock()
sys.modules["google.auth.transport.requests"] = MagicMock()
sys.modules["google.ai"] = MagicMock()
sys.modules["google.ai.generativelanguage_v1beta"] = MagicMock()
sys.modules["google.ai.generativelanguage_v1beta.types"] = MagicMock()
sys.modules["google.oauth2"] = MagicMock()
sys.modules["google.api_core"] = MagicMock()
sys.modules["tenacity"] = MagicMock()

# Mock dotenv to prevent file permission errors during test collection
dotenv_mock = MagicMock()
sys.modules["dotenv"] = dotenv_mock

# Adjust path
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.analysis.llm_pipeline import _should_ignore_path, run_gemini_analysis


class TestLLMPipeline:

    @pytest.fixture
    def mock_gemini_client(self):
        with patch("backend.analysis.llm_pipeline.GeminiFileSearchClient") as MockClient:
            client_instance = MockClient.return_value
            # Mock return values
            client_instance.upload_batch.return_value = [MagicMock(name="files/123"), MagicMock(name="files/456")]
            client_instance.generate_content.return_value = "Mock LLM Summary"
            yield client_instance

    @pytest.fixture
    def mock_generate_report(self):
        with patch("backend.analysis.llm_pipeline.generate_comprehensive_report") as mock_report:
            mock_report.return_value = {
                "analysis_metadata": {
                    "zip_file": "test.zip",
                    "analysis_timestamp": "2023-01-01",
                    "total_projects": 1,
                },
                "summary": {
                    "total_files": 2,
                    "total_size_mb": 0.1,
                    "languages_used": ["python"],
                    "frameworks_used": ["fastapi"],
                },
                "projects": [
                    {
                        "project_name": "test-project",
                        "project_path": "",
                        "primary_language": "python",
                        "total_files": 2,
                        "has_tests": True,
                        "oop_analysis": {"oop_score": 3},
                    }
                ],
            }
            yield mock_report

    @pytest.fixture
    def mock_file_classifier(self):
        with patch("backend.analysis.project_analyzer.FileClassifier") as MockClassifier:
            classifier_instance = MockClassifier.return_value
            classifier_instance.__enter__.return_value = classifier_instance

            classifier_instance.classify_project.return_value = {
                "files": {
                    "code": {"python": [{"path": "main.py", "size": 100}]},
                    "configs": [{"path": "config.json", "size": 50}],
                    "docs": [],
                    "tests": [],
                    "other": [],
                }
            }

            mock_zip = MagicMock()
            # Configure read to return content when path is accessed
            mock_zip.read.return_value = b"file content"
            classifier_instance.zip_file = mock_zip

            yield classifier_instance

    def test_run_gemini_analysis_success(self, mock_gemini_client, mock_generate_report, mock_file_classifier):
        # Patch FileClassifier constructor where it is used in pipeline
        with patch("backend.analysis.llm_pipeline.FileClassifier", return_value=mock_file_classifier):
            zip_path = Path("test.zip")

            report = run_gemini_analysis(zip_path)

            assert report["llm_summary"] == "Mock LLM Summary"
            assert report["analysis_metadata"]["gemini_file_count"] == 2  # mocked return len

            # Verify Upload Batch called
            mock_gemini_client.upload_batch.assert_called_once()
            uploaded_files = mock_gemini_client.upload_batch.call_args[0][0]

            # Check if expected files are in the upload list
            paths = [f["path"] for f in uploaded_files]
            assert "main.py" in paths
            assert "_offline_analysis.json" in paths

            # Verify prompt construction contains offline summary
            call_args = mock_gemini_client.generate_content.call_args
            prompt_used = call_args[0][1]
            assert "Offline Analysis Context" in prompt_used
            assert "test-project" in prompt_used

            # Verify cleanup is called in finally block
            mock_gemini_client.cleanup_files.assert_called_once()

    def test_run_gemini_analysis_error_handling(self, mock_gemini_client, mock_generate_report, mock_file_classifier):
        # Patch FileClassifier
        with patch("backend.analysis.llm_pipeline.FileClassifier", return_value=mock_file_classifier):
            # Simulate upload failure
            mock_gemini_client.upload_batch.side_effect = Exception("Upload failed")

            zip_path = Path("test.zip")
            report = run_gemini_analysis(zip_path)

            assert "llm_error" in report
            assert "Upload failed" in report["llm_error"]
            # Should still return offline analysis
            assert report["projects"][0]["project_name"] == "test-project"

            # Cleanup should not be called if upload failed (uploaded_files_refs is empty)
            mock_gemini_client.cleanup_files.assert_not_called()

    def test_run_gemini_analysis_generation_error(self, mock_gemini_client, mock_generate_report, mock_file_classifier):
        """Test error during generation but after upload (cleanup should happen)."""
        with patch("backend.analysis.llm_pipeline.FileClassifier", return_value=mock_file_classifier):
            # Upload succeeds
            mock_gemini_client.upload_batch.return_value = [MagicMock(name="f1")]
            # Generation fails
            mock_gemini_client.generate_content.side_effect = Exception("Generation failed")

            zip_path = Path("test.zip")
            report = run_gemini_analysis(zip_path)

            assert "llm_error" in report
            assert "Generation failed" in report["llm_error"]

            # Cleanup MUST be called
            mock_gemini_client.cleanup_files.assert_called_once()

    def test_ignore_logic(self):
        # Should ignore
        assert _should_ignore_path("node_modules/package.json") is True
        assert _should_ignore_path("src/node_modules/foo.js") is True
        assert _should_ignore_path(".env") is True
        assert _should_ignore_path("config/.env") is True
        assert _should_ignore_path("dist/bundle.js") is True
        assert _should_ignore_path("__MACOSX/._app.py") is True

        # Should NOT ignore
        assert _should_ignore_path("src/main.py") is False
        assert _should_ignore_path("README.md") is False
        assert _should_ignore_path("src/components/Button.tsx") is False
        # Partial match check (should NOT ignore 'build_utils' just because 'build' is ignored)
        assert _should_ignore_path("build_utils/script.py") is False
