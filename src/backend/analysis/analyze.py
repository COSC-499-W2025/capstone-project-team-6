#!/usr/bin/env python3
"""
Complete Analysis Script - Detailed Metadata Extraction and Deep Code Analysis

Usage:
    python src/backend/analysis/analyze.py <zip_file_path>
"""

import sys
import json
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
src_dir = backend_dir.parent

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from analysis.deep_code_analyzer import generate_comprehensive_report


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
    
    print_separator("COMPLETE PROJECT ANALYSIS")
    print(f"Analyzing: {zip_path}")
    print("Running: File Classification → Metadata Extraction → Deep Code Analysis\n")
    
    try:
        report = generate_comprehensive_report(zip_path)
        
        print_separator("PHASE 1 & 2: FILE CLASSIFICATION + METADATA")
        
        summary = report['summary']
        print(f"Total Files: {summary['total_files']}")
        print(f"Total Projects: {len(report['projects'])}")
        print(f"Languages: {', '.join(summary['languages_used'])}")
        
        # Detailed project analysis
        for i, project in enumerate(report['projects'], 1):
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
            for lang, count in project.get('languages', {}).items():
                print(f"  - {lang}: {count} files")
            
            if project.get('frameworks'):
                print(f"\nFrameworks:")
                for fw in project['frameworks']:
                    print(f"  - {fw}")
            
            if project.get('dependencies'):
                print(f"\nDependencies:")
                for pkg_mgr, deps in project['dependencies'].items():
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
        
        print_separator("PHASE 3: CODE ANALYSIS FOR OOP PRINCIPLES (PYTHON PROJECTS FOR NOW)")
        # Other languages will be added later 
        python_projects = [p for p in report['projects'] if 'python' in p.get('languages', {})]
        
        if not python_projects:
            print("No Python projects found for OOP analysis.\n")
        else:
            for i, project in enumerate(python_projects, 1):
                if 'oop_analysis' not in project:
                    continue
                
                print(f"\n{'-' * 70}")
                print(f"Project {i}: {project['project_name']}")
                print(f"{'-' * 70}")
                
                oop = project['oop_analysis']
                
                if 'error' in oop:
                    print(f"\nError during analysis: {oop['error']}\n")
                    continue
                
                print(f"\nOOP Metrics:")
                print(f"  Total Classes: {oop['total_classes']}")
                
                if oop['abstract_classes']:
                    print(f"  Abstract Classes: {', '.join(oop['abstract_classes'][:5])}")
                    if len(oop['abstract_classes']) > 5:
                        print(f"    ... and {len(oop['abstract_classes']) - 5} more")
                
                print(f"  Classes with Inheritance: {oop['classes_with_inheritance']}")
                print(f"  Max Inheritance Depth: {oop['inheritance_depth']}")
                
                print(f"\nEncapsulation:")
                total_methods = oop['private_methods'] + oop['protected_methods'] + oop['public_methods']
                print(f"  Total Methods: {total_methods}")
                print(f"    - Private (__name): {oop['private_methods']}")
                print(f"    - Protected (_name): {oop['protected_methods']}")
                print(f"    - Public: {oop['public_methods']}")
                print(f"  Properties (@property): {oop['properties_count']}")
                
                print(f"\nPolymorphism:")
                print(f"  Operator Overloads: {oop['operator_overloads']}")
                
                # Calculate OOP score
                score = 0
                if oop['total_classes'] > 0: score += 1
                if oop['abstract_classes']: score += 1
                if oop['inheritance_depth'] > 0: score += 1
                if oop['private_methods'] > 0 or oop['protected_methods'] > 0: score += 1
                if oop['properties_count'] > 0: score += 1
                if oop['operator_overloads'] > 0: score += 1
                
                print(f"\nOOP Score: {score}/6")
                print(f"Principles Used:")
                print(f"  {'✓' if oop['total_classes'] > 0 else '✗'} Uses Classes")
                print(f"  {'✓' if oop['abstract_classes'] else '✗'} Abstraction (ABC/Protocol)")
                print(f"  {'✓' if oop['inheritance_depth'] > 0 else '✗'} Inheritance")
                print(f"  {'✓' if oop['private_methods'] > 0 or oop['protected_methods'] > 0 else '✗'} Encapsulation")
                print(f"  {'✓' if oop['properties_count'] > 0 else '✗'} Properties")
                print(f"  {'✓' if oop['operator_overloads'] > 0 else '✗'} Polymorphism")
                
                # Overall assessment
                if oop['total_classes'] == 0:
                    style = "Procedural/Functional"
                elif score >= 5:
                    style = "Advanced OOP"
                elif score >= 3:
                    style = "Moderate OOP"
                else:
                    style = "Basic OOP"
                
                print(f"\nCoding Style: {style}")
        
        # Offer to save JSON
        print_separator()
        save = input("Save complete report to JSON file? (y/n): ").lower().strip()
        
        if save == 'y':
            output_file = Path("analysis_report.json")
            with open(output_file, 'w', encoding='utf-8') as f:
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
