"""
LLM Analysis Pipeline
Orchestrates the analysis of projects using Gemini File Search.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .metadata_extractor import MetadataExtractor
    from .project_analyzer import FileClassifier
except ImportError:
    from backend.analysis.metadata_extractor import MetadataExtractor
    from backend.analysis.project_analyzer import FileClassifier

try:
    from ..gemini_file_search import GeminiFileSearchClient
except ImportError:
    try:
        from backend.gemini_file_search import GeminiFileSearchClient
    except ImportError:
        GeminiFileSearchClient = None

try:
    from ..session import get_session
except ImportError:
    try:
        from backend.session import get_session
    except ImportError:
        from session import get_session
from dotenv import load_dotenv

from backend.analysis.deep_code_analyzer import generate_comprehensive_report
from backend.analysis.project_analyzer import FileClassifier
from backend.gemini_file_search import GeminiFileSearchClient

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MAX_FILE_SIZE_BYTES = 2_000_000
IGNORED_PATH_KEYWORDS = (
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
    ".idea/",
    ".vscode/",
    "__MACOSX/",  # Added MACOSX ignore
)
IGNORED_FILE_NAMES = {".env", ".env.local", ".env.example", ".DS_Store", "package-lock.json", "yarn.lock"}
IGNORED_FILE_NAMES_LOWER = {name.lower() for name in IGNORED_FILE_NAMES}


def run_gemini_analysis(zip_path: Path, prompt_override: Optional[str] = None) -> Dict[str, Any]:
    """Run the full analysis pipeline using Gemini."""
    from datetime import datetime

    # 1. Run the complete offline analysis pipeline (Python/Java)
    logger.info(f"Starting offline analysis for {zip_path}")
    report = generate_comprehensive_report(zip_path)
    report.setdefault("analysis_metadata", {})

    # Add C++ and C analysis to match non-LLM pipeline
    for i, project in enumerate(report["projects"]):
        project_path = project.get("project_path", "")

        # C++ Analysis
        if "cpp" in project.get("languages", {}):
            try:
                from .cpp_oop_analyzer import analyze_cpp_project
                cpp_analysis = analyze_cpp_project(zip_path, project_path)
                report["projects"][i]["cpp_oop_analysis"] = cpp_analysis["cpp_oop_analysis"]
            except ImportError:
                report["projects"][i]["cpp_oop_analysis"] = {
                    "error": "C++ analyzer not available (libclang not installed)",
                    "total_classes": 0,
                }
            except Exception as e:
                report["projects"][i]["cpp_oop_analysis"] = {"error": str(e), "total_classes": 0}

        # C Analysis (note: .c files are classified as cpp in project_analyzer)
        if "cpp" in project.get("languages", {}) or "c" in project.get("languages", {}):
            try:
                from .c_oop_analyzer import analyze_c_project
                c_analysis = analyze_c_project(zip_path, project_path)
                # Only add if we found C-style code
                if c_analysis["c_oop_analysis"].get("total_structs", 0) > 0:
                    report["projects"][i]["c_oop_analysis"] = c_analysis["c_oop_analysis"]
            except ImportError:
                pass  # C analyzer optional
            except Exception as e:
                pass  # Silently skip if no C code found

    # Update metadata with timestamp
    report["analysis_metadata"].update({
        "zip_file": str(zip_path.absolute()),
        "analysis_timestamp": datetime.now().isoformat(),
        "total_projects": len(report["projects"]),
    })

    # Check if Gemini client is available
    if GeminiFileSearchClient is None:
        error_msg = "Google Cloud AI Platform libraries not installed. Install with: pip install google-cloud-aiplatform google-auth google-generativeai"
        logger.error(error_msg)
        report["llm_error"] = error_msg
        return report

    # 2. Initialize Gemini Client
    try:
        client = GeminiFileSearchClient()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini Client: {e}")
        report["llm_error"] = f"Client Initialization Error: {str(e)}"
        return report

    uploaded_files_refs = []

    try:
        # 3. Prepare Files for Ingestion
        files_to_ingest = []

        with FileClassifier(zip_path) as classifier:
            classification = classifier.classify_project("")
            files_section = classification.get("files", {})

            all_file_infos = []
            for category in ["configs", "docs", "tests", "other"]:
                all_file_infos.extend(files_section.get(category, []))
            for files in files_section.get("code", {}).values():
                all_file_infos.extend(files)

            with classifier.zip_file as zf:
                for file_info in all_file_infos:
                    path = file_info["path"]
                    if _should_ignore_path(path):
                        continue

                    try:
                        content_bytes = zf.read(path)
                        if len(content_bytes) > DEFAULT_MAX_FILE_SIZE_BYTES:
                            logger.warning(f"Skipping large file {path} ({len(content_bytes)} bytes)")
                            continue

                        content = content_bytes.decode("utf-8", errors="ignore")
                        if not content.strip():
                            continue

                        files_to_ingest.append({"path": path, "content": content})
                    except Exception as e:
                        logger.warning(f"Failed to read {path}: {e}")

        # Add offline analysis
        offline_doc = _build_offline_analysis_document(report)
        files_to_ingest.append(offline_doc)

        logger.info(f"Prepared {len(files_to_ingest)} files for Gemini ingestion.")

        # 4. Upload Files
        uploaded_files_refs = client.upload_batch(files_to_ingest)
        logger.info(f"Successfully uploaded {len(uploaded_files_refs)} files to Gemini.")

        # 5. Generate Content
        offline_summary = _summarize_offline_report(report)
        default_prompt = (
            "You are a Senior Principal Software Architect.\n"
            "You have access to the source code of a project and a pre-computed offline analysis report.\n"
            "Analyze the uploaded files to answer the following requirements:\n"
            "1. Validate the findings in the offline analysis report.\n"
            "2. Identify architectural patterns, security risks, and code quality issues.\n"
            "3. Suggest concrete code improvements.\n\n"
            f"Offline Analysis Context:\n{offline_summary}"
        )
        prompt = prompt_override or default_prompt

        logger.info("Generating analysis with Gemini...")
        response_text = client.generate_content(uploaded_files_refs, prompt)

        report["llm_summary"] = response_text
        report["analysis_metadata"]["gemini_file_count"] = len(uploaded_files_refs)

    except Exception as e:
        logger.error(f"Error during Gemini analysis: {e}")
        report["llm_error"] = str(e)

    finally:
        if uploaded_files_refs:
            logger.info("Cleaning up remote files...")
            client.cleanup_files(uploaded_files_refs)

    return report


def _build_offline_analysis_document(report: Dict[str, Any]) -> Dict[str, str]:
    serialized = json.dumps(report, indent=2, ensure_ascii=False, default=str)
    return {"path": "_offline_analysis.json", "content": serialized}


def _summarize_offline_report(report: Dict[str, Any]) -> str:
    if not report:
        return "No offline analysis available."
    summary = report.get("summary", {})
    projects = report.get("projects", [])
    lines = [f"Total Files: {summary.get('total_files', 0)}"]
    lines.append(f"Languages: {', '.join(summary.get('languages_used', []))}")
    for p in projects[:3]:
        lines.append(f"- Project: {p.get('project_name')} ({p.get('primary_language')})")
    return "\n".join(lines)


def _should_ignore_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    filename = parts[-1]

    # FILTER 1: Strict filename match
    if filename.lower() in IGNORED_FILE_NAMES_LOWER:
        return True

    # FILTER 2: Mac resource fork files (._filename)
    if filename.startswith("._"):
        return True

    # FILTER 3: Directory keywords
    for keyword in IGNORED_PATH_KEYWORDS:
        if keyword in normalized:
            return True

    return False


if __name__ == "__main__":
    import argparse
    import sys

    from rich import box
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table

    parser = argparse.ArgumentParser(description="Run Gemini Analysis on a ZIP file.")
    parser.add_argument("zip_path", type=Path, help="Path to the ZIP file to analyze")
    parser.add_argument("--prompt", type=str, help="Optional custom prompt", default=None)
    # Add a flag to still output JSON if you need it for piping
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted report")

    args = parser.parse_args()

    if not args.zip_path.exists():
        print(f"Error: File not found: {args.zip_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Run the analysis
        report = run_gemini_analysis(args.zip_path, prompt_override=args.prompt)

        # If user requested raw JSON (e.g., for piping to another tool)
        if args.json:
            print(json.dumps(report, indent=2, default=str))
            sys.exit(0)

        # --- RICH FORMATTING START ---
        console = Console()

        # 1. Title Panel
        console.print()
        console.print(Panel.fit("[bold white]Gemini Deep Code Analysis[/bold white]", style="blue"))
        console.print()

        # 2. Metadata Table
        # Extract basic info
        meta = report.get("analysis_metadata", {})
        summary = report.get("summary", {})
        project_name = "Unknown"
        if report.get("projects"):
            project_name = report["projects"][0].get("project_name", "Unknown")

        # Create a grid/table for metrics
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column(justify="right")

        # Inner table for stats
        stats_table = Table(box=box.SIMPLE, show_header=False)
        stats_table.add_column("Key", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Project Name", project_name)
        stats_table.add_row("Primary Language", ", ".join(summary.get("languages_used", ["N/A"])))
        stats_table.add_row("Total Files", str(summary.get("total_files", 0)))
        stats_table.add_row("Gemini Files Processed", str(meta.get("gemini_file_count", 0)))
        stats_table.add_row("Analysis Mode", report.get("analysis_mode", "General Audit"))

        console.print(Panel(stats_table, title="[bold]Project Statistics[/bold]", border_style="cyan"))

        # 3. The LLM Report (Markdown Rendering)
        llm_text = report.get("llm_summary", "No analysis generated.")

        # Render the markdown content
        md = Markdown(llm_text)

        console.print(Panel(md, title="[bold green]Gemini Insights[/bold green]", border_style="green", padding=(1, 2)))

        # 4. Error Handling Display
        if report.get("llm_error"):
            console.print(
                Panel(
                    f"[bold red]Error during analysis:[/bold red]\n{report['llm_error']}",
                    title="System Warnings",
                    border_style="red",
                )
            )

    except Exception as e:
        console = Console()
        console.print_exception()
        sys.exit(1)
