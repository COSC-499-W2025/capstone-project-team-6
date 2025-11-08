# Example script demonstrating metadata extraction usage.
# This script shows how to use the MetadataExtractor to analyze projects and generate reports.


import json
from pathlib import Path
import sys

# Add parent directories to path to allow imports
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
src_dir = backend_dir.parent
root_dir = src_dir.parent

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

# Import directly without going through backend __init__
from analysis.metadata_extractor import MetadataExtractor


def example_basic_usage():
    """Example: Basic usage of metadata extractor."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 60)
    
    # Path to your test ZIP
    zip_path = Path("src/tests/backend_test/Test-zip-traversal/python_project.zip")
    
    if not zip_path.exists():
        print(f"Test ZIP not found: {zip_path}")
        return
    
    # Create extractor and generate report
    with MetadataExtractor(zip_path) as extractor:
        report = extractor.generate_report()
    
    # Print summary
    print(f"\nTotal Projects: {len(report['projects'])}")
    print(f"Total Files: {report['summary']['total_files']}")
    print(f"Languages: {', '.join(report['summary']['languages_used'])}")
    print()


def example_detailed_analysis():
    """Example: Detailed project analysis."""
    print("=" * 60)
    print("EXAMPLE 2: Detailed Analysis")
    print("=" * 60)
    
    zip_path = Path("src/tests/backend_test/Test-zip-traversal/python_project.zip")
    
    if not zip_path.exists():
        print(f"Test ZIP not found: {zip_path}")
        return
    
    with MetadataExtractor(zip_path) as extractor:
        # Detect projects
        projects = extractor.detect_projects()
        print(f"\nDetected {len(projects)} project(s)")
        
        # Analyze each project
        for i, project_path in enumerate(projects, 1):
            print(f"\n{'-' * 40}")
            print(f"Project {i}: {project_path or '(root)'}")
            print(f"{'-' * 40}")
            
            metadata = extractor.extract_project_metadata(project_path)
            
            print(f"Name: {metadata.project_name}")
            print(f"Primary Language: {metadata.primary_language or 'N/A'}")
            print(f"\nFiles:")
            print(f"  - Code: {metadata.code_files}")
            print(f"  - Tests: {metadata.test_files}")
            print(f"  - Docs: {metadata.doc_files}")
            print(f"  - Config: {metadata.config_files}")
            
            print(f"\nLanguage Breakdown:")
            for lang, count in metadata.languages.items():
                print(f"  - {lang}: {count} files")
            
            if metadata.frameworks:
                print(f"\nFrameworks: {', '.join(metadata.frameworks)}")
            
            if metadata.dependencies:
                print(f"\nDependencies:")
                for pkg_mgr, deps in metadata.dependencies.items():
                    print(f"  - {pkg_mgr}: {len(deps)} packages")
                    if len(deps) <= 5:
                        for dep in deps[:5]:
                            print(f"      • {dep}")
            
            print(f"\nProject Indicators:")
            print(f"  - Has Tests: {metadata.has_tests}")
            print(f"  - Has README: {metadata.has_readme}")
            print(f"  - Has CI/CD: {metadata.has_ci_cd}")
            print(f"  - Has Docker: {metadata.has_docker}")
            print(f"  - Test Coverage: {metadata.test_coverage_estimate}")
            
            if metadata.is_git_repo:
                print(f"\nGit Repository:")
                print(f"  - Total Commits: {metadata.total_commits}")
                print(f"  - Contributors: {len(metadata.contributors)}")
    
    print()


def example_save_report():
    """Example: Save report to JSON file."""
    print("=" * 60)
    print("EXAMPLE 3: Save Report to File")
    print("=" * 60)
    
    zip_path = Path("src/tests/backend_test/Test-zip-traversal/python_project.zip")
    output_path = Path("example_metadata_report.json")
    
    if not zip_path.exists():
        print(f"Test ZIP not found: {zip_path}")
        return
    
    with MetadataExtractor(zip_path) as extractor:
        report = extractor.generate_report(output_path)
    
    print(f"\nReport saved to: {output_path}")
    print(f"File size: {output_path.stat().st_size} bytes")
    
    # Show a preview of the JSON
    print("\nReport preview:")
    print(json.dumps(report["analysis_metadata"], indent=2))
    print()


def example_compare_projects():
    """Example: Compare multiple projects."""
    print("=" * 60)
    print("EXAMPLE 4: Compare Projects")
    print("=" * 60)
    
    zip_path = Path("src/tests/backend_test/Test-zip-traversal/python_project.zip")
    
    if not zip_path.exists():
        print(f"Test ZIP not found: {zip_path}")
        return
    
    with MetadataExtractor(zip_path) as extractor:
        report = extractor.generate_report()
    
    if len(report["projects"]) > 1:
        print("\nComparing projects:\n")
        
        # Create comparison table
        print(f"{'Project':<30} {'Files':<10} {'Tests':<10} {'Coverage':<12}")
        print("-" * 62)
        
        for project in report["projects"]:
            name = project["project_name"][:28]
            files = project["total_files"]
            tests = project["test_files"]
            coverage = project["test_coverage_estimate"]
            
            print(f"{name:<30} {files:<10} {tests:<10} {coverage:<12}")
    else:
        print("\nOnly one project detected, no comparison needed.")
    
    print()


def example_custom_analysis():
    """Example: Custom analysis using extracted metadata."""
    print("=" * 60)
    print("EXAMPLE 5: Custom Analysis")
    print("=" * 60)
    
    zip_path = Path("src/tests/backend_test/Test-zip-traversal/python_project.zip")
    
    if not zip_path.exists():
        print(f"Test ZIP not found: {zip_path}")
        return
    
    with MetadataExtractor(zip_path) as extractor:
        report = extractor.generate_report()
    
    # Calculate project health score
    print("\nProject Health Analysis:\n")
    
    for project in report["projects"]:
        score = 0
        max_score = 7
        
        # Scoring criteria
        if project["has_tests"]:
            score += 1
        if project["has_readme"]:
            score += 1
        if project["has_ci_cd"]:
            score += 1
        if project["has_docker"]:
            score += 1
        if project["test_coverage_estimate"] in ["medium", "high"]:
            score += 1
        if project["total_files"] > 5:  # Non-trivial project
            score += 1
        if len(project.get("dependencies", {})) > 0:  # Has dependencies managed
            score += 1
        
        percentage = (score / max_score) * 100
        
        print(f"Project: {project['project_name']}")
        print(f"Health Score: {score}/{max_score} ({percentage:.0f}%)")
        
        print("Checklist:")
        print(f"  {'✓' if project['has_tests'] else '✗'} Has tests")
        print(f"  {'✓' if project['has_readme'] else '✗'} Has README")
        print(f"  {'✓' if project['has_ci_cd'] else '✗'} Has CI/CD")
        print(f"  {'✓' if project['has_docker'] else '✗'} Has Docker")
        print(f"  {'✓' if project['test_coverage_estimate'] in ['medium', 'high'] else '✗'} Good test coverage")
        print(f"  {'✓' if project['total_files'] > 5 else '✗'} Non-trivial size")
        print(f"  {'✓' if len(project.get('dependencies', {})) > 0 else '✗'} Manages dependencies")
        print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("METADATA EXTRACTOR - EXAMPLE USAGE")
    print("=" * 60 + "\n")
    
    # Run all examples
    example_basic_usage()
    example_detailed_analysis()
    example_save_report()
    example_compare_projects()
    example_custom_analysis()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
