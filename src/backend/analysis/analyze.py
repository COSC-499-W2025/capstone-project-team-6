#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Analysis Script - Local Code Analysis (Privacy-Preserving)

This script performs comprehensive LOCAL analysis without sending data externally.
All analysis happens on your device using Python AST parsers and static analysis.

Usage:
    python src/backend/analysis/analyze.py <zip_file_path>

For AI-enhanced analysis (requires Google Gemini consent):
    Use the CLI: mda analyze-llm <zip_file_path>

Features (Local Analysis):
    - OOP metrics (Python, Java, C++, C)
    - Complexity analysis
    - Git history and contributor analysis
    - Framework and language detection
    - Project quality scoring
    - Resume item generation
"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configure stdout/stderr to use UTF-8 encoding on Windows to handle Unicode characters
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add paths for imports
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
src_dir = backend_dir.parent

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from analysis.deep_code_analyzer import generate_comprehensive_report
from analysis.resume_generator import (generate_formatted_resume_entry,
                                       print_resume_items)

from backend.analysis.portfolio_item_generator import generate_portfolio_item
from backend.analysis_database import (count_analyses_by_zip_file,
                                       delete_analyses_by_zip_file,
                                       get_all_analyses,
                                       get_all_analyses_by_zip_file,
                                       get_analysis_by_zip_file,
                                       get_analysis_report, get_connection,
                                       get_resume_items_for_project, init_db,
                                       record_analysis, store_resume_item)


def print_separator(title=""):
    """Print a separator line."""
    if title:
        print(f"\n{'=' * 78}")
        print(f"  {title}")
        print(f"{'=' * 78}\n")
    else:
        print("=" * 78)


def calculate_composite_score(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a comprehensive composite score for a project using a balanced multi-factor approach.

    New Scoring System (total: 100 points):
    - Code Architecture (30 points): OOP principles, SOLID design, design patterns
    - Code Quality (25 points): Test coverage, code organization, documentation
    - Project Maturity (25 points): CI/CD, Docker, Git activity, project structure
    - Algorithmic Quality (20 points): Complexity awareness, optimization patterns

    This system balances theoretical code quality with practical project health indicators.
    """
    score_breakdown = {
        "code_architecture": 0.0,
        "code_quality": 0.0,
        "project_maturity": 0.0,
        "algorithmic_quality": 0.0,
    }

    # this is architecture score, 30 points total. metrics: OOP, SOLID, Design Patterns
    architecture_scores = []
    architecture_details = []

    oop_scores = []
    solid_scores = []
    design_patterns_count = 0

    # Python OOP & SOLID
    if "oop_analysis" in project:
        python_oop = project["oop_analysis"]
        if "error" not in python_oop:
            oop_score = python_oop.get("oop_score", 0)
            solid_score = python_oop.get("solid_score", 0.0)

            if oop_score > 0:
                oop_scores.append((oop_score / 6.0) * 100)
            if solid_score > 0:
                solid_scores.append((solid_score / 5.0) * 100)

            design_patterns = python_oop.get("design_patterns", [])
            if design_patterns:
                design_patterns_count += len(design_patterns)
                architecture_details.append(f"Python: {len(design_patterns)} design pattern(s)")

    # Java OOP & SOLID
    if "java_oop_analysis" in project:
        java_oop = project["java_oop_analysis"]
        if "error" not in java_oop:
            oop_score = java_oop.get("oop_score", 0)
            if oop_score == 0:
                from analysis.java_oop_analyzer import (JavaOOPAnalysis,
                                                        calculate_oop_score)

                try:
                    analysis_obj = JavaOOPAnalysis(**java_oop)
                    oop_score = calculate_oop_score(analysis_obj)
                except:
                    oop_score = 0

            if oop_score > 0:
                oop_scores.append((oop_score / 6.0) * 100)

            solid_score = java_oop.get("solid_score", 0.0)
            if solid_score == 0:
                from analysis.java_oop_analyzer import calculate_solid_score

                try:
                    analysis_obj = JavaOOPAnalysis(**java_oop)
                    solid_score = calculate_solid_score(analysis_obj)
                except:
                    solid_score = 0.0

            if solid_score > 0:
                solid_scores.append((solid_score / 5.0) * 100)

            design_patterns = java_oop.get("design_patterns", [])
            if design_patterns:
                design_patterns_count += len(design_patterns)
                architecture_details.append(f"Java: {len(design_patterns)} design pattern(s)")

    # C++ OOP & SOLID
    if "cpp_oop_analysis" in project:
        cpp_oop = project["cpp_oop_analysis"]
        if "error" not in cpp_oop:
            from analysis.cpp_oop_analyzer import (CppOOPAnalysis,
                                                   calculate_oop_score,
                                                   calculate_solid_score)

            try:
                analysis_obj = CppOOPAnalysis(**cpp_oop)
                oop_score = calculate_oop_score(analysis_obj)
                if oop_score > 0:
                    oop_scores.append((oop_score / 6.0) * 100)

                solid_score = calculate_solid_score(analysis_obj)
                if solid_score > 0:
                    solid_scores.append((solid_score / 5.0) * 100)

                design_patterns = cpp_oop.get("design_patterns", [])
                if design_patterns:
                    design_patterns_count += len(design_patterns)
                    architecture_details.append(f"C++: {len(design_patterns)} design pattern(s)")
            except:
                pass

    # C OOP-style patterns
    if "c_oop_analysis" in project:
        c_oop = project["c_oop_analysis"]
        if "error" not in c_oop:
            c_architecture_score = 0.0
            if c_oop.get("opaque_pointer_structs", 0) > 0:
                c_architecture_score += 25
            if c_oop.get("vtable_structs", 0) > 0:
                c_architecture_score += 25
            if c_oop.get("function_pointer_fields", 0) > 0:
                c_architecture_score += 20
            if c_oop.get("static_functions", 0) > 0:
                c_architecture_score += 15
            if c_oop.get("design_patterns"):
                c_architecture_score += 15
                design_patterns_count += len(c_oop.get("design_patterns", []))

            if c_architecture_score > 0:
                architecture_scores.append(min(c_architecture_score, 100))

    # with this we calculate the architecture score, 60% OOP, 30% SOLID, 10% design patterns
    architecture_total = 0.0
    has_oop_or_solid = False

    if oop_scores:
        architecture_total += (sum(oop_scores) / len(oop_scores)) * 0.6
        has_oop_or_solid = True
    if solid_scores:
        architecture_total += (sum(solid_scores) / len(solid_scores)) * 0.3
        has_oop_or_solid = True
    if design_patterns_count > 0:
        # Design patterns: 0-3 patterns = 0-10%, 4+ = 10%
        pattern_bonus = min(design_patterns_count * 2.5, 10)
        architecture_total += pattern_bonus * 0.1

    # If we have C-style architecture scores, use them if no OOP/SOLID scores
    if architecture_scores and not has_oop_or_solid:
        architecture_total = sum(architecture_scores) / len(architecture_scores)
    elif architecture_scores and has_oop_or_solid:
        # Average both if we have both types
        c_avg = sum(architecture_scores) / len(architecture_scores)
        architecture_total = (architecture_total + c_avg) / 2

    score_breakdown["code_architecture"] = min(architecture_total, 100) * 0.30

    # coding practices, 25 points total. metrics: Tests, Documentation, Organization
    quality_score = 0.0
    quality_details = []

    # tests-10pts
    total_files = project.get("total_files", 0)
    test_files = project.get("test_files", 0)
    code_files = project.get("code_files", 0)

    if total_files > 0 and code_files > 0:
        test_ratio = (
            test_files / code_files
        )  # the ratio is defined as the number of test files divided by the number of code files.
        if (
            test_ratio >= 0.5
        ):  # we use the ratio because it is a more accurate measure of test coverage than the number of test files alone.
            quality_score += 10  # higher ratio means more test coverage.
            quality_details.append("Excellent test coverage (≥50%)")
        elif test_ratio >= 0.3:
            quality_score += 7
            quality_details.append("Good test coverage (30-50%)")
        elif test_ratio >= 0.15:
            quality_score += 5
            quality_details.append("Moderate test coverage (15-30%)")
        elif test_ratio > 0:
            quality_score += 2
            quality_details.append("Low test coverage (<15%)")
        else:
            quality_details.append("No tests found")

    # Documentation (5 points)
    doc_files = project.get("doc_files", 0)
    has_readme = project.get("has_readme", False)
    if doc_files > 0 or has_readme:
        if doc_files >= 3 or (has_readme and doc_files >= 1):
            quality_score += 5
            quality_details.append("Good documentation")
        else:
            quality_score += 2
            quality_details.append("Basic documentation")
    else:
        quality_details.append("No documentation")

    # Code organization: defined as the depth of the directory structure (10 points)
    directory_depth = project.get("directory_depth", 0)
    config_files = project.get("config_files", 0)

    # Structure depth indicates organization
    if directory_depth >= 4:
        quality_score += 5
        quality_details.append("Well-organized structure")
    elif directory_depth >= 2:
        quality_score += 3
        quality_details.append("Moderate organization")
    else:
        quality_details.append("Flat structure")

    # configuration management: defined as the number of configuration files such as .json, .yml, .yaml, .ini, etc. (3 points)
    if config_files >= 3:
        quality_score += 3
        quality_details.append("Good config management")
    elif config_files > 0:
        quality_score += 1
        quality_details.append("Basic config")

    # File size distribution (2 points) - projects with reasonable file sizes
    largest_file = project.get("largest_file")
    if largest_file and largest_file.get("size_mb", 0) < 1.0:
        quality_score += 2
        quality_details.append("Reasonable file sizes")

    score_breakdown["code_quality"] = min(quality_score, 25) * 0.25

    # DevOps practices, 25 points total. metrics: CI/CD, Docker, Git activity, Test infrastructure etc
    maturity_score = 0.0
    maturity_details = []

    # CI/CD (8 points)
    if project.get("has_ci_cd", False):
        maturity_score += 8
        maturity_details.append("CI/CD configured")
    else:
        maturity_details.append("No CI/CD")

    # Docker (5 points)
    if project.get("has_docker", False):
        maturity_score += 5
        maturity_details.append("Dockerized")
    else:
        maturity_details.append("No Docker")

    # Git activity (7 points)
    is_git_repo = project.get("is_git_repo", False)
    total_commits = project.get("total_commits", 0)

    if is_git_repo:
        maturity_score += 3
        if total_commits >= 100:
            maturity_score += 4
            maturity_details.append(f"Active Git repo ({total_commits} commits)")
        elif total_commits >= 20:
            maturity_score += 2
            maturity_details.append(f"Moderate Git activity ({total_commits} commits)")
        else:
            maturity_details.append(f"New Git repo ({total_commits} commits)")
    else:
        maturity_details.append("Not a Git repo")

    # Test infrastructure (5 points)
    has_tests = project.get("has_tests", False)
    coverage_estimate = project.get("test_coverage_estimate", "").lower()

    if has_tests:
        maturity_score += 2
        if coverage_estimate == "high":
            maturity_score += 3
            maturity_details.append("High test coverage")
        elif coverage_estimate == "medium":
            maturity_score += 2
            maturity_details.append("Medium test coverage")
        else:
            maturity_details.append("Tests present")
    else:
        maturity_details.append("No test infrastructure")

    score_breakdown["project_maturity"] = min(maturity_score, 25) * 0.25

    # algorithmic quality, 20 points total. metrics: Complexity, Optimization
    # currently only python is supported for this metric.
    # the score is calculated based on the optimization score from the complexity analysis.
    # we will add support for other languages in the future probably during the winter break
    algorithmic_score = 0.0
    algorithmic_details = []

    if "complexity_analysis" in project:
        complexity = project["complexity_analysis"]
        if "error" not in complexity:
            opt_score = complexity.get("optimization_score", 0.0)
            algorithmic_score = opt_score
            if opt_score >= 75:
                algorithmic_details.append("Strong algorithmic optimization")
            elif opt_score >= 50:
                algorithmic_details.append("Moderate optimization awareness")
            elif opt_score >= 25:
                algorithmic_details.append("Basic optimization")
            else:
                algorithmic_details.append("Limited optimization awareness")
        else:
            algorithmic_details.append("Complexity analysis unavailable")
    else:
        algorithmic_details.append("No complexity analysis")

    score_breakdown["algorithmic_quality"] = algorithmic_score * 0.20

    # total
    total_score = sum(score_breakdown.values())

    # justifications for the architecture score
    arch_justification = []
    if oop_scores:
        arch_justification.append(f"OOP: {sum(oop_scores)/len(oop_scores):.1f}/100")
    if solid_scores:
        arch_justification.append(f"SOLID: {sum(solid_scores)/len(solid_scores):.1f}/100")
    if design_patterns_count > 0:
        arch_justification.append(f"{design_patterns_count} design pattern(s)")
    if not arch_justification:
        arch_justification.append("No architecture analysis")

    return {
        "composite_score": total_score,
        "breakdown": score_breakdown,
        "justification": {
            "code_architecture": "; ".join(arch_justification)
            + (" | " + "; ".join(architecture_details) if architecture_details else ""),
            "code_quality": "; ".join(quality_details) if quality_details else "No quality metrics",
            "project_maturity": "; ".join(maturity_details) if maturity_details else "No maturity indicators",
            "algorithmic_quality": "; ".join(algorithmic_details) if algorithmic_details else "No algorithmic analysis",
        },
    }


def summarize_top_ranked_projects(limit: int = 10, zip_file_path: Optional[str] = None) -> None:
    """
    Retrieve projects from the database, calculate composite scores,
    """
    if zip_file_path:
        print_separator(f"TOP RANKED PROJECTS SUMMARY - {Path(zip_file_path).name}")
    else:
        print_separator("TOP RANKED PROJECTS SUMMARY (ALL ZIP FILES)")

    # Get analyses - filter by zip_file_path if provided
    if zip_file_path:
        all_analyses = get_all_analyses_by_zip_file(zip_file_path)
    else:
        # Get all analyses
        all_analyses = get_all_analyses()

    if not all_analyses:
        if zip_file_path:
            print(f"No analyses found for {Path(zip_file_path).name}.")
        else:
            print("No analyses found in database.")
        return

    projects_with_scores = []

    for analysis in all_analyses:
        try:
            report = json.loads(analysis["raw_json"])
            projects = report.get("projects", [])

            for project in projects:
                score_data = calculate_composite_score(project)

                try:
                    analysis_timestamp = analysis["analysis_timestamp"]
                except (KeyError, IndexError):
                    analysis_timestamp = "Unknown"

                try:
                    zip_file = analysis["zip_file"]
                except (KeyError, IndexError):
                    zip_file = "Unknown"

                projects_with_scores.append(
                    {
                        "project": project,
                        "score_data": score_data,
                        "analysis_timestamp": analysis_timestamp,
                        "zip_file": zip_file,
                    }
                )
        except (json.JSONDecodeError, KeyError) as e:
            try:
                analysis_id = analysis["id"]
            except (KeyError, IndexError):
                analysis_id = "unknown"
            print(f"Warning: Could not parse analysis {analysis_id}: {e}")
            continue

    if not projects_with_scores:
        print("No projects found in analyses.")
        return

    # Deduplicate by project name - keep the best version (highest score, then most recent)
    unique_projects = {}
    for item in projects_with_scores:
        project_name = item["project"].get("project_name", "Unknown Project")
        project_path = item["project"].get("project_path", "")
        # Use project_name + project_path as unique key to handle projects with same name in different locations
        unique_key = f"{project_name}::{project_path}"

        if unique_key not in unique_projects:
            unique_projects[unique_key] = item
        else:
            existing = unique_projects[unique_key]
            existing_score = existing["score_data"]["composite_score"]
            new_score = item["score_data"]["composite_score"]

            if new_score > existing_score:
                unique_projects[unique_key] = item
            elif new_score == existing_score:
                if item["analysis_timestamp"] > existing["analysis_timestamp"]:
                    unique_projects[unique_key] = item

    # Convert back to list and sort by composite score (descending)
    projects_with_scores = list(unique_projects.values())
    projects_with_scores.sort(key=lambda x: x["score_data"]["composite_score"], reverse=True)

    # Display top projects
    top_projects = projects_with_scores[:limit]

    print(f"\nFound {len(projects_with_scores)} total projects")
    print(f"Displaying top {len(top_projects)} ranked projects:\n")

    for rank, item in enumerate(top_projects, 1):
        project = item["project"]
        score_data = item["score_data"]

        print(f"{'=' * 78}")
        print(f"RANK #{rank}: {project.get('project_name', 'Unknown Project')}")
        print(f"{'=' * 78}")

        print(f"Analysis Date: {item['analysis_timestamp']}")
        print(f"\nCOMPOSITE SCORE: {score_data['composite_score']:.2f}/100.0")
        print(f"\nScore Breakdown:")
        print(
            f"  • Code Architecture:  {score_data['breakdown']['code_architecture']:.2f}/30.0  ({score_data['justification']['code_architecture']})"
        )
        print(
            f"  • Code Quality:       {score_data['breakdown']['code_quality']:.2f}/25.0  ({score_data['justification']['code_quality']})"
        )
        print(
            f"  • Project Maturity:  {score_data['breakdown']['project_maturity']:.2f}/25.0  ({score_data['justification']['project_maturity']})"
        )
        print(
            f"  • Algorithmic Quality: {score_data['breakdown']['algorithmic_quality']:.2f}/20.0  ({score_data['justification']['algorithmic_quality']})"
        )
        print(f"\nProject Overview:")
        print(f"  • Primary Language: {project.get('primary_language', 'N/A')}")
        print(f"  • Total Files: {project.get('total_files', 0)}")
        print(f"  • Code Files: {project.get('code_files', 0)}")
        print(f"  • Test Files: {project.get('test_files', 0)}")

        languages = project.get("languages", {})
        if languages:
            lang_str = ", ".join([f"{lang} ({count})" for lang, count in list(languages.items())[:5]])
            if len(languages) > 5:
                lang_str += f" ... and {len(languages) - 5} more"
            print(f"  • Languages: {lang_str}")

        frameworks = project.get("frameworks", [])
        if frameworks:
            print(f"  • Frameworks: {', '.join(frameworks[:5])}")
            if len(frameworks) > 5:
                print(f"               ... and {len(frameworks) - 5} more")

        # OOP Analysis Summary
        print(f"\nOOP Analysis:")

        if "oop_analysis" in project and "error" not in project["oop_analysis"]:
            python_oop = project["oop_analysis"]
            print(
                f"  Python: {python_oop.get('total_classes', 0)} classes, "
                f"inheritance depth: {python_oop.get('inheritance_depth', 0)}, "
                f"encapsulation: {python_oop.get('private_methods', 0) + python_oop.get('protected_methods', 0)} private/protected methods"
            )

        if "java_oop_analysis" in project and "error" not in project["java_oop_analysis"]:
            java_oop = project["java_oop_analysis"]
            print(
                f"  Java: {java_oop.get('total_classes', 0)} classes, "
                f"{java_oop.get('interface_count', 0)} interfaces, "
                f"SOLID score: {java_oop.get('solid_score', 0.0):.1f}/5.0"
            )

        if "cpp_oop_analysis" in project and "error" not in project["cpp_oop_analysis"]:
            cpp_oop = project["cpp_oop_analysis"]
            print(
                f"  C++: {cpp_oop.get('total_classes', 0)} classes, "
                f"{cpp_oop.get('template_classes', 0)} templates, "
                f"virtual methods: {cpp_oop.get('virtual_methods', 0)}"
            )

        if "c_oop_analysis" in project and "error" not in project["c_oop_analysis"]:
            c_oop = project["c_oop_analysis"]
            print(
                f"  C: {c_oop.get('total_structs', 0)} structs, "
                f"{c_oop.get('opaque_pointer_structs', 0)} opaque pointers, "
                f"{c_oop.get('vtable_structs', 0)} vtable structs"
            )

        if "complexity_analysis" in project and "error" not in project["complexity_analysis"]:
            complexity = project["complexity_analysis"]
            opt_score = complexity.get("optimization_score", 0.0)
            print(f"\n⚡ Complexity/Optimization Score: {opt_score:.1f}/100")
            print(f"\n Currently, only python is supported for this metric.")
            if opt_score >= 75:
                print(f"   Assessment: Strong algorithmic optimization awareness")
            elif opt_score >= 50:
                print(f"   Assessment: Moderate optimization awareness")
            else:
                print(f"   Assessment: Limited optimization awareness")
        print(f"\nProject Health Indicators:")
        health_items = []
        if project.get("has_tests"):
            health_items.append("✓ Tests")
        if project.get("has_readme"):
            health_items.append("✓ README")
        if project.get("has_ci_cd"):
            health_items.append("✓ CI/CD")
        if project.get("has_docker"):
            health_items.append("✓ Docker")
        if project.get("is_git_repo"):
            health_items.append("✓ Git")

        if health_items:
            print(f"   {', '.join(health_items)}")
        else:
            print(f"   No health indicators found")

        if project.get("test_coverage_estimate"):
            print(f"   Test Coverage: {project['test_coverage_estimate']}")

        print()

    print_separator()
    print(f"\nSummary complete. Top {len(top_projects)} projects displayed.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/backend/analysis/analyze.py <zip_file_path>")
        print("   or: python src/backend/analysis/analyze.py --summarize [limit]")
        print("\nExamples:")
        print("  python src/backend/analysis/analyze.py project.zip")
        print("  python src/backend/analysis/analyze.py --summarize")
        print("  python src/backend/analysis/analyze.py --summarize 5")
        sys.exit(1)

    # Check if user wants to summarize top projects
    if sys.argv[1] == "--summarize" or sys.argv[1] == "-s":
        limit = 10
        if len(sys.argv) > 2:
            try:
                limit = int(sys.argv[2])
            except ValueError:
                print(f"Warning: Invalid limit '{sys.argv[2]}', using default 10")

        init_db()
        summarize_top_ranked_projects(limit=limit)
        return

    zip_path = Path(sys.argv[1])

    if not zip_path.exists():
        print(f"Error: File not found: {zip_path}")
        sys.exit(1)

    # Initialize database
    init_db()

    print_separator("COMPLETE  ANALYSIS")
    print(f"Analyzing: {zip_path}")

    try:
        # Check if analysis already exists
        zip_file_path = str(zip_path.absolute())
        existing_report = get_analysis_report(zip_file_path)
        new_analysis_generated = False
        choice = None  # Initialize choice variable to avoid UnboundLocalError

        if existing_report:
            # Get the current analysis to show the most recent timestamp from database
            current_analysis = get_analysis_by_zip_file(zip_file_path)
            if current_analysis:
                try:
                    timestamp = current_analysis["analysis_timestamp"] or current_analysis["created_at"]
                except KeyError:
                    try:
                        timestamp = current_analysis["created_at"]
                    except KeyError:
                        timestamp = existing_report.get("analysis_metadata", {}).get("analysis_timestamp", "unknown time")
            else:
                timestamp = existing_report.get("analysis_metadata", {}).get("analysis_timestamp", "unknown time")
            print(f"\nFound existing analysis in database (from {timestamp})")
            # Check if there are analyses and ask if user wants to delete them
            total_analyses_count = count_analyses_by_zip_file(zip_file_path)
            if total_analyses_count > 0:
                print_separator("EXISTING ANALYSIS DETECTED" if total_analyses_count == 1 else "EXISTING ANALYSES DETECTED")
                print(f"  Found {total_analyses_count} analysis{'es' if total_analyses_count > 1 else ''} in database.")
                print(
                    f"  Note: Deleting analysis/analyses will remove analysis data but preserve resume items (they are shared across reports and will not be affected)."
                )
                print()
                print(f"  Options:")

                print(f"    1. Delete {total_analyses_count - 1} older analysis/analyses (keep most recent)")
                print(f"    2. Delete ALL {total_analyses_count} analysis/analyses (including most recent)")
                print(f"    3. Keep all analyses and run a new analysis")
                print()
                choice = None
                while choice not in ["1", "2", "3"]:
                    choice = input(f"Enter your choice (1/2/3): ").strip()
                    if choice not in ["1", "2", "3"]:
                        print(f"  Invalid choice. Please enter 1, 2, or 3.")

                if choice == "1":
                    # Delete older analyses (keep most recent)
                    all_analyses = get_all_analyses_by_zip_file(zip_file_path)
                    current_analysis = get_analysis_by_zip_file(zip_file_path)
                    current_analysis_id = current_analysis["id"] if current_analysis else None

                    analyses_to_delete = [a for a in all_analyses if a["id"] != current_analysis_id]
                    analyses_to_delete_count = len(analyses_to_delete)

                    if analyses_to_delete_count > 0:
                        # Show details only if more than 2 analyses
                        if analyses_to_delete_count > 2:
                            print(f"\n  Analyses to be deleted:")
                            for analysis in analyses_to_delete:
                                print(
                                    f"    - Analysis ID {analysis['id']} ({analysis['analysis_type']}) from {analysis['analysis_timestamp']}"
                                )
                            confirm = (
                                input(f"\n  Confirm deletion of {analyses_to_delete_count} older analysis/analyses? (y/n): ")
                                .lower()
                                .strip()
                            )
                        else:
                            confirm = (
                                input(f"\n  Confirm deletion of {analyses_to_delete_count} older analysis/analyses? (y/n): ")
                                .lower()
                                .strip()
                            )

                        if confirm == "y" or confirm == "yes":
                            with get_connection() as conn:
                                conn.execute("PRAGMA foreign_keys = ON;")
                                cursor = conn.execute(
                                    "DELETE FROM analyses WHERE zip_file = ? AND id != ?",
                                    (zip_file_path, current_analysis_id),
                                )
                                deleted_count = cursor.rowcount
                                conn.commit()

                            # Verify deletion worked
                            remaining_count = count_analyses_by_zip_file(zip_file_path)
                            if deleted_count > 0:
                                print(f"  ✓ Deleted {deleted_count} older analysis/analyses")
                                print(f"  ✓ {remaining_count} analysis/analyses remaining in database")
                                # Refresh the report and analysis after deletion to get updated timestamp
                                existing_report = get_analysis_report(zip_file_path)
                                # Update the displayed timestamp to reflect the current (remaining) analysis
                                if existing_report:
                                    current_analysis = get_analysis_by_zip_file(zip_file_path)
                                    if current_analysis:
                                        try:
                                            timestamp = current_analysis["analysis_timestamp"] or current_analysis["created_at"]
                                        except KeyError:
                                            timestamp = existing_report.get("analysis_metadata", {}).get(
                                                "analysis_timestamp", "unknown time"
                                            )
                                        print(f"  ✓ Now displaying analysis from {timestamp}")
                            else:
                                print(
                                    f"  ⚠ Warning: Deletion query executed but no rows were deleted (rowcount: {deleted_count})"
                                )
                                print(f"  ⚠ Current count: {remaining_count} analyses in database")
                                print(f"  ⚠ This might indicate a path mismatch issue")
                            print(f"  ✓ Resume items preserved (not affected by deletion)")
                        else:
                            print(f"  Deletion cancelled.")
                    else:
                        print(f"  No older analyses to delete.")
                elif choice == "2":
                    all_analyses = get_all_analyses_by_zip_file(zip_file_path)
                    print(f"\n  ALL analyses to be deleted:")
                    for analysis in all_analyses:
                        print(
                            f"    - Analysis ID {analysis['id']} ({analysis['analysis_type']}) from {analysis['analysis_timestamp']}"
                        )
                    confirm = (
                        input(
                            f"\n  WARNING: This will delete ALL {total_analyses_count} analysis/analyses. Confirm? (type 'yes' to confirm): "
                        )
                        .lower()
                        .strip()
                    )

                    if confirm == "yes":
                        with get_connection() as conn:
                            conn.execute("PRAGMA foreign_keys = ON;")
                            cursor = conn.execute(
                                "DELETE FROM analyses WHERE zip_file = ?",
                                (zip_file_path,),
                            )
                            deleted_count = cursor.rowcount
                            conn.commit()

                        # Verify deletion worked
                        remaining_count = count_analyses_by_zip_file(zip_file_path)
                        if deleted_count > 0:
                            print(f"  ✓ Deleted ALL {deleted_count} analysis/analyses")
                            print(f"  ✓ {remaining_count} analysis/analyses remaining in database")
                            # Clear the existing report since all analyses were deleted
                            existing_report = None
                        else:
                            print(f"  ⚠ Warning: Deletion query executed but no rows were deleted (rowcount: {deleted_count})")
                            print(f"  ⚠ Current count: {remaining_count} analyses in database")
                        print(f"  ✓ Resume items preserved (not affected by deletion)")
                    else:
                        print(f"  Deletion cancelled.")
                elif choice == "3":
                    print(f"  Keeping all existing analyses. Running new analysis...\n")

            if choice == "1":
                # Choice 1: Use existing report (after deleting older ones)
                report = existing_report
                # Don't mark as new since we're keeping the most recent
                new_analysis_generated = False
            elif choice == "2":
                # Choice 2: Use existing report but mark as new to re-store after deletion
                report = existing_report
                # Mark as new analysis to re-store it after deletion
                new_analysis_generated = True
            else:
                # Choice 3: Generate new analysis (set flag, will generate below)
                existing_report = None

        # Generate new analysis if no existing report
        if existing_report is None:
            report = generate_comprehensive_report(zip_path)
            report["analysis_metadata"] = {
                "zip_file": zip_file_path,
                "analysis_timestamp": datetime.now().isoformat(),
                "total_projects": len(report["projects"]),
            }
            new_analysis_generated = True

        # Add C++ and C analysis to the report
        for i, project in enumerate(report["projects"]):
            project_path = project.get("project_path", "")

            # C++ Analysis
            if "cpp" in project.get("languages", {}):
                try:
                    from analysis.cpp_oop_analyzer import analyze_cpp_project

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
                    from analysis.c_oop_analyzer import analyze_c_project

                    c_analysis = analyze_c_project(zip_path, project_path)
                    # Only add if we found C-style code
                    if c_analysis["c_oop_analysis"].get("total_structs", 0) > 0:
                        report["projects"][i]["c_oop_analysis"] = c_analysis["c_oop_analysis"]
                except ImportError:
                    pass  # C analyzer optional
                except Exception as e:
                    pass  # Silently skip if no C code found

        report["analysis_metadata"] = {
            "zip_file": str(zip_path.absolute()),
            "analysis_timestamp": datetime.now().isoformat(),
            "total_projects": len(report["projects"]),
        }

        print_separator("PHASE 1 & 2: FILE CLASSIFICATION + METADATA")
        # Check if analysis already exists
        zip_file_path = str(zip_path.absolute())
        existing_report = get_analysis_report(zip_file_path)

        if existing_report:
            print(
                f"\nFound existing analysis in database (from {existing_report.get('analysis_metadata', {}).get('analysis_timestamp', 'unknown time')})"
            )
            report = existing_report
        else:
            print("No existing analysis found. Running new analysis...\n")
            report = generate_comprehensive_report(zip_path)

            # Add C++ and C analysis to the report
            for i, project in enumerate(report["projects"]):
                project_path = project.get("project_path", "")

                # C++ Analysis
                if "cpp" in project.get("languages", {}):
                    try:
                        from analysis.cpp_oop_analyzer import \
                            analyze_cpp_project

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
                        from analysis.c_oop_analyzer import analyze_c_project

                        c_analysis = analyze_c_project(zip_path, project_path)
                        # Only add if we found C-style code
                        if c_analysis["c_oop_analysis"].get("total_structs", 0) > 0:
                            report["projects"][i]["c_oop_analysis"] = c_analysis["c_oop_analysis"]
                    except ImportError:
                        pass  # C analyzer optional
                    except Exception as e:
                        pass  # Silently skip if no C code found

            report["analysis_metadata"] = {
                "zip_file": zip_file_path,
                "analysis_timestamp": datetime.now().isoformat(),
                "total_projects": len(report["projects"]),
            }
            new_analysis_generated = True

        summary = report["summary"]
        print(f"Total Files: {summary['total_files']}")
        print(f"Total Projects: {len(report['projects'])}")
        print(f"Languages: {', '.join(summary['languages_used'])}")

        # Detailed project analysis
        for i, project in enumerate(report["projects"], 1):
            print(f"\n{'-' * 70}")
            print(f"Project {i}: {project['project_name']}")
            print(f"{'-' * 70}")

            print(f"\nBasic Info:")
            print(f"  Primary Language: {project.get('primary_language', 'N/A')}")
            print(f"  Path: {project.get('project_path', '(root)')}")

            print(f"\nFile Breakdown:")
            print(f"  Total: {project['total_files']}")
            print(f"  Code: {project['code_files']}")
            print(f"  Tests: {project['test_files']}")
            print(f"  Docs: {project['doc_files']}")
            print(f"  Config: {project['config_files']}")

            print(f"\nLanguages:")
            for lang, count in project.get("languages", {}).items():
                print(f"  - {lang}: {count} files")

            if project.get("frameworks"):
                print(f"\nFrameworks:")
                for fw in project["frameworks"]:
                    print(f"  - {fw}")

            if project.get("dependencies"):
                print(f"\nDependencies:")
                for pkg_mgr, deps in project["dependencies"].items():
                    print(f"  - {pkg_mgr}: {len(deps)} packages")
                    if len(deps) <= 5:
                        for dep in deps:
                            print(f"      • {dep}")
                    else:
                        for dep in deps[:5]:
                            print(f"      • {dep}")
                        print(f"      ... and {len(deps) - 5} more")

            print(f"\nProject Health:")
            print(f"  Has Tests: {'true' if project['has_tests'] else 'false'}")
            print(f"  Has README: {'true' if project['has_readme'] else 'false'}")
            print(f"  Has CI/CD: {'true' if project['has_ci_cd'] else 'false'}")
            print(f"  Has Docker: {'true' if project['has_docker'] else 'false'}")
            print(f"  Test Coverage: {project['test_coverage_estimate']}")

        # Analyze Python projects
        python_projects = [p for p in report["projects"] if "python" in p.get("languages", {})]

        if python_projects:
            print(f"\n{'*' * 70}")
            print(f"  PYTHON OOP ANALYSIS")
            print(f"{'*' * 70}\n")

            for i, project in enumerate(python_projects, 1):
                if "oop_analysis" not in project:
                    continue

                print(f"\n{'-' * 70}")
                print(f"Project {i}: {project['project_name']}")
                print(f"{'-' * 70}")

                oop = project["oop_analysis"]

                if "error" in oop:
                    print(f"\nError during analysis: {oop['error']}\n")
                    continue

                print(f"\nOOP Metrics:")
                print(f"  Total Classes: {oop['total_classes']}")

                if oop["abstract_classes"]:
                    print(f"  Abstract Classes: {', '.join(oop['abstract_classes'][:5])}")
                    if len(oop["abstract_classes"]) > 5:
                        print(f"    ... and {len(oop['abstract_classes']) - 5} more")

                print(f"  Classes with Inheritance: {oop['classes_with_inheritance']}")
                print(f"  Max Inheritance Depth: {oop['inheritance_depth']}")

                print(f"\nEncapsulation:")
                total_methods = oop["private_methods"] + oop["protected_methods"] + oop["public_methods"]
                print(f"  Total Methods: {total_methods}")
                print(f"    - Private (__name): {oop['private_methods']}")
                print(f"    - Protected (_name): {oop['protected_methods']}")
                print(f"    - Public: {oop['public_methods']}")
                print(f"  Properties (@property): {oop['properties_count']}")

                print(f"\nPolymorphism:")
                print(f"  Operator Overloads: {oop['operator_overloads']}")

                # Use pre-calculated OOP score from deep_code_analyzer
                oop_score = oop.get("oop_score", 0)
                solid_score = oop.get("solid_score", 0.0)

                # Fallback calculation if not present (shouldn't happen with deep_code_analyzer)
                if oop_score == 0:
                    score = 0
                    if oop["total_classes"] > 0:
                        score += 1
                    if oop["abstract_classes"]:
                        score += 1
                    if oop["inheritance_depth"] > 0:
                        score += 1
                    if oop["private_methods"] > 0 or oop["protected_methods"] > 0:
                        score += 1
                    if oop["properties_count"] > 0:
                        score += 1
                    if oop["operator_overloads"] > 0:
                        score += 1
                    oop_score = score

                print(f"\nOOP Score: {oop_score}/6")
                if solid_score > 0:
                    print(f"SOLID Score: {solid_score:.1f}/5.0")
                print(f"Principles Used:")
                print(f"  {'✓' if oop['total_classes'] > 0 else '✗'} Uses Classes")
                print(f"  {'✓' if oop['abstract_classes'] else '✗'} Abstraction (ABC/Protocol)")
                print(f"  {'✓' if oop['inheritance_depth'] > 0 else '✗'} Inheritance")
                print(f"  {'✓' if oop['private_methods'] > 0 or oop['protected_methods'] > 0 else '✗'} Encapsulation")
                print(f"  {'✓' if oop['properties_count'] > 0 else '✗'} Properties")
                print(f"  {'✓' if oop['operator_overloads'] > 0 else '✗'} Polymorphism")

                # Overall assessment
                if oop["total_classes"] == 0:
                    style = "Procedural/Functional"
                elif oop_score >= 5:
                    style = "Advanced OOP"
                elif oop_score >= 3:
                    style = "Moderate OOP"
                else:
                    style = "Basic OOP"

                print(f"\nCoding Style: {style}")
        else:
            print("\nNo Python projects found for OOP analysis.")

        # Analyze Java projects
        java_projects = [p for p in report["projects"] if "java" in p.get("languages", {})]

        if java_projects:
            print(f"\n{'*' * 70}")
            print(f"  JAVA OOP ANALYSIS")
            print(f"{'*' * 70}\n")

            for i, project in enumerate(java_projects, 1):
                if "java_oop_analysis" not in project:
                    continue

                print(f"\n{'-' * 70}")
                print(f"Project {i}: {project['project_name']}")
                print(f"{'-' * 70}")

                java_oop = project["java_oop_analysis"]

                if "error" in java_oop:
                    print(f"\nError during analysis: {java_oop['error']}\n")
                    continue

                print(f"\nOOP Metrics:")
                print(f"  Total Classes: {java_oop['total_classes']}")
                print(f"  Interfaces: {java_oop['interface_count']}")

                if java_oop["abstract_classes"]:
                    print(f"  Abstract Classes: {', '.join(java_oop['abstract_classes'][:5])}")
                    if len(java_oop["abstract_classes"]) > 5:
                        print(f"    ... and {len(java_oop['abstract_classes']) - 5} more")

                print(f"  Enums: {java_oop['enum_count']}")
                print(f"  Classes with Inheritance: {java_oop['classes_with_inheritance']}")
                print(f"  Max Inheritance Depth: {java_oop['inheritance_depth']}")

                print(f"\nEncapsulation:")
                total_methods = (
                    java_oop["private_methods"]
                    + java_oop["protected_methods"]
                    + java_oop["public_methods"]
                    + java_oop["package_methods"]
                )
                print(f"  Total Methods: {total_methods}")
                print(f"    - Private: {java_oop['private_methods']}")
                print(f"    - Protected: {java_oop['protected_methods']}")
                print(f"    - Public: {java_oop['public_methods']}")
                print(f"    - Package-private: {java_oop['package_methods']}")
                print(f"  Private Fields: {java_oop['private_fields']}")
                print(f"  Getter/Setter Pairs: {java_oop['getter_setter_pairs']}")

                print(f"\nPolymorphism:")
                print(f"  Method Overrides (@Override): {java_oop['override_count']}")
                print(f"  Method Overloads: {java_oop['method_overloads']}")

                print(f"\nJava-Specific Features:")
                print(f"  Generic Classes: {java_oop['generic_classes']}")
                print(f"  Nested Classes: {java_oop['nested_classes']}")
                print(f"  Lambda Expressions: {java_oop['lambda_count']}")

                if java_oop.get("annotations"):
                    print(f"\nAnnotations (top 5):")
                    for anno, count in sorted(java_oop["annotations"].items(), key=lambda x: x[1], reverse=True)[:5]:
                        print(f"  @{anno}: {count}")

                if java_oop.get("design_patterns"):
                    print(f"\nDesign Patterns Detected:")
                    for pattern in java_oop["design_patterns"]:
                        print(f"  ✓ {pattern}")

                # Calculate OOP score
                from dataclasses import dataclass, field
                from typing import Dict, List

                from analysis.java_oop_analyzer import (JavaOOPAnalysis,
                                                        calculate_oop_score,
                                                        calculate_solid_score,
                                                        get_coding_style)

                analysis_obj = JavaOOPAnalysis(**java_oop)
                oop_score = calculate_oop_score(analysis_obj)
                solid_score = calculate_solid_score(analysis_obj)
                coding_style = get_coding_style(oop_score)

                print(f"\nOOP Score: {oop_score}/6")
                print(f"SOLID Score: {solid_score:.1f}/5.0")
                print(f"Principles Used:")
                print(
                    f"  {'✓' if java_oop['total_classes'] > 0 or java_oop['interface_count'] > 0 else '✗'} Uses Classes/Interfaces"
                )
                print(f"  {'✓' if java_oop['interface_count'] > 0 or java_oop['abstract_classes'] else '✗'} Abstraction")
                print(f"  {'✓' if java_oop['inheritance_depth'] > 0 else '✗'} Inheritance")
                print(f"  {'✓' if java_oop['private_fields'] > 0 or java_oop['private_methods'] > 0 else '✗'} Encapsulation")
                print(f"  {'✓' if java_oop['override_count'] > 0 or java_oop['method_overloads'] > 0 else '✗'} Polymorphism")
                print(
                    f"  {'✓' if java_oop['generic_classes'] > 0 or java_oop['annotations'] or java_oop['lambda_count'] > 0 else '✗'} Advanced Features"
                )

                print(f"\nCoding Style: {coding_style}")
        else:
            print("\nNo Java projects found for OOP analysis.")

        # Analyze C++ projects
        cpp_projects = [p for p in report["projects"] if "cpp" in p.get("languages", {})]

        if cpp_projects:
            print(f"\n{'*' * 70}")
            print(f"  C++ OOP ANALYSIS")
            print(f"{'*' * 70}\n")

            for i, project in enumerate(cpp_projects, 1):
                if "cpp_oop_analysis" not in project:
                    continue

                print(f"\n{'-' * 70}")
                print(f"Project {i}: {project['project_name']}")
                print(f"{'-' * 70}")

                cpp_oop = project["cpp_oop_analysis"]

                if "error" in cpp_oop:
                    print(f"\nError during analysis: {cpp_oop['error']}\n")
                    continue

                print(f"\nOOP Metrics:")
                print(f"  Total Classes: {cpp_oop['total_classes']}")
                print(f"  Abstract classes: {cpp_oop['abstract_classes']}")
                print(f"  Classes with Inheritance: {cpp_oop['classes_with_inheritance']}")
                print(f"  Inheritance depth: {cpp_oop['inheritance_depth']}")

                print(f"\nEncapsulation:")
                print(f"  Private methods: {cpp_oop['private_methods']}")
                print(f"  Protected methods: {cpp_oop['protected_methods']}")
                print(f"  Public methods: {cpp_oop['public_methods']}")

                print(f"\nPolymorphism:")
                print(f"  Virtual methods: {cpp_oop['virtual_methods']}")
                print(f"  Operator overloads: {cpp_oop['operator_overloads']}")

                print(f"\nC++-Specific Features:")
                print(f"  Templates: {cpp_oop.get('template_classes', 0)}")
                print(f"  Namespaces: {cpp_oop.get('namespaces_used', 0)}")
        else:
            print("\nNo C++ projects found for OOP analysis.")

        # Analyze C projects (check for c_oop_analysis since .c files are classified as cpp)
        c_projects = [p for p in report["projects"] if "c_oop_analysis" in p]

        if c_projects:
            print(f"\n{'*' * 70}")
            print(f"  C OOP-STYLE ANALYSIS")
            print(f"{'*' * 70}\n")

            for i, project in enumerate(c_projects, 1):
                if "c_oop_analysis" not in project:
                    continue

                print(f"\n{'-' * 70}")
                print(f"Project {i}: {project['project_name']}")
                print(f"{'-' * 70}")

                c_oop = project["c_oop_analysis"]

                if "error" in c_oop:
                    print(f"\nError during analysis: {c_oop['error']}\n")
                    continue

                print(f"\nOOP-Style Metrics:")
                print(f"  Total Structs: {c_oop['total_structs']}")
                print(f"  Total Functions: {c_oop.get('total_functions', 0)}")
                print(f"  Function pointer fields: {c_oop.get('function_pointer_fields', 0)}")
                print(f"  Typedef count: {c_oop.get('typedef_count', 0)}")

                print(f"\nEncapsulation Patterns:")
                print(f"  Opaque pointer structs: {c_oop.get('opaque_pointer_structs', 0)}")
                print(f"  Static functions: {c_oop.get('static_functions', 0)}")

                print(f"\nPolymorphism Patterns:")
                print(f"  VTable-style structs: {c_oop.get('vtable_structs', 0)}")
                print(f"  OOP-style naming: {c_oop.get('oop_style_naming_count', 0)}")

                print(f"\nMemory Management:")
                print(f"  Malloc/Free usage: {c_oop.get('malloc_usage', 0)}/{c_oop.get('free_usage', 0)}")
                print(f"  Constructor/Destructor pairs: {c_oop.get('constructor_destructor_pairs', 0)}")

                # Calculate OOP-style score
                score = 0
                if c_oop.get("total_structs", 0) > 0:
                    score += 1
                if c_oop.get("function_pointer_fields", 0) > 0:
                    score += 1
                if c_oop.get("opaque_pointer_structs", 0) > 0:
                    score += 1
                if c_oop.get("vtable_structs", 0) > 0:
                    score += 1
                if c_oop.get("oop_style_naming_count", 0) > 0:
                    score += 1

                print(f"\nOOP-Style Score: {score}/5")
                print(f"Coding Style: {'Object-Oriented C' if score >= 3 else 'Procedural C'}")
        else:
            print("\nNo C projects found for OOP-style analysis.")
        for project in report["projects"]:
            try:
                portfolio_item = generate_portfolio_item(project)
                project["portfolio_item"] = portfolio_item
            except Exception as e:
                print(f"[ERROR] Failed to generate portfolio item for {project.get('project_name', 'Unknown')} : {e}")
        # Store analysis in database if it's new
        if new_analysis_generated:
            print_separator("STORING ANALYSIS IN DATABASE")
            try:
                analysis_id = record_analysis(analysis_type="non_llm", payload=report)
                print(f"  Analysis successfully stored in database")
                print(f"  Total Projects: {len(report['projects'])}")
            except Exception as e:
                print(f"  Error storing analysis in database: {e}")
                import traceback

                traceback.print_exc()

        # Automatically summarize top-ranked projects from current zip file
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_file_path)

        # Portfolio Generation
        print("\n" + "=" * 78)
        print("  GENERATED PORTFOLIO ITEMS")
        print("=" * 78 + "\n")

        for project in report["projects"]:
            if "portfolio_item" not in project:
                continue
            item = project["portfolio_item"]

            print(f"Project: {project['project_name']}")
            print("-" * 70)
            print(item["text_summary"])
            print("-" * 70 + "\n")

        # Ask user if they want to generate resume
        print_separator()

        # Check if any resume items exist first
        total_projects = len(report.get("projects", []))
        existing_resume_count = sum(
            1
            for project in report.get("projects", [])
            if get_resume_items_for_project(project.get("project_name", "Unknown Project"))
        )

        if existing_resume_count > 0:
            print(f"Found {existing_resume_count}/{total_projects} résumé item(s) in database.")
            print()
            print("Options:")
            print("  1. View existing résumé items (and generate missing ones)")
            print("  2. Regenerate all résumé items (overwrite existing)")
            print("  3. Skip résumé generation")
            print()
            resume_choice = None
            while resume_choice not in ["1", "2", "3"]:
                resume_choice = input("Enter your choice (1/2/3): ").strip()
                if resume_choice not in ["1", "2", "3"]:
                    print("  Invalid choice. Please enter 1, 2, or 3.")

            if resume_choice == "3":
                generate_resume = "n"
            else:
                generate_resume = "y"
                regenerate_all = resume_choice == "2"
        else:
            generate_resume = input("Generate résumé items? (y/n): ").lower().strip()
            regenerate_all = False

        if generate_resume == "y":
            print("\n" + "=" * 78)
            print("  FULL RESUME")
            print("=" * 78 + "\n")
            from analysis.resume_generator import \
                generate_formatted_resume_entry

            # Check if resume items already exist
            resume_items_by_project = {}
            projects_needing_resume = []

            for project in report.get("projects", []):
                project_name = project.get("project_name", "Unknown Project")
                existing_resume_items = get_resume_items_for_project(project_name)

                if existing_resume_items and not regenerate_all:
                    resume_items_by_project[project_name] = {"text": existing_resume_items[0]["resume_text"], "cached": True}
                else:
                    projects_needing_resume.append(project)

            # Display existing resume items
            if resume_items_by_project and not regenerate_all:
                print(f"✓ Retrieved {len(resume_items_by_project)} cached résumé item(s) from database\n")

                for i, project in enumerate(report.get("projects", []), 1):
                    project_name = project.get("project_name", "Unknown Project")
                    if project_name in resume_items_by_project:
                        print("=" * 78)
                        print(f"RÉSUMÉ ITEM {i}/{total_projects}: {project_name}")
                        print("=" * 78)
                        print()
                        print(resume_items_by_project[project_name]["text"])
                        print("\n")

            # Generate and store resumes for projects that don't have them
            newly_generated = 0  # Initialize to avoid UnboundLocalError

            if projects_needing_resume:
                if resume_items_by_project and not regenerate_all:
                    print(f"\nGenerating {len(projects_needing_resume)} new résumé item(s)...\n")
                elif regenerate_all:
                    print(f"Regenerating all {len(projects_needing_resume)} résumé item(s)...\n")
                else:
                    print(f"Generating {len(projects_needing_resume)} résumé item(s)...\n")

                cached_count = len(resume_items_by_project)

                for idx, project in enumerate(projects_needing_resume, 1):
                    project_name = project.get("project_name", "Unknown Project")
                    resume_entry = generate_formatted_resume_entry(project)

                    item_number = cached_count + idx if not regenerate_all else idx

                    print("=" * 78)
                    print(f"RÉSUMÉ ITEM {item_number}/{total_projects}- Project: {project_name}")
                    print("=" * 78)
                    print()
                    print(resume_entry)
                    print("\n")

                    try:
                        # Delete old resume item if regenerating
                        if regenerate_all:
                            with get_connection() as conn:
                                conn.execute("DELETE FROM resume_items WHERE project_name = ?", (project_name,))
                                conn.commit()

                        store_resume_item(project_name, resume_entry)
                        newly_generated += 1
                    except Exception as e:
                        print(f"⚠  Warning: Could not store résumé item for {project_name}: {e}")
                        import traceback

                        traceback.print_exc()

                print("=" * 78)
                if regenerate_all:
                    print(f"✓ Successfully regenerated {newly_generated}/{len(projects_needing_resume)} résumé item(s)")
                elif newly_generated > 0:
                    print(
                        f"✓ Successfully generated and stored {newly_generated}/{len(projects_needing_resume)} new résumé item(s)"
                    )
                print("=" * 78 + "\n")
            elif resume_items_by_project:
                print("=" * 78)
                print(f"✓ All {len(resume_items_by_project)} résumé item(s) retrieved from database")
                print("=" * 78 + "\n")

        # Offer to save JSON
        print_separator()
        save = input("Save complete report to JSON file? (y/n): ").lower().strip()

        if save == "y":
            output_file = Path("analysis_report.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\nReport saved to: {output_file}")
            print(f"File size: {output_file.stat().st_size:,} bytes")

        print_separator("ANALYSIS COMPLETE")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
