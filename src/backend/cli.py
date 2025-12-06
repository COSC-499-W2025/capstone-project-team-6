#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from . import (Folder_traversal_fs, MDAShell, UserAlreadyExistsError,
               authenticate_user, create_user, initialize)
from .analysis.deep_code_analyzer import generate_comprehensive_report
from .analysis.document_analyzer import DocumentAnalysis, analyze_document
from .analysis_database import init_db
from .consent import ask_for_consent

# Avoid importing heavy optional dependencies at module import time


def handle_first_time_consent(username: str) -> bool:
    """Handle consent for first-time users.

    Args:
        username: The username to handle consent for

    Returns:
        bool: True if consent was given or already exists, False if denied
    """
    from .database import check_user_consent, save_user_consent

    # Check if user has already given consent
    if check_user_consent(username):
        return True

    print("\nFirst-time Login - Consent Required")
    print("--------------------------------------")

    if ask_for_consent():
        save_user_consent(username, True)
        return True
    else:
        save_user_consent(username, False)
        return False


def login(username: str, password: str) -> bool:
    """Attempt to login with the given credentials.

    Args:
        username: The username to login with
        password: The password to login with

    Returns:
        bool: True if login successful, False otherwise
    """
    return authenticate_user(username, password)


def signup(username: str, password: str) -> bool:
    """Register a new user.

    Args:
        username: The username to register
        password: The password to use

    Returns:
        bool: True if signup and consent successful, False otherwise
    """
    try:
        create_user(username, password)

        print("\nAccount created successfully!")
        print("\nBefore continuing, please review our consent form:")

        # Show consent form for new users
        if ask_for_consent():
            from .database import save_user_consent

            save_user_consent(username, True)
            print("\nThank you for providing consent!")
            return True
        else:
            from .database import save_user_consent

            save_user_consent(username, False)
            print("\nYou have not provided consent. Some features will be limited.")
            print("You can update your consent later using 'mda consent --update'")
            return False

    except UserAlreadyExistsError:
        return False


def create_temp_zip(directory: Path) -> Path:
    """Create a temporary ZIP file from a directory.

    Args:
        directory: Path to the directory to zip

    Returns:
        Path: Path to the temporary ZIP file
    """
    # Create a temporary file with .zip extension
    temp_fd, temp_path = tempfile.mkstemp(suffix=".zip")
    import os

    os.close(temp_fd)  # Close the file descriptor

    temp_zip = Path(temp_path)

    # Create ZIP file
    with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through directory and add all files
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Calculate the archive name (relative path from directory)
                arcname = file_path.relative_to(directory.parent)
                zipf.write(file_path, arcname)

    return temp_zip


def analyze_folder(path: Path) -> dict:
    """Analyze a folder or ZIP file using the comprehensive analysis pipeline.

    Args:
        path: Path to the folder or ZIP file to analyze

    Returns:
        dict: Comprehensive analysis results from the pipeline

    Raises:
        ValueError: If path is neither a directory nor a ZIP file
        zipfile.BadZipFile: If ZIP file is corrupted
    """
    import tempfile
    import zipfile as zipfile_module
    from datetime import datetime

    temp_zip = None
    temp_extract_dir = None
    original_path = path  # Store original path before any temp zip creation
    try:
        # Determine if we need to create a ZIP
        if path.is_dir():
            print(f"Creating temporary archive...")
            temp_zip = create_temp_zip(path)
            zip_path = temp_zip
            # For directories, we can analyze git directly
            analysis_dir = path
        elif path.is_file() and path.suffix.lower() == ".zip":
            zip_path = path
            # For ZIPs, we need to extract to analyze git
            analysis_dir = None  # Will extract if needed
        else:
            raise ValueError(f"Path must be a directory or ZIP file: {path}")

        # Run comprehensive analysis (Python/Java)
        print(f"Running analysis pipeline...")
        report = generate_comprehensive_report(zip_path)

        # Add C++ and C analysis to the report
        for i, project in enumerate(report["projects"]):
            project_path = project.get("project_path", "")

            # C++ Analysis
            if "cpp" in project.get("languages", {}):
                try:
                    from .analysis.cpp_oop_analyzer import analyze_cpp_project

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
            # So we check for cpp language and run C analyzer too
            if "cpp" in project.get("languages", {}) or "c" in project.get("languages", {}):
                try:
                    from .analysis.c_oop_analyzer import analyze_c_project

                    c_analysis = analyze_c_project(zip_path, project_path)
                    # Only add if we found C-style code
                    if c_analysis["c_oop_analysis"].get("total_structs", 0) > 0:
                        report["projects"][i]["c_oop_analysis"] = c_analysis["c_oop_analysis"]
                except ImportError:
                    pass  # C analyzer optional
                except Exception as e:
                    pass  # Silently skip if no C code found

        # Git Analysis
        # For directories, analyze directly; for ZIPs, extract if .git exists
        if analysis_dir and (analysis_dir / ".git").exists():
            # Direct directory with .git
            try:
                from .analysis.git_analysis import analyze_project

                git_result = analyze_project(analysis_dir, export_to_file=False)
                # Add git analysis to first project (assuming single project)
                if report["projects"]:
                    report["projects"][0]["git_analysis"] = git_result.to_dict()
            except Exception as e:
                print(f"Warning: Git analysis failed: {e}")
        elif not analysis_dir:
            # ZIP file - check if it contains .git
            try:
                with zipfile_module.ZipFile(zip_path, "r") as zf:
                    git_files = [f for f in zf.namelist() if ".git/" in f]
                    if git_files:
                        # Extract to temp directory
                        temp_extract_dir = tempfile.mkdtemp()
                        zf.extractall(temp_extract_dir)

                        # Find the project root (where .git is)
                        git_root = Path(temp_extract_dir)
                        for item in git_root.rglob(".git"):
                            if item.is_dir():
                                git_root = item.parent
                                break

                        # Run git analysis
                        from .analysis.git_analysis import analyze_project

                        git_result = analyze_project(git_root, export_to_file=False)
                        if report["projects"]:
                            report["projects"][0]["git_analysis"] = git_result.to_dict()
            except Exception as e:
                print(f"Warning: Git analysis failed: {e}")

        # Add analysis metadata - use original path, not temp zip path
        report["analysis_metadata"] = {
            "zip_file": str(original_path.absolute()),
            "analysis_timestamp": datetime.now().isoformat(),
            "total_projects": len(report["projects"]),
        }

        return report

    finally:
        # Cleanup temporary directories and files
        if temp_zip and temp_zip.exists():
            temp_zip.unlink()
        if temp_extract_dir:
            import shutil

            try:
                shutil.rmtree(temp_extract_dir)
            except Exception:
                pass  # Best effort cleanup


def display_analysis(results: dict) -> None:
    """Display comprehensive analysis results.

    Args:
        results: Analysis results from comprehensive pipeline
    """
    # Extract main sections
    metadata = results.get("analysis_metadata", {})
    summary = results.get("summary", {})
    projects = results.get("projects", [])

    # Header
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)

    # Metadata
    if metadata:
        print(f"\nArchive: {metadata.get('zip_file', 'N/A')}")
        print(f"Analyzed: {metadata.get('analysis_timestamp', 'N/A')}")
        print(f"Projects Found: {metadata.get('total_projects', len(projects))}")

    # Summary
    if summary:
        print(f"\nSummary:")
        print(f"   Total Files: {summary.get('total_files', 0)}")
        size_mb = summary.get("total_size_mb", 0)
        print(f"   Total Size: {size_mb:.2f} MB")

        if summary.get("languages"):
            print(f"   Languages: {', '.join(summary['languages'])}")
        if summary.get("frameworks"):
            print(f"   Frameworks: {', '.join(summary['frameworks'])}")

    # Display each project
    for i, project in enumerate(projects, 1):
        print("\n" + "━" * 70)
        print(f"PROJECT {i}: {project.get('project_name', 'Unknown')}")
        print("━" * 70)

        # Basic info
        if project.get("project_path"):
            print(f"\nPath: {project['project_path']}")

        if project.get("primary_language"):
            print(f"Primary Language: {project['primary_language']}")

        print(f"Total Files: {project.get('total_files', 0)}")

        size = project.get("total_size", 0)
        size_mb = size / (1024 * 1024) if size > 0 else 0
        print(f"Size: {size_mb:.2f} MB")

        # Languages breakdown
        languages = project.get("languages", {})
        if languages:
            print(f"\nLanguages:")
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {lang}: {count} files")

        # Frameworks
        frameworks = project.get("frameworks", [])
        if frameworks:
            print(f"\nFrameworks:")
            for fw in frameworks:
                print(f"   • {fw}")

        # Dependencies
        dependencies = project.get("dependencies", {})
        if dependencies:
            print(f"\nDependencies:")
            for ecosystem, deps in dependencies.items():
                if deps:
                    deps_str = ", ".join(deps[:5])  # Show first 5
                    if len(deps) > 5:
                        deps_str += f", ... ({len(deps) - 5} more)"
                    print(f"   {ecosystem}: {deps_str}")

        # Project health indicators
        has_tests = project.get("has_tests", False)
        has_readme = project.get("has_readme", False)
        has_ci_cd = project.get("has_ci_cd", False)
        has_docker = project.get("has_docker", False)

        print(f"\nProject Health:")
        print(f"   {'[x]' if has_tests else '[ ]'} Tests: {project.get('test_files', 0)} test files")
        print(f"   {'[x]' if has_readme else '[ ]'} README")
        print(f"   {'[x]' if has_ci_cd else '[ ]'} CI/CD")
        print(f"   {'[x]' if has_docker else '[ ]'} Docker")

        # Git info
        if project.get("is_git_repo"):
            total_commits = project.get("total_commits", 0)
            print(f"   [x] Git repository ({total_commits} commits)")

        # OOP Analysis (for Python projects)
        oop = project.get("oop_analysis", {})
        if oop and oop.get("total_classes", 0) > 0:
            print(f"\nOOP Analysis (Python):")
            print(f"   Classes: {oop.get('total_classes', 0)}")

            abstract = oop.get("abstract_classes", [])
            if abstract:
                print(f"   Abstraction: {len(abstract)} abstract classes")

            private = oop.get("private_methods", 0)
            protected = oop.get("protected_methods", 0)
            if private > 0 or protected > 0:
                print(f"   Encapsulation: {private} private, {protected} protected methods")

            properties = oop.get("properties_count", 0)
            if properties > 0:
                print(f"   Properties: {properties} @property decorators")

            inheritance = oop.get("classes_with_inheritance", 0)
            if inheritance > 0:
                print(f"   Inheritance: {inheritance} classes")

            overloads = oop.get("operator_overloads", 0)
            if overloads > 0:
                print(f"   Polymorphism: {overloads} operator overloads")

        # OOP Analysis (for Java projects)
        java_oop = project.get("java_oop_analysis", {})
        if java_oop and java_oop.get("total_classes", 0) > 0:
            print(f"\nOOP Analysis (Java):")
            print(f"   Classes: {java_oop.get('total_classes', 0)}")
            print(f"   Interfaces: {java_oop.get('interface_count', 0)}")
            print(f"   Enums: {java_oop.get('enum_count', 0)}")

            abstract = java_oop.get("abstract_classes", [])
            if abstract:
                print(f"   Abstraction: {len(abstract)} abstract classes")

            private = java_oop.get("private_methods", 0)
            protected = java_oop.get("protected_methods", 0)
            if private > 0 or protected > 0:
                print(f"   Encapsulation: {private} private, {protected} protected methods")

            inheritance = java_oop.get("classes_with_inheritance", 0)
            if inheritance > 0:
                print(f"   Inheritance: {inheritance} classes")

            overrides = java_oop.get("override_count", 0)
            overloads_java = java_oop.get("method_overloads", 0)
            if overrides > 0 or overloads_java > 0:
                print(f"   Polymorphism: {overrides} overrides, {overloads_java} overloads")

        # OOP Analysis (for C++ projects)
        cpp_oop = project.get("cpp_oop_analysis", {})
        if cpp_oop and (cpp_oop.get("total_classes", 0) > 0 or cpp_oop.get("struct_count", 0) > 0):
            print(f"\nOOP Analysis (C++):")
            print(f"   Classes: {cpp_oop.get('total_classes', 0)}")
            print(f"   Structs: {cpp_oop.get('struct_count', 0)}")

            abstract = cpp_oop.get("abstract_classes", [])
            if abstract:
                print(f"   Abstraction: {len(abstract)} abstract classes")

            private = cpp_oop.get("private_methods", 0)
            protected = cpp_oop.get("protected_methods", 0)
            if private > 0 or protected > 0:
                print(f"   Encapsulation: {private} private, {protected} protected methods")

            virtual = cpp_oop.get("virtual_methods", 0)
            if virtual > 0:
                print(f"   Polymorphism: {virtual} virtual methods")

            inheritance = cpp_oop.get("classes_with_inheritance", 0)
            if inheritance > 0:
                print(f"   Inheritance: {inheritance} classes")

            templates = cpp_oop.get("template_classes", 0)
            if templates > 0:
                print(f"   Templates: {templates} template classes")

        # OOP-Style Analysis (for C projects)
        c_oop = project.get("c_oop_analysis", {})
        if c_oop and c_oop.get("total_structs", 0) > 0:
            print(f"\nOOP-Style Analysis (C):")
            print(f"   Structs: {c_oop.get('total_structs', 0)}")
            print(f"   Functions: {c_oop.get('total_functions', 0)}")

            opaque = c_oop.get("opaque_pointer_structs", 0)
            if opaque > 0:
                print(f"   Abstraction: {opaque} opaque pointer structs")

            static = c_oop.get("static_functions", 0)
            if static > 0:
                print(f"   Encapsulation: {static} static functions")

            vtables = c_oop.get("vtable_structs", 0)
            if vtables > 0:
                print(f"   Polymorphism: {vtables} vtable-style structs")

            constructors = c_oop.get("constructor_destructor_pairs", 0)
            if constructors > 0:
                print(f"   Memory Management: {constructors} constructor/destructor pairs")

        # Git Analysis
        git_analysis = project.get("git_analysis", {})
        if git_analysis and git_analysis.get("is_git_repo"):
            print(f"\nGit Analysis:")
            print(f"   Total Commits: {git_analysis.get('total_commits', 0)}")
            print(f"   Contributors: {git_analysis.get('total_contributors', 0)}")

            if git_analysis.get("is_collaborative"):
                print(f"   Project Type: Collaborative")
            elif git_analysis.get("is_solo_project"):
                print(f"   Project Type: Solo")

            # Show top contributors
            contributors = git_analysis.get("contributors", [])
            if contributors:
                print(f"\n   Top Contributors:")
                for contrib in contributors[:3]:  # Show top 3
                    name = contrib.get("name", "Unknown")
                    commits = contrib.get("commit_count", 0)
                    percentage = contrib.get("percentage", 0)
                    print(f"      • {name}: {commits} commits ({percentage:.1f}%)")

    print("\n" + "=" * 70)


def display_document_analysis(analysis: DocumentAnalysis) -> None:
    """Display document analysis results in a formatted way.

    Args:
        analysis: DocumentAnalysis object with all analysis results
    """
    print("\n" + "=" * 70)
    print("  DOCUMENT ANALYSIS RESULTS")
    print("=" * 70)

    # Document basic info
    file_name = Path(analysis.file_path).name
    print(f"\nDocument: {file_name}")
    print(f"Type: {analysis.file_type.upper()} File")

    # Word count and pages
    wm = analysis.writing_metrics
    if wm.word_count > 0:
        print(
            f"Pages: {wm.page_estimate:.1f} | Words: {wm.word_count:,} | Paragraphs: {analysis.structure_analysis.paragraph_count}"
        )

    # Citation Analysis
    print("\n" + "-" * 70)
    print("CITATION ANALYSIS")
    print("-" * 70)

    cit = analysis.citation_analysis
    if cit.style:
        print(f"Citation Style Detected: {cit.style}")
        print(f"Total Citations:")
        print(f"   In-text citations: {cit.in_text_count}")
        print(f"   Bibliography entries: {cit.bibliography_count}")
        print(f"\nCitation Quality: {cit.confidence.capitalize()} confidence")

        if cit.has_consistent_style:
            print("   [x] Consistent formatting")
        else:
            print("   [ ] Mixed citation styles detected")
    else:
        print("No citations detected in this document")

    # Writing Quality Metrics
    print("\n" + "-" * 70)
    print("WRITING QUALITY METRICS")
    print("-" * 70)

    if wm.flesch_kincaid_grade is not None:
        print(f"Reading Level: {wm.reading_level_description}")
        print(f"   Flesch-Kincaid Grade: {wm.flesch_kincaid_grade}")
        print(f"   Flesch Reading Ease: {wm.flesch_reading_ease}")
    else:
        print("Reading Level: Analysis requires textstat library")

    if wm.sentence_count > 0:
        print(f"\nSentence Complexity:")
        print(f"   Total sentences: {wm.sentence_count}")
        print(f"   Average sentence length: {wm.avg_sentence_length:.1f} words")

        if wm.avg_sentence_length > 25:
            complexity = "High"
        elif wm.avg_sentence_length > 15:
            complexity = "Medium"
        else:
            complexity = "Low"
        print(f"   Complexity: {complexity}")

    print(f"\nAcademic Indicators:")
    print(f"   {'[x]' if wm.has_formal_tone else '[ ]'} Formal tone maintained")
    print(f"   {'[x]' if wm.has_technical_vocabulary else '[ ]'} Technical vocabulary used appropriately")

    # Document Structure
    print("\n" + "-" * 70)
    print("DOCUMENT STRUCTURE")
    print("-" * 70)

    struct = analysis.structure_analysis
    print(f"Structure Quality: {struct.structure_quality.replace('_', ' ').title()}")
    print(f"   {'[x]' if struct.has_introduction else '[ ]'} Clear introduction section")
    print(f"   {'[x]' if struct.has_conclusion else '[ ]'} Strong conclusion section")

    if struct.paragraph_count > 0:
        print(f"\nParagraph Analysis:")
        print(f"   Total paragraphs: {struct.paragraph_count}")
        print(f"   Average paragraph length: {struct.avg_paragraph_length:.0f} words")

    # Resume Highlights
    if analysis.resume_highlights:
        print("\n" + "-" * 70)
        print("RESUME HIGHLIGHTS")
        print("-" * 70)
        print("\nSkills & Achievements:")
        for highlight in analysis.resume_highlights:
            print(f"   • {highlight}")

        print("\nSuggested Resume Bullets:")
        # Generate formatted resume bullets
        if cit.in_text_count >= 10 and wm.page_estimate >= 3:
            print(f'   • "Conducted academic research and authored {wm.page_estimate:.0f}-page paper with')
            print(f'      {cit.in_text_count} peer-reviewed citations using {cit.style} format"')

        if wm.flesch_kincaid_grade and wm.flesch_kincaid_grade >= 16:
            print(f'   • "Demonstrated advanced writing proficiency (Grade {int(wm.flesch_kincaid_grade)}+ reading')
            print(f'      level) in formal academic contexts"')

        if wm.has_formal_tone and wm.has_technical_vocabulary:
            print(f'   • "Developed strong analytical and research skills through')
            print(f'      evidence-based academic writing"')

    print("\n" + "=" * 70)


def analyze_essay(file_path: Path) -> DocumentAnalysis:
    """Analyze an essay/document file.

    Args:
        file_path: Path to the document file

    Returns:
        DocumentAnalysis object with results
    """
    # Extract text from the document (lazy import to avoid optional deps blocking other commands)
    from .text_extractor import extract_text

    text = extract_text(str(file_path))

    if not text or len(text.strip()) < 100:
        raise ValueError("Could not extract sufficient text from document. File may be empty or unsupported format.")

    # Analyze the document
    analysis = analyze_document(str(file_path), text)

    return analysis


def analyze_complexity(zip_path: Path, verbose: bool = False) -> int:
    """Analyze Python code complexity in a ZIP file.

    Args:
        zip_path: Path to the ZIP file
        verbose: Show detailed findings

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from .analysis.complexity_analyzer import format_report
    from .analysis.project_analyzer import FileClassifier

    try:
        # First, detect projects in the ZIP
        print("\n[>] Step 1: Detecting projects...")
        project_results = analyze_folder(zip_path)

        # Find Python projects
        python_projects = []
        for directory, info in project_results.items():
            if info.is_project:
                # Check if it has Python files (heuristic: check for .py indicator)
                if any("py" in indicator.lower() for indicator in info.indicators_found):
                    python_projects.append(directory)

        if not python_projects:
            # If no clear Python projects, analyze the whole ZIP
            python_projects = [""]  # Empty string = root of ZIP

        print(f"   Found {len(python_projects)} project(s) to analyze")

        # Analyze each project
        with FileClassifier(zip_path) as classifier:
            for project_path in python_projects:
                if project_path:
                    print(f"\n Analyzing Python code in: {project_path}")
                else:
                    print("\n Analyzing Python code in ZIP root")

                result = classifier.analyze_python_complexity(project_path)

                if result["total_files"] == 0:
                    print(f"   No Python files found")
                    continue

                # Display the report
                report = result.get("report")
                if report:
                    print(format_report(report, verbose=verbose))

        return 0

    except Exception as e:
        print(f"\n[!] Error during complexity analysis: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from .database import check_user_consent, save_user_consent
    from .session import get_session
    from .shell import MDAShell

    parser = argparse.ArgumentParser(description="Mining Digital Artifacts CLI")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start in interactive mode")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Login to your account")
    login_parser.add_argument("username", help="Your username")
    login_parser.add_argument("password", help="Your password")

    # Signup command
    signup_parser = subparsers.add_parser("signup", help="Create a new account")
    signup_parser.add_argument("username", help="Choose a username")
    signup_parser.add_argument("password", help="Choose a password")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a folder")
    analyze_parser.add_argument("path", help="Path to the folder to analyze")
    analyze_parser.add_argument(
        "--complexity",
        action="store_true",
        help="Analyze Python code for time complexity patterns (requires ZIP file)",
    )
    analyze_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed complexity findings")

    # Analyze-essay command
    essay_parser = subparsers.add_parser("analyze-essay", help="Analyze an essay or document")
    essay_parser.add_argument("path", help="Path to the document file (.txt, .pdf, .docx, .md)")

    # Analyze-llm command
    llm_parser = subparsers.add_parser("analyze-llm", help="Analyze code using AI (Gemini)")
    llm_parser.add_argument("path", help="Path to the ZIP file to analyze")
    llm_parser.add_argument("--prompt", help="Custom analysis prompt (optional)")
    # Timeline command
    timeline_parser = subparsers.add_parser("timeline", help="Show chronological timelines from stored analyses")
    timeline_parser.add_argument("type", choices=["projects", "skills"], help="Timeline type to display")

    # Consent command
    consent_parser = subparsers.add_parser("consent", help="View or update consent status")
    consent_parser.add_argument("--status", action="store_true", help="Check current consent status")
    consent_parser.add_argument("--update", action="store_true", help="Update consent status")

    args = parser.parse_args()

    try:
        initialize()

        # Initialize analysis database
        try:
            init_db()
        except Exception as e:
            # Non-fatal: analysis can still run without database
            print(f"Warning: Could not initialize analysis database: {e}")

        # Interactive mode
        if args.interactive or not args.command:
            shell = MDAShell()
            shell.cmdloop()
            return 0

        # Session management
        session = {"logged_in": False, "username": None}

        # Command line mode
        if args.command == "login":
            from .session import save_session

            # First verify credentials
            if not authenticate_user(args.username, args.password):
                print("\nInvalid username or password")
                return 1

            # Handle consent for first-time users
            if not handle_first_time_consent(args.username):
                # User is authenticated but denied consent
                print("\nDenied Consent.")
                print("You can update your consent later using 'mda consent --update'")
                return 1

            # Save session for future commands
            save_session(args.username)
            print(f"\nLogin successful! Welcome {args.username}!")
            return 0

        elif args.command == "signup":
            if signup(args.username, args.password):
                print("\nAccount created successfully!")
                return 0
            else:
                print("\nUsername already exists")
                return 1

        elif args.command == "consent":
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1

            username = session["username"]
            has_consented = check_user_consent(username)

            if args.status:
                print(f"\nConsent Status for {username}:")
                print("Consented" if has_consented else "Not consented")
                return 0

            if args.update:
                if has_consented:
                    print("\nYou have already provided consent.")
                    print("To revoke consent, contact support.")
                    return 0

                print("\nConsent Required")
                print("------------------")
                if ask_for_consent():
                    save_user_consent(username, True)
                    print("\nThank you for providing consent!")
                    return 0
                else:
                    save_user_consent(username, False)
                    print("\nYou have not provided consent. Some features will be limited.")
                    return 1

        elif args.command == "analyze":
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1

            username = session["username"]
            if not check_user_consent(username):
                print("\nPlease provide consent before analyzing files")
                print("Run 'mda consent --update' to view and accept the consent form")
                return 1

            path = Path(args.path)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return 1

            # Run complexity analysis if requested
            if args.complexity:
                # Complexity analysis requires a ZIP file
                if not (path.is_file() and path.suffix.lower() == ".zip"):
                    print("\n❌ Complexity analysis requires a ZIP file")
                    print(f"   Provided: {path}")
                    return 1

                print(f"\n[*] Analyzing Python code complexity in: {path.name}")
                return analyze_complexity(path, args.verbose)

            # Standard project detection analysis - validate path type
            if not path.is_dir() and not (path.is_file() and path.suffix.lower() == ".zip"):
                print(f"\n❌ Path must be a directory or ZIP file: {path}")
            # Validate path type
            if not path.is_dir() and not (path.is_file() and path.suffix.lower() == ".zip"):
                print(f"\nPath must be a directory or ZIP file: {path}")
                return 1

            # Run analysis with error handling
            try:
                print(f"\n[*] Analyzing: {path}")
                results = analyze_folder(path)
                display_analysis(results)

                # Generate resume highlights
                from .analysis.resume_generator import print_resume_items

                print_resume_items(results)

                # Store analysis in database
                try:
                    from .analysis_database import record_analysis

                    analysis_id = record_analysis("non_llm", results)
                    analysis_uuid = results.get("analysis_metadata", {}).get("analysis_uuid", "unknown")
                    print(f"\n📊 Analysis saved to database (ID: {analysis_id}, UUID: {analysis_uuid})")
                except Exception as db_error:
                    print(f"\n⚠️  Warning: Could not save to database: {db_error}")

                print("\n✅ Analysis complete!")
                return 0
            except zipfile.BadZipFile:
                print(f"\n❌ Invalid or corrupted ZIP file: {path}")
                return 1
            except ValueError as e:
                print(f"\n❌ {e}")
                return 1
            except Exception as e:
                print(f"\n❌ Analysis failed: {e}")
                import traceback

                traceback.print_exc()
                return 1

        elif args.command == "analyze-essay":
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1

            username = session["username"]
            if not check_user_consent(username):
                print("\nPlease provide consent before analyzing files")
                print("Run 'mda consent --update' to view and accept the consent form")
                return 1

            path = Path(args.path)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return 1

            # Validate file type
            supported_extensions = {".txt", ".pdf", ".docx", ".md"}
            if not path.is_file() or path.suffix.lower() not in supported_extensions:
                print(f"\nFile must be one of: {', '.join(supported_extensions)}")
                return 1

            # Run essay analysis
            try:
                print(f"\nAnalyzing document: {path}")
                analysis = analyze_essay(path)
                display_document_analysis(analysis)
                print("\nDocument analysis complete!")
                return 0
            except ValueError as e:
                print(f"\n{e}")
                return 1
            except Exception as e:
                print(f"\nDocument analysis failed: {e}")
                import traceback

                traceback.print_exc()
                return 1

        elif args.command == "analyze-llm":
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1

            username = session["username"]
            if not check_user_consent(username):
                print("\nPlease provide consent before analyzing files")
                print("Run 'mda consent --update' to view and accept the consent form")
                return 1

            path = Path(args.path)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return 1

            # Validate file type - must be ZIP
            if not path.is_file() or path.suffix.lower() != ".zip":
                print(f"\nLLM analysis requires a ZIP file")
                return 1

            # Run LLM analysis
            try:
                from rich.progress import (BarColumn, Progress, SpinnerColumn,
                                           TaskProgressColumn, TextColumn)

                from .analysis.llm_pipeline import run_gemini_analysis

                print(f"\n[*] Running AI-powered analysis on: {path}")

                results = {}
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    transient=True,
                ) as progress:
                    task = progress.add_task("Starting analysis...", total=100)

                    def cli_progress_callback(current, total, msg):
                        percent = (current / total) * 100 if total > 0 else 0
                        progress.update(task, completed=percent, description=msg)

                    results = run_gemini_analysis(path, prompt_override=args.prompt, progress_callback=cli_progress_callback)

                # Display standard analysis
                display_analysis(results)

                # Display LLM summary
                llm_summary = results.get("llm_summary")
                llm_error = results.get("llm_error")

                if llm_error:
                    print(f"\n⚠️  LLM Analysis Error: {llm_error}")
                elif llm_summary:
                    print("\n" + "=" * 70)
                    print("  AI-POWERED ANALYSIS SUMMARY")
                    print("=" * 70)
                    print(f"\n{llm_summary}\n")
                    print("=" * 70)

                # Store in database
                try:
                    from .analysis_database import record_analysis

                    analysis_id = record_analysis("llm", results)
                    analysis_uuid = results.get("analysis_metadata", {}).get("analysis_uuid", "unknown")
                    print(f"\n📊 Analysis saved to database (ID: {analysis_id}, UUID: {analysis_uuid})")
                except Exception as db_error:
                    print(f"\n⚠️  Warning: Could not save to database: {db_error}")

                print("\n✅ LLM analysis complete!")
                return 0
            except Exception as e:
                print(f"\n❌ LLM analysis failed: {e}")
                import traceback

                traceback.print_exc()
                return 1
        elif args.command == "timeline":
            # No login/consent required to view previously stored aggregate timelines
            from .analysis.chronology import (get_projects_timeline,
                                              get_skills_timeline)

            try:
                init_db()
            except Exception:
                pass

            if args.type == "projects":
                entries = get_projects_timeline()
                if not entries:
                    print("\nNo projects found in the analysis database.")
                    return 0
                print("\nProjects Timeline (by analysis date):")
                for i, e in enumerate(entries, 1):
                    print(f"  {i}. {e.analysis_timestamp} — {e.project_name}")
                    if e.primary_language:
                        print(f"     Language: {e.primary_language}")
                    if e.total_files is not None:
                        print(f"     Files: {e.total_files}")
                    if e.has_tests is not None:
                        print(f"     Tests: {'yes' if e.has_tests else 'no'}")
                    if e.has_ci_cd is not None:
                        print(f"     CI/CD: {'yes' if e.has_ci_cd else 'no'}")
                    if e.has_docker is not None:
                        print(f"     Docker: {'yes' if e.has_docker else 'no'}")
                return 0

            elif args.type == "skills":
                entries = get_skills_timeline()
                if not entries:
                    print("\nNo skills found in the analysis database.")
                    return 0
                print("\nSkills Timeline (by analysis date):")
                for i, e in enumerate(entries, 1):
                    langs = ", ".join(e.skills.get("languages", [])) or "-"
                    fws = ", ".join(e.skills.get("frameworks", [])) or "-"
                    print(f"  {i}. {e.date}")
                    print(f"     Languages: {langs}")
                    print(f"     Frameworks: {fws}")
                return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
