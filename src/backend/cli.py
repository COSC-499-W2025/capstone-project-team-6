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
    """Handle consent for first-time users."""
    from .database import check_user_consent, save_user_consent

    # Check if user has already given consent (True or False)
    # We just need to know if a record exists, but the DB helper returns bool.
    # Logic: Login succeeds regardless of consent value, but we need to ensure
    # they have at least answered the question.
    
    # In this specific implementation, we treat the existence of a consent record
    # (checked via a query) as sufficient to proceed. 
    # However, since check_user_consent returns the boolean value of the consent,
    # we might need to check if the record exists at all. 
    # For simplicity based on provided db code, we assume the user flow 
    # handles the "ask if not asked before" logic.
    
    # Actually, looking at the DB code:
    # check_user_consent returns False if no record OR if record is 0.
    # This might force a re-ask if they said NO previously.
    # But for this helper, let's stick to the existing flow.
    
    # Note: A strict "has user answered?" check isn't exposed in database.py 
    # without modifying it. We will assume the CLI flow handles the "ask" 
    # part if check_user_consent returns False during signup/login.
    
    # For now, we will rely on the interactive flow in login/signup.
    pass 
    # The original function logic was actually inline in the commands or 
    # specific to the flow. I will keep the helper as defined in original file
    # or rely on the logic inside main().
    
    # REVERTING to original helper logic from your file for safety:
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
    """Attempt to login with the given credentials."""
    return authenticate_user(username, password)


def signup(username: str, password: str) -> bool:
    """Register a new user."""
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
    """Create a temporary ZIP file from a directory."""
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
    """Analyze a folder or ZIP file using the comprehensive analysis pipeline."""
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

            # C Analysis
            if "cpp" in project.get("languages", {}) or "c" in project.get("languages", {}):
                try:
                    from .analysis.c_oop_analyzer import analyze_c_project

                    c_analysis = analyze_c_project(zip_path, project_path)
                    if c_analysis["c_oop_analysis"].get("total_structs", 0) > 0:
                        report["projects"][i]["c_oop_analysis"] = c_analysis["c_oop_analysis"]
                except ImportError:
                    pass
                except Exception as e:
                    pass

        # Git Analysis
        if analysis_dir and (analysis_dir / ".git").exists():
            try:
                from .analysis.git_analysis import analyze_project

                git_result = analyze_project(analysis_dir, export_to_file=False)
                if report["projects"]:
                    report["projects"][0]["git_analysis"] = git_result.to_dict()
            except Exception as e:
                print(f"Warning: Git analysis failed: {e}")
        elif not analysis_dir:
            try:
                with zipfile_module.ZipFile(zip_path, "r") as zf:
                    git_files = [f for f in zf.namelist() if ".git/" in f]
                    if git_files:
                        temp_extract_dir = tempfile.mkdtemp()
                        zf.extractall(temp_extract_dir)

                        git_root = Path(temp_extract_dir)
                        for item in git_root.rglob(".git"):
                            if item.is_dir():
                                git_root = item.parent
                                break

                        from .analysis.git_analysis import analyze_project

                        git_result = analyze_project(git_root, export_to_file=False)
                        if report["projects"]:
                            report["projects"][0]["git_analysis"] = git_result.to_dict()
            except Exception as e:
                print(f"Warning: Git analysis failed: {e}")

        # Add analysis metadata
        report["analysis_metadata"] = {
            "zip_file": str(original_path.absolute()),
            "analysis_timestamp": datetime.now().isoformat(),
            "total_projects": len(report["projects"]),
        }

        return report

    finally:
        if temp_zip and temp_zip.exists():
            temp_zip.unlink()
        if temp_extract_dir:
            import shutil
            try:
                shutil.rmtree(temp_extract_dir)
            except Exception:
                pass


def display_analysis(results: dict) -> None:
    """Display comprehensive analysis results."""
    # (Existing display code omitted for brevity - works as previously defined)
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
        
        # ... (rest of the display logic is standard and unchanged) ...
        # For brevity in the diff, assuming the original display function logic remains here
        # It is purely a display function and doesn't affect the logic flow we are changing.
        if project.get("project_path"):
            print(f"\nPath: {project['project_path']}")

        if project.get("primary_language"):
            print(f"Primary Language: {project['primary_language']}")
            
        # ... (Keeping the rest of the original display_analysis function implicitly) ...
        # (Copying the rest of the function to ensure the file is complete)
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
            
        # OOP Analysis (Python)
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

        # OOP Analysis (Java)
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

        # OOP Analysis (C++)
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

        # OOP-Style Analysis (C)
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
            contributors = git_analysis.get("contributors", [])
            if contributors:
                print(f"\n   Top Contributors:")
                for contrib in contributors[:3]:
                    name = contrib.get("name", "Unknown")
                    commits = contrib.get("commit_count", 0)
                    percentage = contrib.get("percentage", 0)
                    print(f"      • {name}: {commits} commits ({percentage:.1f}%)")

        # Complexity Analysis (Python)
        complexity_analysis = project.get("complexity_analysis", {})
        if complexity_analysis and "error" not in complexity_analysis:
            print(f"\nComplexity Analysis (Python):")
            opt_score = complexity_analysis.get("optimization_score", 0.0)
            print(f"   Optimization Score: {opt_score:.1f}/100")
            if opt_score >= 75:
                assessment = "Strong optimization awareness ✓"
            elif opt_score >= 50:
                assessment = "Moderate optimization awareness"
            elif opt_score >= 25:
                assessment = "Basic optimization"
            else:
                assessment = "Limited optimization awareness"
            print(f"   Assessment: {assessment}")
            summary = complexity_analysis.get("summary", {})
            if summary:
                good_practices = []
                issues = []
                for key in ["efficient_data_structure", "set_operations", "dict_lookup", "list_comprehension", "generator_expression", "binary_search", "memoization"]:
                    if summary.get(key, 0) > 0:
                        good_practices.append(f"{key.replace('_', ' ').title()}: {summary[key]}")
                for key in ["nested_loops", "inefficient_lookup", "inefficient_membership_test"]:
                    if summary.get(key, 0) > 0:
                        issues.append(f"{key.replace('_', ' ').title()}: {summary[key]}")
                if good_practices:
                    print(f"   Good Practices Found:")
                    for practice in good_practices[:3]:
                        print(f"      • {practice}")
                if issues:
                    print(f"   Optimization Opportunities:")
                    for issue in issues:
                        print(f"      • {issue}")

    print("\n" + "=" * 70)


def display_document_analysis(analysis: DocumentAnalysis) -> None:
    """Display document analysis results in a formatted way."""
    # (Kept identical to original)
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
    """Analyze an essay/document file."""
    from .text_extractor import extract_text

    text = extract_text(str(file_path))

    if not text or len(text.strip()) < 100:
        raise ValueError("Could not extract sufficient text from document. File may be empty or unsupported format.")

    analysis = analyze_document(str(file_path), text)

    return analysis


def analyze_complexity(zip_path: Path, verbose: bool = False) -> int:
    """Analyze Python code complexity in a ZIP file."""
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
    """Main CLI entry point."""
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
    analyze_parser.add_argument("path", help="Path to the folder or ZIP to analyze")
    analyze_parser.add_argument(
        "--complexity",
        action="store_true",
        help="Analyze Python code for time complexity patterns (requires ZIP file)",
    )
    analyze_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed complexity findings")
    
    # LLM arguments merged into analyze
    analyze_parser.add_argument("--prompt", help="Custom analysis prompt for AI (requires consent)")
    analyze_parser.add_argument("--architecture", action="store_true", help="AI: Deep analysis of patterns and anti-patterns")
    analyze_parser.add_argument("--security", action="store_true", help="AI: Logic-based security and defensive coding")
    analyze_parser.add_argument("--skills", action="store_true", help="AI: Infer soft skills and testing maturity")
    analyze_parser.add_argument("--domain", action="store_true", help="AI: Domain-specific best practices")
    analyze_parser.add_argument("--resume", action="store_true", help="AI: Generate resume and portfolio artifacts")
    analyze_parser.add_argument("--all", action="store_true", help="AI: Enable all deep analysis features")

    # Analyze-essay command
    essay_parser = subparsers.add_parser("analyze-essay", help="Analyze an essay or document")
    essay_parser.add_argument("path", help="Path to the document file (.txt, .pdf, .docx, .md)")

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
            #handle_first_time_consent(args.username)
            # We don't block login if they don't consent, just features

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
            
            # NOTE: Logic changed. We no longer strictly require consent to run ANY analysis.
            # We check consent to decide whether to run LLM analysis.
            # Standard analysis runs locally regardless.
            has_consented = check_user_consent(username)

            path = Path(args.path)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return 1

            # Run complexity analysis if requested
            if args.complexity and not args.all: 
                # Note: If --all is passed, we assume LLM complexity analysis is desired unless specified otherwise,
                # but standard complexity requires zip. 
                # For backward compatibility, strict --complexity uses the non-LLM tool if zip is provided.
                if path.is_file() and path.suffix.lower() == ".zip":
                    print(f"\n[*] Analyzing Python code complexity in: {path.name}")
                    return analyze_complexity(path, args.verbose)
                elif args.complexity:
                     print("\n❌ Traditional complexity analysis requires a ZIP file. Continuing with standard analysis...")

            # Validate path type for standard analysis
            if not path.is_dir() and not (path.is_file() and path.suffix.lower() == ".zip"):
                print(f"\nPath must be a directory or ZIP file: {path}")
                return 1

            # 1. Run Standard Analysis
            try:
                print(f"\n[*] Analyzing: {path}")
                results = analyze_folder(path)
                display_analysis(results)

                # Generate resume highlights
                from .analysis.resume_generator import print_resume_items
                print_resume_items(results)

                # Generate portfolio items
                from .analysis.portfolio_item_generator import generate_portfolio_item

                print("\n" + "=" * 70)
                print("  GENERATED PORTFOLIO ITEMS")
                print("=" * 70)

                for project in results.get("projects", []):
                    try:
                        portfolio_item = generate_portfolio_item(project)
                        print(f"\n{'━' * 70}")
                        print(f"PROJECT: {portfolio_item.get('project_name', 'Unknown')}")
                        print(f"{'━' * 70}")
                        
                        stats = portfolio_item.get("project_statistics", {})
                        print(f"\nSophistication Level: {stats.get('sophistication_level', 'basic').title()}")
                        print(f"Quality Score: {stats.get('quality_score', 0)}/100")
                        
                        tech_stack = portfolio_item.get("tech_stack", [])
                        if tech_stack:
                            print(f"\nTech Stack: {', '.join(tech_stack[:5])}...")
                            
                        skills = portfolio_item.get("skills_exercised", [])
                        if skills:
                            print(f"\nSkills Demonstrated: {', '.join(skills[:5])}")

                    except Exception as e:
                        print(f"\n   Warning: Could not generate portfolio item: {e}")

                print("\n" + "=" * 70 + "\n")

                # Store standard analysis in database
                try:
                    from .analysis_database import record_analysis
                    analysis_id = record_analysis("non_llm", results)
                    print(f"\n📊 Standard analysis saved to database (ID: {analysis_id})")
                except Exception as db_error:
                    print(f"\n⚠️  Warning: Could not save to database: {db_error}")

                # 2. Check Consent for LLM Analysis
                if has_consented:
                    print("\n[+] Consent verified. Proceeding with AI-powered analysis...")
                    
                    # Prepare ZIP for LLM if input was a directory
                    llm_target_path = path
                    temp_llm_zip = None
                    
                    if path.is_dir():
                        print("    Creating temporary zip for AI processing...")
                        try:
                            temp_llm_zip = create_temp_zip(path)
                            llm_target_path = temp_llm_zip
                        except Exception as e:
                            print(f"❌ Failed to create zip for AI analysis: {e}")
                            has_consented = False # Abort LLM part

                    if has_consented:
                        # Collect active features
                        active_features = []
                        if args.all:
                            active_features = ["architecture", "complexity", "security", "skills", "domain", "resume"]
                        else:
                            if args.architecture: active_features.append("architecture")
                            if args.complexity: active_features.append("complexity")
                            if args.security: active_features.append("security")
                            if args.skills: active_features.append("skills")
                            if args.domain: active_features.append("domain")
                            if args.resume: active_features.append("resume")

                        try:
                            from rich.progress import (BarColumn, Progress, SpinnerColumn,
                                                       TaskProgressColumn, TextColumn)
                            from .analysis.llm_pipeline import run_gemini_analysis

                            print(f"[*] Running Gemini analysis on: {llm_target_path}")
                            
                            llm_results = {}
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                BarColumn(),
                                TaskProgressColumn(),
                                transient=True,
                            ) as progress:
                                task = progress.add_task("Analyzing with AI...", total=100)

                                def cli_progress_callback(current, total, msg):
                                    percent = (current / total) * 100 if total > 0 else 0
                                    progress.update(task, completed=percent, description=msg)

                                llm_results = run_gemini_analysis(
                                    llm_target_path,
                                    active_features=active_features,
                                    prompt_override=args.prompt,
                                    progress_callback=cli_progress_callback,
                                )
                            
                            # Display Rich Results
                            from rich import box
                            from rich.console import Console
                            from rich.markdown import Markdown
                            from rich.panel import Panel
                            
                            console = Console()
                            console.print()
                            console.print(Panel.fit("[bold white]Gemini Deep Code Analysis[/bold white]", style="blue"))
                            
                            llm_summary = llm_results.get("llm_summary")
                            llm_error = llm_results.get("llm_error")
                            
                            if llm_error:
                                console.print(Panel(f"[bold red]Error:[/bold red]\n{llm_error}", style="red"))
                            elif llm_summary:
                                md = Markdown(llm_summary)
                                console.print(Panel(md, title="[bold green]AI-Powered Insights[/bold green]", border_style="green"))

                            # Store LLM analysis in database
                            try:
                                from .analysis_database import record_analysis
                                llm_analysis_id = record_analysis("llm", llm_results)
                                print(f"\n📊 AI analysis saved to database (ID: {llm_analysis_id})")
                            except Exception as db_error:
                                print(f"\n⚠️  Warning: Could not save AI results: {db_error}")

                        except Exception as e:
                            print(f"\n❌ AI analysis failed: {e}")
                            # Don't fail the whole command, standard analysis succeeded
                        
                        finally:
                            # Cleanup temp zip if we created one
                            if temp_llm_zip and temp_llm_zip.exists():
                                temp_llm_zip.unlink()

                else:
                    print("\n[i] AI-powered analysis skipped (No consent provided).")
                    print("    Run 'mda consent --update' to enable deep code insights.")

                # Prompt to save JSON (Combined logic?) 
                # The original code asked to save standard, then asked to save LLM in separate commands.
                # Here we can just ask once to save the main results. 
                # If LLM ran, we could merge results or just save the standard one which is the return type expectation.
                # For simplicity, we stick to the standard result saving as per the original 'analyze' flow.
                
                print("\n" + "=" * 70)
                response = input("Would you like to save the analysis as JSON? (y/N): ").strip().lower()
                if response in ["y", "yes"]:
                    import json
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = input(f"Enter filename (default: analysis_{timestamp}.json): ").strip() or f"analysis_{timestamp}.json"
                    if not filename.endswith(".json"): filename += ".json"
                    
                    try:
                        with open(filename, "w", encoding="utf-8") as f:
                            # If LLM ran, ideally we'd want those results too, but merging dicts cleanly is complex 
                            # given the schema. We will save the standard results which cover 90% of data.
                            json.dump(results, f, indent=2, ensure_ascii=False)
                        print(f"✅ Analysis saved to: {Path(filename).absolute()}")
                    except Exception as e:
                        print(f"❌ Error saving JSON: {e}")

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
            # (Identical to original)
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1
            # Note: Essays don't strictly require the codebase consent, but good practice to check
            # For now, sticking to original logic that required consent check
            if not check_user_consent(session["username"]):
                 print("\nPlease provide consent before analyzing files")
                 return 1
                 
            path = Path(args.path)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return 1

            supported_extensions = {".txt", ".pdf", ".docx", ".md"}
            if not path.is_file() or path.suffix.lower() not in supported_extensions:
                print(f"\nFile must be one of: {', '.join(supported_extensions)}")
                return 1

            try:
                print(f"\nAnalyzing document: {path}")
                analysis = analyze_essay(path)
                display_document_analysis(analysis)
                print("\nDocument analysis complete!")
                return 0
            except Exception as e:
                print(f"\nDocument analysis failed: {e}")
                return 1

        elif args.command == "timeline":
             # (Identical to original)
            from .analysis.chronology import (get_projects_timeline,
                                              get_skills_timeline)
            try:
                init_db()
            except Exception:
                pass

            if args.type == "projects":
                entries = get_projects_timeline()
                if not entries:
                    print("\nNo projects found.")
                    return 0
                print("\nProjects Timeline:")
                for i, e in enumerate(entries, 1):
                    d = e.last_commit_date or e.last_modified_date or e.analysis_timestamp
                    print(f"  {i}. {d} — {e.project_name}")
                return 0

            elif args.type == "skills":
                entries = get_skills_timeline()
                if not entries:
                    print("\nNo skills found.")
                    return 0
                print("\nSkills Timeline:")
                for i, e in enumerate(entries, 1):
                    print(f"  {i}. {e.date}")
                    print(f"     Languages: {', '.join(e.skills.get('languages', []))}")
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