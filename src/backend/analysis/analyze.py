#!/usr/bin/env python3
"""
Complete Analysis Script - Detailed Metadata Extraction and Deep Code Analysis

Usage:
    python src/backend/analysis/analyze.py <zip_file_path>
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
src_dir = backend_dir.parent

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from analysis.deep_code_analyzer import generate_comprehensive_report
from analysis.resume_generator import (generate_formatted_resume_entry,
                                       print_resume_items)

from backend.analysis_database import (get_analysis_report,
                                       get_resume_items_for_project, init_db,
                                       record_analysis, store_resume_item)


def print_separator(title=""):
    """Print a separator line."""
    if title:
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}\n")
    else:
        print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/backend/analysis/analyze.py <zip_file_path>")
        print("\nExample:")
        print("  python src/backend/analysis/analyze.py project.zip")
        sys.exit(1)

    zip_path = Path(sys.argv[1])

    if not zip_path.exists():
        print(f"Error: File not found: {zip_path}")
        sys.exit(1)

    # Initialize database
    init_db()

    print_separator("COMPLETE  ANALYSIS")
    print(f"Analyzing: {zip_path}")

    try:
        report = generate_comprehensive_report(zip_path)

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
            report["analysis_metadata"] = {
                "zip_file": zip_file_path,
                "analysis_timestamp": datetime.now().isoformat(),
                "total_projects": len(report["projects"]),
            }

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

                # Calculate OOP score
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

                print(f"\nOOP Score: {score}/6")
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
                elif score >= 5:
                    style = "Advanced OOP"
                elif score >= 3:
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

        # Only store analysis if it's new
        if not existing_report:
            print_separator("STORING ANALYSIS IN DATABASE")
            try:
                analysis_id = record_analysis(analysis_type="non_llm", payload=report)
                print(f"  Analysis successfully stored in database")
                print(f"  Total Projects: {len(report['projects'])}")
            except Exception as e:
                print(f"  Error storing analysis in database: {e}")
                import traceback

                traceback.print_exc()

        # Ask user if they want to generate resume
        print_separator()
        generate_resume = input("Generate resume? (y/n): ").lower().strip()

        if generate_resume == "y":
            print("\n" + "=" * 78)
            print("  FULL RESUME")
            print("=" * 78 + "\n")
            from analysis.resume_generator import (
                generate_formatted_resume_entry, generate_full_resume)

            # Check if resume items already exist
            resume_items_by_project = {}
            projects_needing_resume = []

            for project in report.get("projects", []):
                project_name = project.get("project_name", "Unknown Project")
                existing_resume_items = get_resume_items_for_project(project_name)

                if existing_resume_items:
                    resume_items_by_project[project_name] = existing_resume_items[0]["resume_text"]
                else:
                    projects_needing_resume.append(project)

            # Display existing resume items
            if resume_items_by_project:
                print("Found existing resume items in database. Using cached resumes.\n")
                for project in report.get("projects", []):
                    project_name = project.get("project_name", "Unknown Project")
                    if project_name in resume_items_by_project:
                        print(resume_items_by_project[project_name])
                        print()

            # Generate and store resumes for projects that don't have them
            if projects_needing_resume:
                if resume_items_by_project:
                    print("Generating resumes for remaining projects...\n")
                else:
                    print("No existing resume items found. Generating new resumes.\n")

                for project in projects_needing_resume:
                    project_name = project.get("project_name", "Unknown Project")
                    resume_entry = generate_formatted_resume_entry(project)
                    print(resume_entry)
                    print()

                    try:
                        store_resume_item(project_name, resume_entry)
                    except Exception as e:
                        print(f" Warning: Could not store resume item for {project_name}: {e}")
                        import traceback

                        traceback.print_exc()

                if projects_needing_resume:
                    print("=" * 78 + "\n")
                    print(f" Successfully stored {len(projects_needing_resume)} resume item(s) in the database")
            elif resume_items_by_project:
                print("=" * 78 + "\n")
                print(f" All {len(resume_items_by_project)} resume item(s) retrieved from database")
        for project in report["projects"]:
            try:
                portfolio_item = generate_portfolio_item(project)
                project["portfolio_item"] = portfolio_item
            except Exception as e:
                print(f"[ERROR] Failed to generate portfolio item: {e}")
        print_separator("STORING ANALYSIS IN DATABASE")
        try:
            analysis_id = record_analysis(analysis_type="non_llm", payload=report)
            print(f"  Analysis successfully stored in database")
            print(f"  Total Projects: {len(report['projects'])}")
        except Exception as e:
            print(f"  Error storing analysis in database: {e}")
            import traceback

            traceback.print_exc()

        # Ask user if they want to generate resume
        print_separator()
        generate_resume = input("Generate resume? (y/n): ").lower().strip()

        if generate_resume == "y":
            print("\n" + "=" * 78)
            print("  FULL RESUME")
            print("=" * 78 + "\n")
            from analysis.resume_generator import generate_full_resume

            print(generate_full_resume(report))
            print("\n" + "=" * 78 + "\n")

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
