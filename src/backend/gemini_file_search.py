"""
Gemini File Search Service

This module handles interaction with the Gemini API (v1.5+).
It manages the upload of documents to the File API and Long Context Generation.
"""

import logging
import os
import tempfile
import time
from typing import Dict, List, Any, Callable, Optional

# New SDK import
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiFileSearchClient:
    def __init__(self):
        """Initialize the Gemini Client (Google Gen AI SDK)."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GEMINI_LOCATION", "us-central1")

        # Initialize Client based on available credentials
        if self.api_key:
            # AI Studio Mode (API Key)
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-2.5-flash"
            logger.info("Initialized Gemini Client in AI Studio mode.")
        elif self.project_id:
            # Vertex AI Mode (ADC / Service Account)
            self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
            self.model_name = "gemini-1.5-pro-002"
            logger.info(f"Initialized Gemini Client in Vertex AI mode ({self.project_id}).")
        else:
            raise ValueError("No valid credentials found. Set GOOGLE_API_KEY or GOOGLE_CLOUD_PROJECT.")

    def upload_batch(
        self,
        files_data: List[Dict[str, str]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[types.File]:
        """
        Uploads a batch of files to the Gemini File API.

        Args:
            files_data: List of dicts containing 'path' (str) and 'content' (str).
            progress_callback: Optional callback(current, total, description) for progress updates.

        Returns:
            List of active Gemini File objects ready for generation.
        """
        uploaded_files = []
        total_files = len(files_data)
        # We estimate total steps as 2 * total_files (upload + process)
        total_steps = total_files * 2
        current_step = 0

        # The File API requires physical files, so we dump content to temp storage first
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, file_dat in enumerate(files_data):
                try:
                    rel_path = file_dat["path"]
                    content = file_dat["content"]

                    # Create a safe filename in the temp dir
                    safe_filename = os.path.basename(rel_path)
                    temp_file_path = os.path.join(temp_dir, safe_filename)

                    with open(temp_file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    msg = f"Uploading {safe_filename}..."
                    if progress_callback:
                        progress_callback(current_step, total_steps, msg)
                    else:
                        logger.info(msg)

                    # Upload to Gemini
                    # Note: We pass the 'file' argument (path to file), NOT 'path'
                    uploaded_file = self.client.files.upload(
                        file=temp_file_path,
                        config=types.UploadFileConfig(display_name=rel_path, mime_type="text/plain"),
                    )
                    uploaded_files.append(uploaded_file)

                except Exception as e:
                    logger.error(f"Failed to upload {file_dat.get('path')}: {e}")

                current_step += 1

        # Wait for files to transition from PROCESSING to ACTIVE
        if not uploaded_files:
            return []

        msg = "Waiting for remote file processing..."
        if progress_callback:
            progress_callback(current_step, total_steps, msg)
        else:
            logger.info(msg)

        active_files = []

        # Simple polling mechanism
        for f in uploaded_files:
            try:
                current_file = self.client.files.get(name=f.name)

                # Poll until ready or failed
                while current_file.state.name == "PROCESSING":
                    if progress_callback:
                        progress_callback(
                            current_step, total_steps, f"Processing {f.display_name}..."
                        )
                    time.sleep(1)
                    current_file = self.client.files.get(name=f.name)

                if current_file.state.name == "ACTIVE":
                    active_files.append(current_file)
                else:
                    logger.error(f"File {f.display_name} failed processing: {current_file.state.name}")
            except Exception as e:
                logger.error(f"Error checking state for {f.name}: {e}")

            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, "Processing files...")

        return active_files

    def generate_content(self, files: List[types.File], prompt: str) -> str:
        """
        Generate content using the uploaded files as context (Long Context).
        """
        if not files:
            return "No files were successfully uploaded for analysis."

        try:
            # Pass the prompt and the file objects directly to the model
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, *files],
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Lower temperature for analytical precision
                ),
            )

            if response.text:
                return response.text
            return "No text response generated."

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error executing analysis: {str(e)}"

    def cleanup_files(self, files: List[types.File]):
        """Delete files from the Gemini Cloud storage to avoid storage costs."""
        for f in files:
            try:
                self.client.files.delete(name=f.name)
                logger.debug(f"Deleted remote file {f.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {f.name}: {e}")
