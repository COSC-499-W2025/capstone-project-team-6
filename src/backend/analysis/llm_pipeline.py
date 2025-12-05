"""
LLM Analysis Pipeline
Orchestrates the analysis of projects using Gemini File Search.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, List

from backend.analysis.deep_code_analyzer import generate_comprehensive_report
from backend.analysis.project_analyzer import FileClassifier
from backend.gemini_file_search import GeminiFileSearchClient

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MAX_FILE_SIZE_BYTES = 2_000_000
IGNORED_PATH_KEYWORDS = (
    ".git/", "node_modules/", "dist/", "build/", ".next/", 
    "__pycache__/", ".venv/", "venv/", "env/", ".terraform/", 
    ".idea/", ".vscode/", "__MACOSX/"
)
IGNORED_FILE_NAMES = {".env", ".env.local", ".env.example", ".DS_Store", "package-lock.json", "yarn.lock"}
IGNORED_FILE_NAMES_LOWER = {name.lower() for name in IGNORED_FILE_NAMES}

# --- PROMPT MODULES DEFINITION ---
PROMPT_MODULES = {
    "architecture": (
        """### 2. Architectural Reasoning, Patterns & Data Flow Analysis
Act as a Senior Software Architect. Analyze the codebase for structural integrity, pattern application, and data movement. Your response must go beyond identification and provide architectural critique.
#### A. Design Pattern Efficacy & Correctness
- **Detection & Intent:** Identify design patterns (e.g., Singleton, Factory, Strategy) and deduce the developer's intent.
- **Critique:** Evaluate if the pattern is implemented correctly or if it is an 'abuse of pattern.' Does it solve the problem or introduce unnecessary complexity?
- **Side Effects:** Analyze the impact on **testability** and **coupling**. (e.g., "The Singleton here ensures unique connections but makes mocking impossible during unit tests.").
#### B. Anti-Pattern Detection & Refactoring Strategy
- **Smell Identification:** Scan for architectural smells such as God Objects, Circular Dependencies, Shotgun Surgery, or Spaghetti Code.
- **Root Cause & Solution:** For every anti-pattern found, explain the long-term maintenance risk. Provide a high-level refactoring strategy (e.g., "Refactor the monolithic UserManager into discrete services using Dependency Injection to adhere to SRP").
#### C. Cross-Module Data Flow & Serialization
- **Boundary Analysis:** Trace how data moves between architectural layers (e.g., API -> Service -> Data Access).
- **Serialization Efficiency:** Detect manual data marshalling/parsing. Highlight where this creates maintenance bottlenecks and recommend standard libraries (e.g., Pydantic, Jackson, Serde) or proper DTO usage.
- **Leakage:** Identify if domain entities are leaking into the presentation layer or vice versa.
"""
    ),
    "complexity": (
        """### 3. Algorithmic Intent, Complexity Gap & Concurrency Audit

Act as a Lead Performance Engineer. Your goal is to evaluate the *efficiency maturity* of the code. Do not just state Big-O; analyze the *gap* between the implementation and the optimal solution.

#### A. 'Big O' Gap Analysis & Data Structure Selection
- **Intent vs. Implementation:** Deduce the algorithmic intent (e.g., "Finding the intersection of two datasets").
- **The Efficiency Gap:** Contrast the *Actual Time Complexity* (e.g., O(n^2) via nested loops) against the *Theoretical Best Case* (e.g., O(n) via Hash Maps).
- **Maturity Assessment:** Critique the data structure choice. Does the use of a suboptimal structure (e.g., `List.contains` inside a loop) indicate a lack of familiarity with standard collections (like Sets), or is it a valid trade-off for memory constraints?

#### B. Concurrency & Thread-Safety Audit (Target: C++, Java, Go)
- **Shared State Analysis:** Identify mutable state shared across threads or asynchronous tasks.
- **Safety & Synchronization:** Detect specific concurrency risks such as Race Conditions, missing synchronization blocks, or the use of non-thread-safe collections (e.g., `HashMap` vs `ConcurrentHashMap`) in multi-threaded contexts.
- **Locking Strategy:** Evaluate if the locking is too coarse (bottleneck risk) or too fine (deadlock risk)."""
    ),
    "security": (
        """### 4. Security Mindset & Defensive Coding

Act as a Lead Application Security Engineer performing a manual code review. Ignore trivial findings (like regex secrets) and focus on **logical flaws**, **trust boundaries**, and **fail-safe design**.

#### A. Input Validation & Trust Boundaries
- **Trace the Data:** Identify where data enters the system (API endpoints, CLI args, file reads). Does the code treat this data as 'untrusted' by default?
- **Validation vs. Sanitization:** Critically evaluate the defense strategy. Does the code merely *check* data (validation) or actively *clean* it (sanitization) before use in sensitive operations (SQL, HTML rendering, OS commands)?
- **Deep Insight Requirement:** point out specific functions where parameters are passed blindly. (e.g., "The `update_profile` function accepts a raw dictionary and passes it directly to the ORM, allowing a user to potentially overwrite restricted fields like `is_admin`.")

#### B. Error Handling Maturity & Information Leakage
- **Pokemon Exception Handling:** Identify catch-all blocks (`except Exception: pass`). Explain the operational risk: does this hide bugs, leave the system in an inconsistent state, or force the application to run when it should crash safely?
- **Information Leakage:** Analyze what happens when things go wrong. Does the application dump raw stack traces to the user (security risk) or swallow errors entirely (debugging nightmare)?
- **Fail-Safe Logic:** Determine if the system defaults to a secure state upon failure (e.g., "If the auth check throws an error, is access denied or granted?").

#### C. Business Logic & State Manipulation
- **IDOR & Access Control:** Look beyond login checks. Can a user manipulate an ID in a request (e.g., `/user/123`) to access another user's data? Is there a verification that the `resource_owner_id` matches the `current_user_id`?
- **Logic Attacks:** Check for "impossible states". Does the code prevent negative transactions, double-spending, or modifying locked resources?"""
    ),
    "skills": (
        """### 5. Inferred Soft Skills & Technical Maturity

Act as a Technical Hiring Manager reviewing a candidate's code submission. Your goal is to infer the author's professional habits, experience level, and problem-solving approach based solely on the artifacts.

#### A. Evolution & Refactoring Capability
- **Project Genealogy:** Analyze the folder structure and file organization. Does it demonstrate a "monolithic mindset" (everything in root) or "architectural foresight" (clear separation of concerns, modular utilities)?
- **Refactoring Evidence:** Look for signs of iterative improvement, such as abstracted base classes, "v2" interfaces, or TODO comments that acknowledge technical debt (indicating self-awareness). (e.g., "The extraction of `shared_utils` implies the author recognized code duplication and refactored for maintainability.").

#### B. Testing Psychology (Quality vs. Quantity)
- **The "Happy Path" Trap:** Critique the *intent* of the tests. do they only verify that the code works under perfect conditions?
- **Defensive Testing:** Look for "Failure Mode" tests. Does the author explicitly test how the system behaves when the database is down, when inputs are null, or when APIs timeout? This indicates a Senior-level defensive mindset.
- **Test Readability:** Are test cases named descriptively (e.g., `should_throw_error_when_user_not_found`) or generically (`test_1`)? This reflects communication skills.

#### C. Language Fluency vs. Translation
- **Idiomatic Usage:** Determine if the author "thinks" in the language they are using.
  - *Python:* Are they using list comprehensions and decorators, or writing C-style loops?
  - *Java:* Are they using Streams and Optionals, or procedural logic?
- **Cognitive Load:** Evaluate how hard the code is to read. Does the author prioritize "clever" one-liners (hard to maintain) or "clean" readable logic (empathetic to future maintainers)?"""
    ),
    "domain": (
        """{
  "title": "### 6. Domain-Specific Competency",
  "context": "You have access to framework metadata extracted offline (e.g., Django, Flask, React, Spring, Express). Use that list to tailor your review. When no frameworks are detected, fall back to language-specific idioms.",
  "sections": [
    {
      "feature": "Framework Idiom Usage",
      "goal": "Determine whether the author writes idiomatic code for the detected frameworks and languages.",
      "guidance": [
        "Compare the detected frameworks from metadata_extractor.py with the code samples you inspect.",
        "Highlight mismatches between the framework's idioms and the implementation style (e.g., class-based views vs. function-based views in Django).",
        "Deep Insight Example: \\"The author uses C-style iteration (`for i in range(len(list))`) instead of Pythonic iteration (`for item in list`). This suggests a background in C/C++ or Java rather than native Python expertise.\\""
      ]
    },
    {
      "feature": "REST API Design Maturity",
      "goal": "Assess whether HTTP API endpoints follow RESTful conventions and modern backend practices.",
      "guidance": [
        "Identify verbs used in route names and match them against HTTP methods.",
        "Check for proper status codes, pagination patterns, error payloads, and versioning where relevant.",
        "Deep Insight Example: \\"The API uses POST requests for retrieving data (`/get_users`). A more experienced backend engineer would adhere to RESTful standards by using GET for retrieval and POST only for creation.\\""
      ]
    }
  ],
  "deliverable": "Produce a concise report that cites concrete files/functions and explains how well the author demonstrates domain fluency for the detected frameworks."
}"""
    )
}

def run_gemini_analysis(zip_path: Path, active_features: List[str] = None, prompt_override: Optional[str] = None) -> Dict[str, Any]:
    """Run the full analysis pipeline using Gemini."""
    
    # 1. Run the complete offline analysis pipeline
    logger.info(f"Starting offline analysis for {zip_path}")
    report = generate_comprehensive_report(zip_path)
    report.setdefault("analysis_metadata", {})

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

        # 5. Generate Prompt (Base + Features)
        offline_summary = _summarize_offline_report(report)
        
        # Base Prompt (Always runs)
        base_prompt = (
            "You are a Senior Principal Software Architect.\n"
            "You have access to the source code of a project and a pre-computed offline analysis report.\n"
            "Analyze the uploaded files to answer the following requirements:\n\n"
            "### 1. General Validation\n"
            "- Validate the findings in the offline analysis report.\n"
            "- Provide a high-level summary of the codebase.\n"
            "Suggest concrete code improvements.\n"
            "In your report, do not mention that you are a senior principal software architect.\n"
        )

        # Append Requested Modules
        additional_instructions = []
        if active_features:
            for feature in active_features:
                if feature in PROMPT_MODULES:
                    additional_instructions.append(PROMPT_MODULES[feature])
        
        # If no specific features requested, add a generic deep dive instruction
        if not additional_instructions and not prompt_override:
             additional_instructions.append(
                 "### 2. General Deep Dive\nIdentify architectural patterns, security risks, and code quality issues."
             )

        # Final Prompt Construction
        full_prompt = prompt_override or (
            f"{base_prompt}\n"
            + "\n".join(additional_instructions)
            + "\n\n### Output Format\n"
            "Structure your response with clear headings corresponding to the sections above. Use Markdown.\n"
            f"\nOffline Analysis Context:\n{offline_summary}"
        )

        logger.info("Generating analysis with Gemini...")
        response_text = client.generate_content(uploaded_files_refs, full_prompt)

        report["llm_summary"] = response_text
        report["analysis_metadata"]["gemini_file_count"] = len(uploaded_files_refs)
        report["analysis_mode"] = f"Base + {', '.join(active_features)}" if active_features else "Standard"

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
    if not report: return "No offline analysis available."
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
    
    if filename.lower() in IGNORED_FILE_NAMES_LOWER:
        return True

    if filename.startswith("._"):
        return True
        
    for keyword in IGNORED_PATH_KEYWORDS:
        if keyword in normalized:
            return True
            
    return False

if __name__ == "__main__":
    import argparse
    import sys
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
    parser = argparse.ArgumentParser(description="Run Gemini Analysis on a ZIP file.")
    parser.add_argument("zip_path", type=Path, help="Path to the ZIP file to analyze")
    parser.add_argument("--prompt", type=str, help="Optional custom prompt (overrides all)", default=None)
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted report")
    
    # Feature Flags
    parser.add_argument("--architecture", action="store_true", help="Deep analysis of patterns and anti-patterns")
    parser.add_argument("--complexity", action="store_true", help="Algorithmic intent and Big O gap analysis")
    parser.add_argument("--security", action="store_true", help="Logic-based security and defensive coding")
    parser.add_argument("--skills", action="store_true", help="Infer soft skills and testing maturity")
    parser.add_argument("--domain", action="store_true", help="Domain-specific best practices")
    parser.add_argument("--all", action="store_true", help="Enable all deep analysis features")

    args = parser.parse_args()

    # Collect active features
    active_features = []
    if args.all:
        active_features = ["architecture", "complexity", "security", "skills", "domain"]
    else:
        if args.architecture: active_features.append("architecture")
        if args.complexity: active_features.append("complexity")
        if args.security: active_features.append("security")
        if args.skills: active_features.append("skills")
        if args.domain: active_features.append("domain")

    if not args.zip_path.exists():
        print(f"Error: File not found: {args.zip_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Run the analysis with selected features
        report = run_gemini_analysis(
            args.zip_path, 
            active_features=active_features,
            prompt_override=args.prompt
        )

        if args.json:
            print(json.dumps(report, indent=2, default=str))
            sys.exit(0)

        # --- RICH FORMATTING ---
        console = Console()
        console.print()
        console.print(Panel.fit("[bold white]Gemini Deep Code Analysis[/bold white]", style="blue"))
        console.print()

        meta = report.get("analysis_metadata", {})
        summary = report.get("summary", {})
        project_name = report.get("projects", [{}])[0].get("project_name", "Unknown")

        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column(justify="right")
        
        stats_table = Table(box=box.SIMPLE, show_header=False)
        stats_table.add_column("Key", style="cyan")
        stats_table.add_column("Value", style="white")
        
        stats_table.add_row("Project Name", project_name)
        stats_table.add_row("Primary Language", ", ".join(summary.get("languages_used", ["N/A"])))
        stats_table.add_row("Total Files", str(summary.get("total_files", 0)))
        stats_table.add_row("Gemini Files", str(meta.get("gemini_file_count", 0)))
        stats_table.add_row("Analysis Mode", report.get("analysis_mode", "Standard"))

        console.print(Panel(stats_table, title="[bold]Project Statistics[/bold]", border_style="cyan"))

        llm_text = report.get("llm_summary", "No analysis generated.")
        md = Markdown(llm_text)
        
        console.print(Panel(
            md, 
            title="[bold green]AI-Powered Insights[/bold green]", 
            border_style="green", 
            padding=(1, 2)
        ))
        
        if report.get("llm_error"):
            console.print(Panel(
                f"[bold red]Error during analysis:[/bold red]\n{report['llm_error']}", 
                title="System Warnings", 
                border_style="red"
            ))

    except Exception as e:
        console = Console()
        console.print_exception()
        sys.exit(1)
