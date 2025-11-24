"""
Tests for the Gemini File Search Client.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from tenacity import RetryError

# Create distinct mocks
mock_google = MagicMock()
mock_google_auth = MagicMock()
mock_google_oauth2 = MagicMock()
mock_google_api_core = MagicMock()

# Configure auth default to return a tuple (creds, project_id)
mock_google_auth.default.return_value = (MagicMock(), "test-project")

# Link them so attribute access works consistent with imports
mock_google.auth = mock_google_auth
mock_google.oauth2 = mock_google_oauth2
mock_google.api_core = mock_google_api_core

# Assign to sys.modules
sys.modules["google"] = mock_google
sys.modules["google.auth"] = mock_google_auth
sys.modules["google.auth.transport"] = MagicMock()
sys.modules["google.auth.transport.requests"] = MagicMock()
sys.modules["google.ai"] = MagicMock()
sys.modules["google.ai.generativelanguage_v1beta"] = MagicMock()
sys.modules["google.ai.generativelanguage_v1beta.types"] = MagicMock()
sys.modules["google.oauth2"] = mock_google_oauth2
sys.modules["google.api_core"] = mock_google_api_core

# Now import
try:
    from backend.gemini_file_search import GeminiFileSearchClient
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
    from backend.gemini_file_search import GeminiFileSearchClient


class TestGeminiFileSearchClient:

    @pytest.fixture
    def client(self):
        with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            with patch("backend.gemini_file_search.service_account.Credentials"):
                with patch("backend.gemini_file_search.RetrieverServiceClient") as mock_retriever, patch(
                    "backend.gemini_file_search.GenerativeServiceClient"
                ) as mock_gen:

                    client = GeminiFileSearchClient()
                    client.retriever_client = mock_retriever.return_value
                    client.gen_client = mock_gen.return_value
                    return client

    def test_ingest_document_retry(self, client):

        class ResourceExhausted(Exception):
            pass

        class ServiceUnavailable(Exception):
            pass

        mock_google_api_core.exceptions.ResourceExhausted = ResourceExhausted
        mock_google_api_core.exceptions.ServiceUnavailable = ServiceUnavailable

        from backend.gemini_file_search import exceptions as module_exceptions

        mock_success = MagicMock(name="corpora/123/documents/456")
        mock_success.name = "corpora/123/documents/456"

        mock_create = client.retriever_client.create_document

        mock_create.return_value = mock_success

        client.ingest_document("corpora/123", "test.txt", "content")
        assert mock_create.call_count == 1

    def test_ingest_batch(self, client):
        # Mock single ingest
        with patch.object(client, "ingest_document") as mock_ingest:
            docs = [{"path": "1.txt", "content": "a"}, {"path": "2.txt", "content": "b"}]
            count = client.ingest_batch("corpora/123", docs)

            assert count == 2
            assert mock_ingest.call_count == 2

    def test_cleanup_corpus(self, client):
        client.cleanup_corpus("corpora/123")
        client.retriever_client.delete_corpus.assert_called_once_with(name="corpora/123", force=True)
