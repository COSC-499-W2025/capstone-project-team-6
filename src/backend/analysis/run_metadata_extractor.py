"""
CLI for running metadata extraction.

Usage:
    python -m src.backend.analysis.run_metadata_extractor <zip_path> [output_path]
    
Or directly:
    python src/backend/analysis/run_metadata_extractor.py <zip_path> [output_path]
"""

import sys
from pathlib import Path

from analysis.resume_generator import (generate_formatted_resume_entry,
                                       generate_full_resume)

# Add parent directories to path to allow imports
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
src_dir = backend_dir.parent
root_dir = src_dir.parent

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

# Import directly without going through backend __init__ to avoid unnecessary dependencies
from analysis.metadata_extractor import MetadataExtractor


def main():
    """Main entry point for metadata extraction CLI."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.backend.analysis.run_metadata_extractor <zip_path> [output_path]")
        print("\nExample:")
        print("  python -m src.backend.analysis.run_metadata_extractor test_project.zip output.json")
        sys.exit(1)

    zip_path = Path(sys.argv[1])

    if not zip_path.exists():
        print(f"Error: ZIP file not found: {zip_path}")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = zip_path.parent / f"{zip_path.stem}_metadata.json"

    print(f"Analyzing ZIP file: {zip_path}")
    print(f"Output will be saved to: {output_path}")
    print("-" * 60)

    # Run extraction
    with MetadataExtractor(zip_path) as extractor:
        report = extractor.generate_report(output_path)

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    summary = report["summary"]
    projects = report["projects"]

    print(f"\nTotal Projects: {report['analysis_metadata']['total_projects']}")
    print(f"Total Files: {summary['total_files']}")
    print(f"Total Size: {summary['total_size_mb']} MB")
    print(f"\nLanguages: {', '.join(summary['languages_used'])}")
    if summary["frameworks_used"]:
        print(f"Frameworks: {', '.join(summary['frameworks_used'])}")

    print("\n" + "-" * 60)
    print("PROJECT DETAILS")
    print("-" * 60)

    for i, project in enumerate(projects, 1):
        print(f"\n{i}. {project['project_name']}")
        print(f"   Path: {project['project_path'] or '(root)'}")
        print(f"   Primary Language: {project['primary_language'] or 'N/A'}")
        print(f"   Files: {project['total_files']} ({project['code_files']} code, {project['test_files']} tests)")
        print(f"   Test Coverage: {project['test_coverage_estimate']}")

        if project["frameworks"]:
            print(f"   Frameworks: {', '.join(project['frameworks'])}")

        if project["dependencies"]:
            print(f"   Dependencies:")
            for pkg_mgr, deps in project["dependencies"].items():
                print(f"      {pkg_mgr}: {len(deps)} packages")

        if project["is_git_repo"]:
            print(f"   Git Repository: Yes")
            if project["contributors"]:
                print(f"   Contributors: {len(project['contributors'])}")

        print(f"   Has README: {'Yes' if project['has_readme'] else 'No'}")
        print(f"   Has CI/CD: {'Yes' if project['has_ci_cd'] else 'No'}")
        print(f"   Has Docker: {'Yes' if project['has_docker'] else 'No'}")

        print(generate_formatted_resume_entry(project))

    print(f"\n{'-' * 60}")
    print(f"Full report saved to: {output_path}")
    print(generate_full_resume(report))
    print()


if __name__ == "__main__":
    main()
