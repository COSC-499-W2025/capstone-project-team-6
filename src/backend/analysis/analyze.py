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

from backend.analysis_database import init_db, record_analysis


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
        report["analysis_metadata"] = {
            "zip_file": str(zip_path.absolute()),
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

                from analysis.java_oop_analyzer import (calculate_oop_score,
                                                        calculate_solid_score,
                                                        get_coding_style)

                @dataclass
                class JavaOOPAnalysis:
                    total_classes: int = 0
                    interface_count: int = 0
                    abstract_classes: List[str] = field(default_factory=list)
                    enum_count: int = 0
                    private_methods: int = 0
                    protected_methods: int = 0
                    public_methods: int = 0
                    package_methods: int = 0
                    private_fields: int = 0
                    protected_fields: int = 0
                    public_fields: int = 0
                    classes_with_inheritance: int = 0
                    inheritance_depth: int = 0
                    override_count: int = 0
                    method_overloads: int = 0
                    generic_classes: int = 0
                    nested_classes: int = 0
                    anonymous_classes: int = 0
                    lambda_count: int = 0
                    annotations: Dict[str, int] = field(default_factory=dict)
                    design_patterns: List[str] = field(default_factory=list)
                    getter_setter_pairs: int = 0

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

                print(
                    f"  {'✓' if java_oop['generic_classes'] > 0 or java_oop['annotations'] or java_oop['lambda_count'] > 0 else '✗'} Advanced Features"
                )

                print(f"\nCoding Style: {coding_style}")
        else:
            print("\nNo Java projects found for OOP analysis.")
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
            print("\n" + "="*78)
            print("  FULL RESUME")
            print("="*78 + "\n")
            from analysis.resume_generator import generate_full_resume
            print(generate_full_resume(report))
            print("\n" + "="*78 + "\n")

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
