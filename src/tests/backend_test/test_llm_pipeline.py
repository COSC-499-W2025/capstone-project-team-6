"""
Tests for the LLM Pipeline.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Mock missing Google dependencies globally
module_mock = MagicMock()
sys.modules["google"] = module_mock
sys.modules["google.auth"] = module_mock
sys.modules["google.ai"] = module_mock
sys.modules["google.ai.generativelanguage_v1beta"] = module_mock
sys.modules["google.ai.generativelanguage_v1beta.types"] = module_mock
sys.modules["google.oauth2"] = module_mock
sys.modules["google.api_core"] = module_mock

# Adjust path
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.analysis.llm_pipeline import _should_ignore_path, run_gemini_analysis

class TestLLMPipeline:
    
    @pytest.fixture
    def mock_gemini_client(self):
        with patch("backend.analysis.llm_pipeline.GeminiFileSearchClient") as MockClient:
            client_instance = MockClient.return_value
            client_instance.create_corpus.return_value = "corpora/test-uuid"
            client_instance.generate_content.return_value = "Mock LLM Summary"
            client_instance.ingest_batch.return_value = 2
            yield client_instance

    @pytest.fixture
    def mock_metadata_extractor(self):
        with patch("backend.analysis.llm_pipeline.MetadataExtractor") as MockExtractor:
            extractor_instance = MockExtractor.return_value
            extractor_instance.__enter__.return_value = extractor_instance
            
            extractor_instance.generate_report.return_value = {
                "analysis_metadata": {"zip_file": "test.zip", "analysis_timestamp": "2023-01-01"},
                "projects": [{"project_name": "test-project"}],
                "summary": {}
            }
            yield extractor_instance
            
    @pytest.fixture
    def mock_session(self):
        with patch("backend.analysis.llm_pipeline.get_session") as mock_get_session:
            mock_get_session.return_value = {"username": "testuser"}
            yield mock_get_session

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
                    "other": []
                }
            }
            
            mock_zip = MagicMock()
            # Configure read to return content when path is accessed
            mock_zip.read.return_value = b"file content"
            classifier_instance.zip_file = mock_zip
            
            yield classifier_instance

    def test_run_gemini_analysis_success(self, mock_gemini_client, mock_metadata_extractor, mock_file_classifier, mock_session):
        # Patch FileClassifier constructor where it is used in pipeline
        with patch("backend.analysis.llm_pipeline.FileClassifier", return_value=mock_file_classifier):
            zip_path = Path("test.zip")
            
            # Reset global cache for tests
            from backend.analysis import llm_pipeline
            llm_pipeline._SESSION_CORPORA = {}
            
            report = run_gemini_analysis(zip_path)
            
            assert report["llm_summary"] == "Mock LLM Summary"
            assert report["analysis_metadata"]["gemini_corpus"] == "corpora/test-uuid"
            
            # Verify session reuse
            assert llm_pipeline._SESSION_CORPORA["testuser"] == "corpora/test-uuid"
            
            # Verify NO cleanup because user is logged in
            mock_gemini_client.cleanup_corpus.assert_not_called()

    def test_run_gemini_analysis_cleanup_anonymous(self, mock_gemini_client, mock_metadata_extractor, mock_file_classifier):
        # Patch FileClassifier
        with patch("backend.analysis.llm_pipeline.FileClassifier", return_value=mock_file_classifier):
            # Simulate anonymous user
            with patch("backend.analysis.llm_pipeline.get_session", return_value={}):
                run_gemini_analysis(Path("test.zip"))
                # Should cleanup
                mock_gemini_client.cleanup_corpus.assert_called_once()

    def test_ignore_logic(self):
        # Should ignore
        assert _should_ignore_path("node_modules/package.json") is True
        assert _should_ignore_path("src/node_modules/foo.js") is True
        assert _should_ignore_path(".env") is True
        assert _should_ignore_path("config/.env") is True
        assert _should_ignore_path("dist/bundle.js") is True
        
        # Should NOT ignore
        assert _should_ignore_path("src/main.py") is False
        assert _should_ignore_path("README.md") is False
        assert _should_ignore_path("src/components/Button.tsx") is False
        # Partial match check (should NOT ignore 'build_utils' just because 'build' is ignored)
        assert _should_ignore_path("build_utils/script.py") is False
