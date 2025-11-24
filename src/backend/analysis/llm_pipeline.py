"""
LLM Analysis Pipeline
Orchestrates the analysis of projects using Gemini File Search.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from backend.analysis.metadata_extractor import MetadataExtractor
from backend.analysis.project_analyzer import FileClassifier
from backend.gemini_file_search import GeminiFileSearchClient
from backend.session import get_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MAX_FILE_SIZE_BYTES = 1_000_000
IGNORED_PATH_KEYWORDS: Sequence[str] = (
    ".git/",
    "node_modules/",
    "dist/",
    "build/",
    ".next/",
    "__pycache__/",
    ".venv/",
    "venv/",
    "env/",
    ".terraform/",
)
IGNORED_FILE_NAMES = {".env", ".env.local", ".env.example", ".DS_Store"}
IGNORED_FILE_NAMES_LOWER = {name.lower() for name in IGNORED_FILE_NAMES}

# Global cache for session-based corpora (in-memory for now, ideally redundant with DB)
# Key: session_username, Value: corpus_name
_SESSION_CORPORA: Dict[str, str] = {}


def run_gemini_analysis(zip_path: Path, prompt_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full analysis pipeline using Gemini.

    Args:
        zip_path: Path to the uploaded ZIP file.
        prompt_override: Optional custom prompt.

    Returns:
        The complete analysis payload including LLM results.
    """
    # 1. Run standard metadata extraction (Non-LLM)
    logger.info(f"Starting metadata extraction for {zip_path}")
    with MetadataExtractor(zip_path) as extractor:
        report = extractor.generate_report()

    # 2. Initialize Gemini Client
    try:
        client = GeminiFileSearchClient()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini Client: {e}")
        report["llm_error"] = str(e)
        return report

    # 3. Session-based Corpus Management
    session = get_session()
    username = session.get("username")

    # If user is logged in, try to reuse their corpus
    corpus_name = None
    if username and username in _SESSION_CORPORA:
        corpus_name = _SESSION_CORPORA[username]
        logger.info(f"Reusing session corpus for user {username}: {corpus_name}")
        # Check if it still exists
        try:
            client.get_corpus(corpus_name)
        except Exception:
            logger.warning("Session corpus not found, creating new one.")
            corpus_name = None

    if not corpus_name:
        analysis_id = str(uuid.uuid4())
        display_name = f"Session Corpus {username}" if username else f"Analysis {analysis_id}"
        try:
            corpus_name = client.create_corpus(display_name=display_name)
            logger.info(f"Created corpus: {corpus_name}")
            if username:
                _SESSION_CORPORA[username] = corpus_name
        except Exception as e:
            logger.error(f"Failed to create corpus: {e}")
            report["llm_error"] = str(e)
            return report

    try:
        # 4. Prepare Files for Ingestion
        files_to_ingest = []
        with FileClassifier(zip_path) as classifier:
            classification = classifier.classify_project("")
            files_section = classification.get("files", {})

            # Collect all categories
            all_file_infos = []
            for files in files_section.get("code", {}).values():
                all_file_infos.extend(files)
            all_file_infos.extend(files_section.get("configs", []))
            all_file_infos.extend(files_section.get("docs", []))
            all_file_infos.extend(files_section.get("tests", []))
            all_file_infos.extend(files_section.get("other", []))

            with classifier.zip_file as zf:
                for file_info in all_file_infos:
                    path = file_info["path"]

                    if _should_ignore_path(path):
                        continue

                    try:
                        # Read content
                        content_bytes = zf.read(path)

                        # Truncate if too large instead of skipping
                        if len(content_bytes) > DEFAULT_MAX_FILE_SIZE_BYTES:
                            logger.warning(f"Truncating large file {path} ({len(content_bytes)} bytes)")
                            content_bytes = content_bytes[:DEFAULT_MAX_FILE_SIZE_BYTES]

                        content = content_bytes.decode("utf-8", errors="ignore")

                        if not content.strip():
                            continue

                        files_to_ingest.append({"path": path, "content": content})
                    except Exception as e:
                        logger.warning(f"Failed to read {path}: {e}")

        total_files = len(files_to_ingest)
        logger.info(f"Found {total_files} relevant files to ingest.")

        # 5. Parallel Ingestion
        successful_count = client.ingest_batch(corpus_name, files_to_ingest)
        logger.info(f"Successfully ingested {successful_count}/{total_files} files.")

        # 6. Generate Content
        default_prompt = (
            "Analyze the provided codebase. Identify the main projects, their architecture, "
            "key technologies used, and any potential code quality or security issues. "
            "Provide a summary of the implementation."
        )
        prompt = prompt_override or default_prompt

        logger.info("Generating analysis...")
        response_text = client.generate_content(corpus_name, prompt)

        # 7. Attach to report
        report["llm_summary"] = response_text
        report["analysis_metadata"]["gemini_corpus"] = corpus_name
        report["analysis_metadata"]["ingested_files_count"] = successful_count

    except Exception as e:
        logger.error(f"Error during Gemini analysis: {e}")
        report["llm_error"] = str(e)

    finally:
        # Cleanup logic changes:
        # If persistent session, DO NOT delete corpus.
        # If ephemeral (no username), delete it.
        if not username:
            logger.info("Cleaning up ephemeral corpus...")
            try:
                client.cleanup_corpus(corpus_name)
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
        else:
            logger.info(f"Persisting corpus {corpus_name} for user session.")

    return report


def _should_ignore_path(path: str) -> bool:
    """Check if path should be ignored using strict directory matching."""
    # Normalize path to forward slashes
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")

    # Check filename (last part)
    filename = parts[-1].lower()
    if filename in IGNORED_FILE_NAMES_LOWER:
        return True

    # Check directory parts
    # We look for exact directory name matches against keywords
    # Remove trailing slashes from keywords for comparison
    ignored_dirs = {k.rstrip("/") for k in IGNORED_PATH_KEYWORDS}

    # Check if any part of the path matches an ignored directory name
    for part in parts[:-1]:  # Don't check filename against dir list
        if part in ignored_dirs:
            return True

    return False


if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Run Gemini Analysis on a ZIP file.")
    parser.add_argument("zip_path", type=Path, help="Path to the ZIP file to analyze")
    parser.add_argument("--prompt", type=str, help="Optional custom prompt", default=None)

    args = parser.parse_args()

    if not args.zip_path.exists():
        print(f"Error: File not found: {args.zip_path}", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_gemini_analysis(args.zip_path, prompt_override=args.prompt)
        # Use default=str to handle non-serializable objects like Path or datetime
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"Analysis failed: {e}", file=sys.stderr)
        sys.exit(1)
