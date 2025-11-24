"""
Gemini File Search Service

This module handles interaction with the Gemini API's File Search (Semantic Retriever) capabilities.
It manages the ingestion of documents into a Corpus and querying via the LLM.
"""

import concurrent.futures
import logging
import os
from typing import Dict, Iterable, List, Optional

import google.auth
import google.auth.transport.requests
from google.ai.generativelanguage_v1beta import (CreateChunkRequest,
                                                 CreateDocumentRequest,
                                                 FileServiceClient,
                                                 GenerativeServiceClient,
                                                 RetrieverServiceClient)
from google.ai.generativelanguage_v1beta.types import (Chunk, Content, Corpus,
                                                       Document, FileSearch,
                                                       FileSearchDatastore,
                                                       GenerateContentRequest,
                                                       Part, Tool)
from google.api_core import exceptions
from google.oauth2 import service_account
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

logger = logging.getLogger(__name__)

# Constants
# Chunk size for splitting text before uploading (approx tokens or chars)
# Gemini File Search limits: 1MB per chunk, but recommended smaller for better retrieval.
CHUNK_SIZE_CHARS = 2000  # Conservative char count ~500 tokens


class GeminiFileSearchClient:
    def __init__(self):
        """Initialize the Gemini File Search Client."""
        self.project_id: Optional[str] = None
        self._setup_auth()

        # If ADC didn't yield a project, fall back to env vars
        if not self.project_id:
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

        if not self.project_id:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set and credentials do not include a project_id.")

        # Initialize clients
        self.retriever_client = RetrieverServiceClient(credentials=self.credentials)
        self.gen_client = GenerativeServiceClient(credentials=self.credentials)

        # Configuration
        self.location = os.getenv("GEMINI_LOCATION", "us-central1")

    def _setup_auth(self):
        """Set up Google Auth credentials."""
        # Try to find credentials from environment
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            self.credentials = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            # Fallback to default credentials (ADC)
            self.credentials, self.project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

    def create_corpus(self, display_name: str = "Project Analysis Corpus") -> str:
        """Create a new Corpus for storing documents."""
        corpus = Corpus(display_name=display_name)
        request = self.retriever_client.create_corpus(corpus=corpus)
        return request.name  # Returns resource name: corpora/{corpus_id}

    def get_corpus(self, corpus_name: str) -> Corpus:
        """Get an existing corpus."""
        return self.retriever_client.get_corpus(name=corpus_name)

    def delete_corpus(self, corpus_name: str):
        """Delete a corpus and all its documents."""
        request = self.retriever_client.delete_corpus(name=corpus_name, force=True)
        return request

    def _chunk_text(self, text: str) -> Iterable[str]:
        """Split text into chunks."""
        # Simple character-based chunking for now.
        # In production, use a tokenizer or sentence splitter.
        for i in range(0, len(text), CHUNK_SIZE_CHARS):
            yield text[i : i + CHUNK_SIZE_CHARS]

    @retry(
        retry=retry_if_exception_type((exceptions.ResourceExhausted, exceptions.ServiceUnavailable)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(5),
    )
    def ingest_document(self, corpus_name: str, file_path: str, text: str, metadata: Dict[str, str] = None) -> str:
        """
        Ingest a single document into the corpus.

        Args:
            corpus_name: Resource name of the corpus (corpora/...)
            file_path: Local path of the file (used as display name/ID base)
            text: Extracted text content
            metadata: Optional key-value metadata

        Returns:
            Document resource name
        """
        # Create Document
        display_name = os.path.basename(file_path)

        document = Document(display_name=display_name, custom_metadata=[])

        create_doc_req = CreateDocumentRequest(parent=corpus_name, document=document)
        doc = self.retriever_client.create_document(request=create_doc_req)

        # Create Chunks
        chunks = []
        for chunk_text in self._chunk_text(text):
            chunk = Chunk(data={"string_value": chunk_text})
            chunks.append(chunk)

        # Batch ingest chunks (up to 100 per request usually)
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            for c in batch:
                self.retriever_client.create_chunk(parent=doc.name, chunk=c)

        return doc.name

    def ingest_batch(self, corpus_name: str, documents: List[Dict[str, str]]) -> int:
        """
        Ingest multiple documents in parallel.

        Args:
            corpus_name: The target corpus resource name.
            documents: List of dicts with 'path' and 'content'.

        Returns:
            Number of successfully ingested documents.
        """
        # Use ThreadPoolExecutor for parallel IO-bound operations
        # Limit max_workers to avoid hitting rate limits too instantly
        max_workers = 5
        successful_ingestions = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map each ingestion task
            future_to_doc = {
                executor.submit(self.ingest_document, corpus_name, doc["path"], doc["content"]): doc["path"] for doc in documents
            }

            for future in concurrent.futures.as_completed(future_to_doc):
                path = future_to_doc[future]
                try:
                    future.result()
                    successful_ingestions += 1
                except Exception as e:
                    logger.warning(f"Failed to ingest {path}: {e}")

        return successful_ingestions

    def generate_content(self, corpus_name: str, prompt: str, model: str = "models/gemini-1.5-pro-001") -> str:
        """
        Generate content using the File Search tool pointing to the corpus.
        """
        datastore = FileSearchDatastore(resource_name=corpus_name)
        file_search = FileSearch(datastores=[datastore])
        tool = Tool(file_search=file_search)

        content = Content(role="user", parts=[Part(text=prompt)])

        req = GenerateContentRequest(model=model, contents=[content], tools=[tool])

        response = self.gen_client.generate_content(request=req)

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text

        return "No response generated."

    def cleanup_corpus(self, corpus_name: str):
        """Delete the corpus."""
        try:
            self.delete_corpus(corpus_name)
        except Exception as e:
            logger.error(f"Error cleaning up corpus {corpus_name}: {e}")
