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
from .analysis.analyze import calculate_composite_score
from .analysis.deep_code_analyzer import generate_comprehensive_report
from .analysis.document_analyzer import DocumentAnalysis, analyze_document
from .analysis.role_predictor import predict_developer_role, format_role_prediction
from .analysis_database import init_db
from .consent import ask_for_consent
from .curation_cli import (curate_project_rank_interactive,
                           curate_skills_highlight_interactive)

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


def analyze_folder(path: Path, target_user_email: Optional[str] = None, quick_mode: bool = False) -> dict:
    """Analyze a folder or ZIP file using the comprehensive analysis pipeline.

    Args:
        path: Path to the folder or ZIP file to analyze
        target_user_email: Optional email to focus git analysis on specific user
        quick_mode: If True, skip heavy operations like deep git blame analysis

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
            if not quick_mode:
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
        if not quick_mode:
            print(f"Running analysis pipeline...")
        else:
            print(f"Running quick analysis (skipping heavy git operations)...")

        report = generate_comprehensive_report(zip_path, target_user_email=target_user_email, quick_mode=quick_mode)

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
                    report["projects"][i]["cpp_oop_analysis"] = {
                        "error": str(e),
                        "total_classes": 0,
                    }

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

                git_result = analyze_project(
                    analysis_dir,
                    target_user_email=target_user_email,
                    export_to_file=False,
                )
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

                        git_result = analyze_project(
                            git_root,
                            target_user_email=target_user_email,
                            export_to_file=False,
                        )
                        if report["projects"]:
                            report["projects"][0]["git_analysis"] = git_result.to_dict()
            except Exception as e:
                print(f"Warning: Git analysis failed: {e}")

        # Add role prediction to each project
        for i, project in enumerate(report["projects"]):
            try:
                # Calculate composite score for role prediction
                score_data = calculate_composite_score(project, user_email=target_user_email)
                project_with_score = project.copy()
                project_with_score["score_data"] = score_data
                
                # Predict developer role
                role_prediction = predict_developer_role(project_with_score)
                
                # Store role prediction data in project
                report["projects"][i]["role_prediction"] = {
                    "predicted_role": role_prediction.predicted_role.value,
                    "confidence_score": role_prediction.confidence_score,
                    "alternative_roles": [(role.value, score) for role, score in role_prediction.alternative_roles],
                    "reasoning": role_prediction.reasoning,
                    "key_indicators": role_prediction.key_indicators
                }
            except Exception as e:
                print(f"Warning: Role prediction failed for {project.get('project_name', 'Unknown')}: {e}")
                # Add minimal role data to prevent issues
                report["projects"][i]["role_prediction"] = {
                    "predicted_role": "Junior Developer",
                    "confidence_score": 0.1,
                    "alternative_roles": [],
                    "reasoning": ["Role prediction failed"],
                    "key_indicators": {}
                }

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

        target_user_stats = project.get("target_user_stats") or {}
        target_user_email = project.get("target_user_email")
        if target_user_stats:
            contribution_volume = project.get("contribution_volume") or {}
            blame_summary = project.get("blame_summary") or {}
            semantic_summary = project.get("semantic_summary", {})
            activity_breakdown = project.get("activity_breakdown", {})
            lines_changed = contribution_volume.get(target_user_email)
            surviving_lines = blame_summary.get(target_user_email)
            commit_count = target_user_stats.get("commit_count") or target_user_stats.get("commits") or 0
            commit_share = target_user_stats.get("percentage") or 0

            print("\nTarget User Contribution:")
            print(f"   Email: {target_user_stats.get('email', target_user_email)}")
            print(f"   Commits: {commit_count} ({commit_share:.1f}% share)")
            if lines_changed is not None:
                print(f"   Lines changed: {lines_changed}")
            if surviving_lines is not None:
                total_surviving = sum(v for v in blame_summary.values() if isinstance(v, (int, float)))
                if total_surviving > 0:
                    percentage = (surviving_lines / total_surviving) * 100
                    print(f"   Surviving lines: {surviving_lines} ({percentage:.1f}% of codebase)")
                else:
                    print(f"   Surviving lines: {surviving_lines}")

            # Semantic summary (trivial vs substantial commits)
            user_semantic = semantic_summary.get(target_user_email, {})
            if user_semantic:
                trivial = user_semantic.get("trivial_commits", 0)
                substantial = user_semantic.get("substantial_commits", 0)
                total_lines_semantic = user_semantic.get("total_lines_changed", 0)
                if trivial > 0 or substantial > 0:
                    print(f"   Commit breakdown: {substantial} substantial, {trivial} trivial commits")
                if total_lines_semantic > 0:
                    print(f"   Total lines changed (semantic): {total_lines_semantic}")

            # Activity breakdown (code/test/docs/design)
            user_activity = activity_breakdown.get(target_user_email, {})
            if user_activity:
                activity_parts = []
                if user_activity.get("code", 0) > 0:
                    activity_parts.append(f"code: {user_activity['code']} lines")
                if user_activity.get("test", 0) > 0:
                    activity_parts.append(f"tests: {user_activity['test']} lines")
                if user_activity.get("docs", 0) > 0:
                    activity_parts.append(f"docs: {user_activity['docs']} lines")
                if user_activity.get("design", 0) > 0:
                    activity_parts.append(f"design: {user_activity['design']} lines")

                if activity_parts:
                    print(f"   Activity breakdown: {', '.join(activity_parts)}")

        # Developer Role Prediction
        try:
            # Check if role prediction data already exists in the project
            existing_role_data = project.get("role_prediction")
            if existing_role_data:
                # Display stored role prediction
                print(f"\n{'-' * 40}")
                print(f"   PREDICTED ROLE: {existing_role_data.get('predicted_role', 'Unknown')}")
                confidence = existing_role_data.get('confidence_score', 0)
                print(f"   Confidence: {confidence:.1%}")
                
                alternative_roles = existing_role_data.get('alternative_roles', [])
                if alternative_roles:
                    print(f"   Alternative roles:")
                    for role_info in alternative_roles[:3]:  # Show top 3 alternatives
                        if isinstance(role_info, (list, tuple)) and len(role_info) >= 2:
                            role_name, score = role_info[0], role_info[1]
                            print(f"      • {role_name} ({score:.1%})")
                
                reasoning = existing_role_data.get('reasoning', [])
                if reasoning:
                    print(f"   Key indicators:")
                    for reason in reasoning[:5]:  # Show top 5 reasons
                        print(f"      • {reason}")
                print(f"{'-' * 40}")
            else:
                # Generate new role prediction
                from .analysis.analyze import calculate_composite_score
                # Calculate score data for role prediction
                score_data = calculate_composite_score(project, user_email=target_user_email)
                project_with_score = project.copy()
                project_with_score["score_data"] = score_data
                
                # Predict developer role
                role_prediction = predict_developer_role(project_with_score)
                
                print(f"\n{'-' * 40}")
                role_display = format_role_prediction(role_prediction)
                print(role_display)
                print(f"{'-' * 40}")
        except Exception as e:
            print(f"\n🎯 ROLE PREDICTION: Unable to predict role (Error: {e})")

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

        # Additional Git Contribution Details (if available)
        semantic_summary = project.get("semantic_summary", {})
        activity_breakdown = project.get("activity_breakdown", {})
        contribution_volume = project.get("contribution_volume", {})
        blame_summary = project.get("blame_summary", {})

        if semantic_summary or activity_breakdown or contribution_volume or blame_summary:
            print(f"\nDetailed Contribution Analysis:")

            # Show overall contribution volume
            if contribution_volume:
                total_lines = sum(v for v in contribution_volume.values() if isinstance(v, (int, float)))
                print(f"   Total lines changed: {total_lines}")
                if len(contribution_volume) > 1:
                    print(f"   Contributors with changes: {len(contribution_volume)}")
                    # Show top contributors by lines changed
                    sorted_contributors = sorted(
                        contribution_volume.items(),
                        key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                        reverse=True,
                    )[:3]
                    print(f"   Top contributors by lines:")
                    for email, lines in sorted_contributors:
                        if isinstance(lines, (int, float)) and lines > 0:
                            percentage = (lines / total_lines * 100) if total_lines > 0 else 0
                            print(f"      • {email}: {lines} lines ({percentage:.1f}%)")

            # Show semantic summary (trivial vs substantial)
            if semantic_summary:
                total_substantial = sum(
                    stats.get("substantial_commits", 0) for stats in semantic_summary.values() if isinstance(stats, dict)
                )
                total_trivial = sum(
                    stats.get("trivial_commits", 0) for stats in semantic_summary.values() if isinstance(stats, dict)
                )
                if total_substantial > 0 or total_trivial > 0:
                    print(f"   Commit quality: {total_substantial} substantial, {total_trivial} trivial commits")

            # Show activity breakdown summary
            if activity_breakdown:
                total_code = sum(act.get("code", 0) for act in activity_breakdown.values() if isinstance(act, dict))
                total_test = sum(act.get("test", 0) for act in activity_breakdown.values() if isinstance(act, dict))
                total_docs = sum(act.get("docs", 0) for act in activity_breakdown.values() if isinstance(act, dict))
                total_design = sum(act.get("design", 0) for act in activity_breakdown.values() if isinstance(act, dict))

                activity_parts = []
                if total_code > 0:
                    activity_parts.append(f"code: {total_code}")
                if total_test > 0:
                    activity_parts.append(f"tests: {total_test}")
                if total_docs > 0:
                    activity_parts.append(f"docs: {total_docs}")
                if total_design > 0:
                    activity_parts.append(f"design: {total_design}")

                if activity_parts:
                    print(f"   Activity breakdown: {', '.join(activity_parts)} lines")

            # Show blame summary (surviving lines)
            if blame_summary:
                total_surviving = sum(v for v in blame_summary.values() if isinstance(v, (int, float)))
                if total_surviving > 0:
                    print(f"   Total surviving lines: {total_surviving}")
                    if len(blame_summary) > 1:
                        sorted_blame = sorted(
                            blame_summary.items(),
                            key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                            reverse=True,
                        )[:3]
                        print(f"   Top code owners:")
                        for email, lines in sorted_blame:
                            if isinstance(lines, (int, float)) and lines > 0:
                                percentage = (lines / total_surviving * 100) if total_surviving > 0 else 0
                                print(f"      • {email}: {lines} lines ({percentage:.1f}%)")

        # Enhanced Contribution Ranking Scores
        try:
            from analysis.analyze import calculate_composite_score

            user_email = project.get("target_user_email")
            score_data = calculate_composite_score(project, user_email=user_email)

            if score_data:
                print(f"\n{'=' * 60}")
                print(f"  ENHANCED CONTRIBUTION RANKING")
                print(f"{'=' * 60}")

                # Overall scores
                composite_score = score_data.get("composite_score", 0)
                category = score_data.get("category", "N/A")
                print(f"\nFinal Score: {composite_score:.2f}/100.0 ({category})")

                user_score = score_data.get("user_contribution_score", 0.0)
                if user_score > 0:
                    print(f"User Contribution Boost: +{user_score:.2f}/20.0")
                    print(f"Adjusted Score: {score_data.get('adjusted_score', 0):.2f}/100.0")

                # Breakdown by factor
                breakdown = score_data.get("breakdown", {})
                justification = score_data.get("justification", {})

                if breakdown:
                    print(f"\nScore Breakdown:")
                    print(f"\n  Base Factors (45% weight):")
                    print(f"    • Code Architecture:     {breakdown.get('code_architecture', 0):>6.2f}/30.0")
                    print(f"    • Code Quality:          {breakdown.get('code_quality', 0):>6.2f}/25.0")
                    print(f"    • Project Maturity:      {breakdown.get('project_maturity', 0):>6.2f}/25.0")
                    print(f"    • Algorithmic Quality:   {breakdown.get('algorithmic_quality', 0):>6.2f}/20.0")

                    # Enhanced factors
                    if "individual_contribution" in breakdown:
                        print(f"\n  Enhanced Factors (55% weight):")
                        print(f"    • Individual Contribution: {breakdown.get('individual_contribution', 0):>6.2f}/30.0")
                        print(f"    • Recency:                 {breakdown.get('recency', 0):>6.2f}/15.0")
                        print(f"    • Project Scale:           {breakdown.get('project_scale', 0):>6.2f}/10.0")
                        print(f"    • Collaboration Diversity: {breakdown.get('collaboration_diversity', 0):>6.2f}/10.0")
                        print(f"    • Activity Duration:       {breakdown.get('activity_duration', 0):>6.2f}/10.0")

                # Show justifications for enhanced factors
                if justification and "individual_contribution" in justification:
                    print(f"\nEnhanced Ranking Details:")
                    print(f"  • Contribution: {justification.get('individual_contribution', 'N/A')}")
                    print(f"  • Recency: {justification.get('recency', 'N/A')}")
                    print(f"  • Scale: {justification.get('project_scale', 'N/A')}")
                    print(f"  • Collaboration: {justification.get('collaboration_diversity', 'N/A')}")
                    print(f"  • Duration: {justification.get('activity_duration', 'N/A')}")

                if user_email and justification.get("target_user"):
                    print(f"\n  Target User Analysis:")
                    print(f"    {justification['target_user']}")

                print(f"{'=' * 60}\n")
        except Exception as e:
            print(f"\nWarning: Could not calculate enhanced ranking: {e}")

        # Complexity Analysis (Python)
        complexity_analysis = project.get("complexity_analysis", {})
        if complexity_analysis and "error" not in complexity_analysis:
            print(f"\nComplexity Analysis (Python):")
            opt_score = complexity_analysis.get("optimization_score", 0.0)
            print(f"   Optimization Score: {opt_score:.1f}/100")

            # Assessment
            if opt_score >= 75:
                assessment = "Strong optimization awareness ✓"
            elif opt_score >= 50:
                assessment = "Moderate optimization awareness"
            elif opt_score >= 25:
                assessment = "Basic optimization"
            else:
                assessment = "Limited optimization awareness"
            print(f"   Assessment: {assessment}")

            # Summary statistics
            summary = complexity_analysis.get("summary", {})
            if summary:
                good_practices = []
                issues = []

                # Good practices
                for key in [
                    "efficient_data_structure",
                    "set_operations",
                    "dict_lookup",
                    "list_comprehension",
                    "generator_expression",
                    "binary_search",
                    "memoization",
                ]:
                    if summary.get(key, 0) > 0:
                        good_practices.append(f"{key.replace('_', ' ').title()}: {summary[key]}")

                # Issues
                for key in [
                    "nested_loops",
                    "inefficient_lookup",
                    "inefficient_membership_test",
                ]:
                    if summary.get(key, 0) > 0:
                        issues.append(f"{key.replace('_', ' ').title()}: {summary[key]}")

                if good_practices:
                    print(f"   Good Practices Found:")
                    for practice in good_practices[:3]:  # Show top 3
                        print(f"      • {practice}")

                if issues:
                    print(f"   Optimization Opportunities:")
                    for issue in issues:
                        print(f"      • {issue}")

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
    analyze_parser.add_argument(
        "--user-email",
        dest="user_email",
        help="Git email used to attribute and rank contributions for the requesting user",
    )
    analyze_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed complexity findings")

    # LLM arguments merged into analyze
    analyze_parser.add_argument("--prompt", help="Custom analysis prompt for AI (requires consent)")
    analyze_parser.add_argument(
        "--architecture",
        action="store_true",
        help="AI: Deep analysis of patterns and anti-patterns",
    )
    analyze_parser.add_argument(
        "--security",
        action="store_true",
        help="AI: Logic-based security and defensive coding",
    )
    analyze_parser.add_argument(
        "--skills",
        action="store_true",
        help="AI: Infer soft skills and testing maturity",
    )
    analyze_parser.add_argument("--domain", action="store_true", help="AI: Domain-specific best practices")
    analyze_parser.add_argument(
        "--resume",
        action="store_true",
        help="AI: Generate resume and portfolio artifacts",
    )
    analyze_parser.add_argument("--all", action="store_true", help="AI: Enable all deep analysis features")

    # Analyze-essay command
    essay_parser = subparsers.add_parser("analyze-essay", help="Analyze an essay or document")
    essay_parser.add_argument("path", help="Path to the document file (.txt, .pdf, .docx, .md)")

    # Timeline command
    timeline_parser = subparsers.add_parser("timeline", help="Show chronological timelines from stored analyses")
    timeline_parser.add_argument(
        "type",
        choices=["projects", "skills", "all-skills"],
        help="Timeline type to display",
    )

    # Curation command
    curate_parser = subparsers.add_parser("curate", help="Curate project information and presentation")
    curate_subparsers = curate_parser.add_subparsers(dest="curate_type", help="Curation options")

    # Chronology correction
    chrono_parser = curate_subparsers.add_parser("chronology", help="Correct project dates and chronology")

    # Comparison attributes
    comparison_parser = curate_subparsers.add_parser("comparison", help="Select attributes for project comparison")

    # Project re-ranking
    rerank_parser = curate_subparsers.add_parser("rerank", help="Allows the rer-ranking of projects based on your preference")

    skills_parser = curate_subparsers.add_parser("skills-highlight", help="Select up to 10 skills to highlight")

    # Showcase projects
    showcase_parser = curate_subparsers.add_parser("showcase", help="Select top 3 projects to showcase")

    # Status overview
    status_parser = curate_subparsers.add_parser("status", help="Show current curation settings")

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
                print("\nConsent Update")
                print("------------------")

                if has_consented:
                    choice = input("You have already provided consent. Do you want to revoke consent? (y/n): ").strip().lower()
                    if choice in ("y", "yes"):
                        save_user_consent(username, False)
                        print("\nConsent revoked. AI-powered features have been disabled.")
                    else:
                        print("\nConsent remains active. No changes made.")
                    return 0

                print("Consent Required")
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
            has_consented = check_user_consent(username)

            llm_features_requested = (
                args.all or args.prompt or args.architecture or args.security or args.skills or args.domain or args.resume
            )

            if not has_consented and llm_features_requested:
                print("\nPlease provide consent before using AI-powered analysis features")
                print("Run 'mda consent --update' to view and accept the consent form")
                return 1

            path = Path(args.path)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return 1

            if args.complexity and not args.all:
                # Note: If --all is passed, we assume LLM complexity analysis is desired unless specified otherwise,
                # but standard complexity requires zip.
                # For backward compatibility, strict --complexity uses the non-LLM tool if zip is provided.
                if path.is_file() and path.suffix.lower() == ".zip":
                    print(f"\n[*] Analyzing Python code complexity in: {path.name}")
                    return analyze_complexity(path, args.verbose)
                elif args.complexity:
                    print("\n❌ Traditional complexity analysis requires a ZIP file. Continuing with standard analysis...")

            # Validate path type
            if not path.is_dir() and not (path.is_file() and path.suffix.lower() == ".zip"):
                print(f"\nPath must be a directory or ZIP file: {path}")
                return 1

            # Build targets: if directory contains zip children, analyze each zip; otherwise analyze the path itself
            targets: list[Path] = []
            if path.is_dir():
                # Only consider top-level zips (no recursion) to avoid treating nested archives as projects
                zip_children = sorted(path.glob("*.zip"))
                if zip_children:
                    targets.extend(zip_children)
                else:
                    targets.append(path)
            else:
                targets.append(path)

            batch_results = []

            # Run analysis with error handling
            try:
                for target_path in targets:
                    print(f"\n[*] Analyzing: {target_path}")
                    results = analyze_folder(target_path, target_user_email=args.user_email)
                    display_analysis(results)
                    batch_results.append(results)

                    # Store analysis in database
                    try:
                        import json

                        from .analysis_database import (get_analysis,
                                                        get_connection,
                                                        record_analysis)

                        analysis_id = None
                        analysis_uuid = None

                        if not has_consented:
                            analysis_id = record_analysis("non_llm", results, username=username)
                            row = get_analysis(analysis_id)
                            if row:
                                analysis_uuid = row["analysis_uuid"]
                                # Stored UUID in results metadata for consistency
                                results.setdefault("analysis_metadata", {})["analysis_uuid"] = analysis_uuid
                                print(f"\nAnalysis saved to database (ID: {analysis_id}, UUID: {analysis_uuid})")
                            else:
                                print(f"\nAnalysis saved to database (ID: {analysis_id})")

                        else:
                            print("\n[i] Standard analysis complete. Proceeding with AI analysis...")

                            # temporary UUID for tracking (NOT written to DB)
                            import uuid

                        analysis_id = record_analysis("non_llm", results, username=username)
                        analysis_uuid = results.get("analysis_metadata", {}).get("analysis_uuid", "unknown")
                        print(f"\nAnalysis saved to database (ID: {analysis_id}, UUID: {analysis_uuid})")

                        # Ask if user wants to add more projects incrementally
                        while True:
                            try:
                                response = (
                                    input("\n" + "=" * 70 + "\nWould you like to add more projects to this portfolio? (y/N): ")
                                    .strip()
                                    .lower()
                                )
                                if response in ["y", "yes"]:
                                    additional_path = input("Enter path to additional ZIP file or folder: ").strip()
                                    if not additional_path:
                                        print("No path provided, skipping...")
                                        break

                                    additional_path = Path(additional_path).expanduser()
                                    if not additional_path.exists():
                                        print(f"Error: Path does not exist: {additional_path}")
                                        continue

                                    print(f"\n[*] Analyzing additional projects from: {additional_path}")
                                    new_results = analyze_folder(
                                        additional_path,
                                        target_user_email=args.user_email,
                                        quick_mode=True,
                                    )

                                    # Merge with existing results
                                    existing_projects = results.get("projects", [])
                                    new_projects = new_results.get("projects", [])

                                    # Deduplicate by project_path
                                    existing_paths = {p.get("project_path") for p in existing_projects}
                                    added_count = 0
                                    for proj in new_projects:
                                        if proj.get("project_path") not in existing_paths:
                                            existing_projects.append(proj)
                                            added_count += 1

                                    results["projects"] = existing_projects
                                    results["analysis_metadata"]["total_projects"] = len(existing_projects)

                                    # Update database
                                    import json

                                    from .analysis_database import \
                                        get_connection

                                    with get_connection() as conn:
                                        conn.execute(
                                            """UPDATE analyses 
                                               SET raw_json = ?, 
                                                   total_projects = ?,
                                                   analysis_timestamp = datetime('now')
                                               WHERE analysis_uuid = ?""",
                                            (
                                                json.dumps(results),
                                                len(existing_projects),
                                                analysis_uuid,
                                            ),
                                        )
                                        conn.commit()

                                    print(f"\n✓ Added {added_count} new project(s) to portfolio")
                                    print(f"✓ Total projects now: {len(existing_projects)}")
                                    print(f"✓ Portfolio UUID: {analysis_uuid}")
                                else:
                                    break
                            except KeyboardInterrupt:
                                print("\n\nIncremental upload cancelled.")
                                break
                            except Exception as e:
                                print(f"\nError adding projects: {e}")
                                break

                    except Exception as db_error:
                        print(f"\nWarning: Could not save to database: {db_error}")

                # Contribution-aware ranking across all processed projects
                if args.user_email and batch_results:
                    aggregated_projects = []
                    for report in batch_results:
                        meta = report.get("analysis_metadata", {}) or {}
                        ts = meta.get("analysis_timestamp", "Unknown")
                        zip_file = meta.get("zip_file", "Unknown")
                        for proj in report.get("projects", []):
                            score_data = calculate_composite_score(proj)
                            aggregated_projects.append(
                                {
                                    "project": proj,
                                    "score_data": score_data,
                                    "analysis_timestamp": ts,
                                    "zip_file": zip_file,
                                }
                            )
                    if aggregated_projects:
                        aggregated_projects.sort(
                            key=lambda x: x["score_data"].get("adjusted_score", x["score_data"]["composite_score"]),
                            reverse=True,
                        )
                        print("\n" + "=" * 78)
                        print(f"  CONTRIBUTION-AWARE RANKING (target: {args.user_email})")
                        print("=" * 78)
                        for idx, item in enumerate(aggregated_projects, 1):
                            proj = item["project"]
                            score = item["score_data"]
                            adjusted = score.get("adjusted_score", score["composite_score"])
                            user_score = score.get("user_contribution_score", 0.0)
                            print(f"\nRANK #{idx}: {proj.get('project_name', 'Unknown Project')}")
                            print(f"  Source: {item['zip_file']}")
                            print(f"  Adjusted Score: {adjusted:.2f} (User boost: {user_score:.2f})")
                            print(f"  Composite Score: {score['composite_score']:.2f}")
                            if user_score == 0.0:
                                print("  Target user contribution: none detected for this project")

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
                            print(f" Failed to create zip for AI analysis: {e}")
                            has_consented = False  # Abort LLM part

                    if has_consented:
                        # Collect active features
                        active_features = []
                        if args.all:
                            active_features = [
                                "architecture",
                                "complexity",
                                "security",
                                "skills",
                                "domain",
                                "resume",
                            ]
                        else:
                            if args.architecture:
                                active_features.append("architecture")
                            if args.complexity:
                                active_features.append("complexity")
                            if args.security:
                                active_features.append("security")
                            if args.skills:
                                active_features.append("skills")
                            if args.domain:
                                active_features.append("domain")
                            if args.resume:
                                active_features.append("resume")

                        try:
                            from rich.progress import (BarColumn, Progress,
                                                       SpinnerColumn,
                                                       TaskProgressColumn,
                                                       TextColumn)

                            from .analysis.llm_pipeline import \
                                run_gemini_analysis

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
                            console.print(
                                Panel.fit(
                                    "[bold white]Gemini Deep Code Analysis[/bold white]",
                                    style="blue",
                                )
                            )

                            llm_summary = llm_results.get("llm_summary")
                            llm_error = llm_results.get("llm_error")

                            if llm_error:
                                console.print(
                                    Panel(
                                        f"[bold red]Error:[/bold red]\n{llm_error}",
                                        style="red",
                                    )
                                )
                            elif llm_summary:
                                md = Markdown(llm_summary)
                                console.print(
                                    Panel(
                                        md,
                                        title="[bold green]AI-Powered Insights[/bold green]",
                                        border_style="green",
                                    )
                                )

                            # Store LLM analysis in database
                            try:
                                from .analysis_database import record_analysis

                                llm_results["non_llm_results"] = results
                                llm_id = record_analysis("llm", llm_results, username=username)
                                print(f"\n AI analysis saved to database (ID: {llm_id})")

                            except Exception as db_error:
                                print(f"\n Warning: Could not save AI results: {db_error}")

                        except Exception as e:
                            print(f"\nAI analysis failed: {e}")
                            # Don't fail the whole command, standard analysis succeeded

                        finally:
                            # Cleanup temp zip if we created one
                            if temp_llm_zip and temp_llm_zip.exists():
                                temp_llm_zip.unlink()

                else:
                    print("\n[i] AI-powered analysis skipped (No consent provided).")
                    print("    Run 'mda consent --update' to enable deep code insights.")

                # Prompt to save JSON output
                print("\n" + "=" * 70)
                try:
                    response = input("Would you like to save the full analysis as JSON? (y/N): ").strip().lower()
                except (EOFError, OSError):
                    response = "n"
                if response in ["y", "yes"]:
                    import json
                    from datetime import datetime

                    # decide which dictionary to use
                    final_results = llm_results if "llm_results" in locals() and llm_features_requested else results

                    # Generate filename based on project name and timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    is_llm = "llm_results" in locals() and llm_features_requested
                    default_filename = f"analysis_{timestamp}.json"

                    filename = input(f"Enter filename (default: {default_filename}): ").strip()
                    if not filename:
                        filename = default_filename

                    # Ensure .json extension
                    if not filename.endswith(".json"):
                        filename += ".json"

                    try:
                        output_path = Path(filename)
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(final_results, f, indent=2, ensure_ascii=False)
                        print(f"Analysis saved to: {output_path.absolute()}")
                    except Exception as e:
                        print(f"Error saving JSON file: {e}")

                try:
                    # Generate resume highlights
                    from .analysis.resume_generator import print_resume_items

                    print_resume_items(results)

                    # Generate portfolio items (separate from resume)
                    from .analysis.portfolio_item_generator import \
                        generate_portfolio_item

                    print("\n" + "=" * 70)
                    print("  GENERATED PORTFOLIO ITEMS")
                    print("=" * 70)

                    for project in results.get("projects", []):
                        try:
                            portfolio_item = generate_portfolio_item(project)

                            print(f"\n{'━' * 70}")
                            print(f"PROJECT: {portfolio_item.get('project_name', 'Unknown')}")
                            print(f"{'━' * 70}")

                            # Project statistics
                            stats = portfolio_item.get("project_statistics", {})
                            quality_score = stats.get("quality_score", 0)
                            sophistication = stats.get("sophistication_level", "basic")

                            print(f"\nSophistication Level: {sophistication.title()}")
                            print(f"Quality Score: {quality_score}/100")

                            # Technology Stack
                            tech_stack = portfolio_item.get("tech_stack", [])
                            if tech_stack:
                                print(f"\nTech Stack: {', '.join(tech_stack[:5])}")
                                if len(tech_stack) > 5:
                                    print(f"   ... and {len(tech_stack) - 5} more")

                            # Text Summary (main description)
                            text_summary = portfolio_item.get("text_summary", "")
                            if text_summary:
                                print(f"\nSummary:")
                                # Wrap text to 70 characters
                                words = text_summary.split()
                                line = "   "
                                for word in words:
                                    if len(line) + len(word) + 1 > 73:
                                        print(line)
                                        line = "   " + word
                                    else:
                                        line += (" " if line != "   " else "") + word
                                if line.strip():
                                    print(line)

                            # Skills exercised
                            skills = portfolio_item.get("skills_exercised", [])
                            if skills:
                                print(f"\nSkills Demonstrated: {', '.join(skills[:5])}")

                            # File statistics
                            print(f"\nProject Metrics:")
                            print(f"   Total Files: {stats.get('total_files', 0)}")
                            print(f"   Source Files: {stats.get('code_files', 0)}")
                            print(f"   Test Files: {stats.get('test_files', 0)}")

                        except Exception as e:
                            print(
                                f"\n   Warning: Could not generate portfolio item for {project.get('project_name', 'project')}: {e}"
                            )
                            import traceback

                            traceback.print_exc()

                    print("\n" + "=" * 70 + "\n")
                except Exception:
                    print(f"\n❌ Output of resume or portfolio error: {path}")
                    return 1

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

        elif args.command == "timeline":
            # No login/consent required to view previously stored aggregate timelines
            from .analysis.chronology import (get_all_skills_chronological,
                                              get_projects_timeline,
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
                print("\nProjects Timeline (by commit date):")
                for i, e in enumerate(entries, 1):
                    # Determine which date to display and its source
                    if e.last_commit_date:
                        display_date = e.last_commit_date
                        date_source = "commit"
                    elif e.last_modified_date:
                        display_date = e.last_modified_date
                        date_source = "modified"
                    else:
                        display_date = e.analysis_timestamp
                        date_source = "analysis"

                    print(f"  {i}. {display_date} ({date_source}) — {e.project_name}")
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
                print("\nSkills Timeline (by commit date):")
                for i, e in enumerate(entries, 1):
                    langs = ", ".join(e.skills.get("languages", [])) or "-"
                    fws = ", ".join(e.skills.get("frameworks", [])) or "-"
                    detailed_skills = e.skills.get("detailed_skills", [])
                    print(f"  {i}. {e.date}")
                    print(f"     Languages: {langs}")
                    print(f"     Frameworks: {fws}")
                    if detailed_skills:
                        print(f"     Detailed Skills ({len(detailed_skills)}):")
                        # Display skills in a wrapped format
                        skills_text = ", ".join(detailed_skills)
                        words = skills_text.split(", ")
                        line = "        "
                        for word in words:
                            if len(line) + len(word) + 2 > 73:
                                print(line.rstrip())
                                line = "        " + word
                            else:
                                line += (", " if line != "        " else "") + word
                        if line.strip():
                            print(line.rstrip())
                return 0

            elif args.type == "all-skills":
                skills = get_all_skills_chronological()
                if not skills:
                    print("\nNo skills found in the analysis database.")
                    return 0
                print("\nChronological List of All Skills Exercised:")
                print("=" * 70)

                # Group by date for better display
                current_date = None
                for i, skill_entry in enumerate(skills, 1):
                    if current_date != skill_entry.first_exercised_date:
                        if current_date is not None:
                            print()  # Blank line between dates
                        current_date = skill_entry.first_exercised_date
                        print(f"\n{current_date}:")

                    skill_type_label = {
                        "language": "Language",
                        "framework": "Framework",
                        "detailed_skill": "Skill",
                    }.get(skill_entry.skill_type, "Skill")

                    print(f"  {i}. [{skill_type_label}] {skill_entry.skill}")
                    print(f"     First used in: {skill_entry.project_name}")

                print(f"\n{'=' * 70}")
                print(f"Total unique skills: {len(skills)}")
                return 0

        elif args.command == "curate":
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1

            username = session["username"]

            # Initialize curation tables
            try:
                from .curation import init_curation_tables
                from .curation_cli import (
                    curate_chronology_interactive,
                    curate_comparison_attributes_interactive,
                    curate_project_rank_interactive,
                    curate_showcase_projects_interactive,
                    curate_skills_highlight_interactive,
                    display_curation_status, display_showcase_summary)

                init_db()
                init_curation_tables()
            except Exception as e:
                print(f"\nError initializing curation: {e}")
                return 1

            if args.curate_type == "chronology":
                curate_chronology_interactive(username)
                return 0
            elif args.curate_type == "comparison":
                curate_comparison_attributes_interactive(username)
                return 0
            elif args.curate_type == "showcase":
                curate_showcase_projects_interactive(username)
                return 0
            elif args.curate_type == "status":
                display_curation_status(username)
                display_showcase_summary(username)
                return 0
            elif args.curate_type == "rerank":
                curate_project_rank_interactive(username)
                return 0
            elif args.curate_type == "skills-highlight":
                curate_skills_highlight_interactive(username)
                return 0
            else:
                print("\nAvailable curation commands:")
                print("  mda curate chronology  - Correct project dates")
                print("  mda curate comparison  - Select comparison attributes")
                print("  mda curate showcase    - Choose top 3 projects")
                print("  mda curate status      - Show current settings")
                print("  mda curate rerank      - Re-rank projects")
                print("  mda curate skills-highlight - Choose up to 10 skills to display")

                return 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
