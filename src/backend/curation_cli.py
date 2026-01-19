"""
CLI integration for project curation features.

Provides interactive interfaces for users to:
- Correct project chronology
- Select comparison attributes
- Choose showcase projects
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .curation import (ATTRIBUTE_DESCRIPTIONS,
                           DEFAULT_COMPARISON_ATTRIBUTES,
                           ProjectChronologyCorrection,
                           format_project_comparison,
                           get_chronology_corrections, get_showcase_projects,
                           get_user_curation_settings, get_user_projects,
                           init_curation_tables, save_chronology_correction,
                           save_comparison_attributes, save_showcase_projects,
                           validate_date_format)
except ImportError:
    # Handle direct execution or testing
    import sys

    current_dir = Path(__file__).parent
    src_dir = current_dir.parent
    sys.path.insert(0, str(src_dir))
    from backend.curation import (ATTRIBUTE_DESCRIPTIONS,
                                  DEFAULT_COMPARISON_ATTRIBUTES,
                                  ProjectChronologyCorrection,
                                  format_project_comparison,
                                  get_chronology_corrections,
                                  get_showcase_projects,
                                  get_user_curation_settings,
                                  get_user_projects, init_curation_tables,
                                  save_chronology_correction,
                                  save_comparison_attributes,
                                  save_showcase_projects, validate_date_format)


def curate_chronology_interactive(user_id: str) -> None:
    """Interactive interface for correcting project chronology."""
    print("\n" + "=" * 70)
    print("PROJECT CHRONOLOGY CORRECTION")
    print("=" * 70)

    # Get user's projects
    projects = get_user_projects(user_id)
    if not projects:
        print("\nNo projects found. Please analyze some repositories first.")
        return

    print(f"\nFound {len(projects)} projects:")
    print("-" * 70)

    for i, project in enumerate(projects, 1):
        print(f"{i:2d}. {project['project_name']}")
        print(f"    Current dates:")
        print(f"      Last commit:  {project['effective_last_commit_date'] or 'None'}")
        print(f"      Last modified: {project['effective_last_modified_date'] or 'None'}")
        print(f"      Start date:   {project['effective_project_start_date'] or 'None'}")
        print(f"      End date:     {project['effective_project_end_date'] or 'None'}")
        if project["correction_timestamp"]:
            print(f"      (Corrected on {project['correction_timestamp'][:19]})")
        print()

    while True:
        try:
            choice = input("Enter project number to correct (or 'q' to quit): ").strip()
            if choice.lower() == "q":
                break

            project_num = int(choice)
            if 1 <= project_num <= len(projects):
                project = projects[project_num - 1]
                _correct_project_chronology(user_id, project)

                # Refresh projects list to show updates
                projects = get_user_projects(user_id)
            else:
                print(f"Please enter a number between 1 and {len(projects)}")

        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\nCancelled.")
            break


def _correct_project_chronology(user_id: str, project: Dict[str, Any]) -> None:
    """Correct chronology for a specific project."""
    print(f"\nCorrecting chronology for: {project['project_name']}")
    print("-" * 50)

    corrections = {}
    date_fields = [
        ("last_commit_date", "Last commit date"),
        ("last_modified_date", "Last modified date"),
        ("project_start_date", "Project start date"),
        ("project_end_date", "Project end date"),
    ]

    for field, label in date_fields:
        current_value = project[f"effective_{field}"]
        print(f"\n{label}:")
        print(f"  Current: {current_value or 'None'}")

        while True:
            new_value = input(f"  New value (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS, blank to keep current): ").strip()

            if not new_value:
                break
            elif new_value.lower() == "none" or new_value.lower() == "null":
                corrections[field] = None
                print(f"  Will clear {label.lower()}")
                break
            else:
                # Try to parse and validate the date
                if validate_date_format(new_value):
                    corrections[field] = new_value
                    print(f"  Will set {label.lower()} to: {new_value}")
                    break
                else:
                    print("  Invalid date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")

    if corrections:
        print(f"\nSummary of changes for {project['project_name']}:")
        for field, value in corrections.items():
            label = next(label for f, label in date_fields if f == field)
            print(f"  {label}: {value or 'Clear'}")

        confirm = input("\nSave these corrections? (y/N): ").strip().lower()
        if confirm == "y":
            if save_chronology_correction(
                project["id"],
                user_id,
                corrections.get("last_commit_date"),
                corrections.get("last_modified_date"),
                corrections.get("project_start_date"),
                corrections.get("project_end_date"),
            ):
                print("✅ Chronology corrections saved successfully!")
            else:
                print("❌ Failed to save corrections")
        else:
            print("Cancelled - no changes saved")
    else:
        print("No changes made")


def curate_comparison_attributes_interactive(user_id: str) -> None:
    """Interactive interface for selecting comparison attributes."""
    print("\n" + "=" * 70)
    print("PROJECT COMPARISON ATTRIBUTES SELECTION")
    print("=" * 70)

    # Get current settings
    settings = get_user_curation_settings(user_id)
    current_attrs = set(settings.comparison_attributes)

    # Show all available attributes
    all_attributes = sorted(ATTRIBUTE_DESCRIPTIONS.keys())

    print("\nAvailable comparison attributes:")
    print("-" * 40)

    for i, attr in enumerate(all_attributes, 1):
        status = "✓" if attr in current_attrs else " "
        desc = ATTRIBUTE_DESCRIPTIONS[attr]
        print(f"{i:2d}. [{status}] {desc}")
        print(f"      ({attr})")

    print(f"\nCurrently selected: {len(current_attrs)} attributes")
    print("✓ = currently selected for comparison")

    while True:
        try:
            print("\nOptions:")
            print("  1. Toggle individual attributes")
            print("  2. Select default set")
            print("  3. Select all attributes")
            print("  4. Clear all attributes")
            print("  5. Save and exit")
            print("  q. Quit without saving")

            choice = input("\nEnter option: ").strip()

            if choice == "1":
                _toggle_comparison_attributes(all_attributes, current_attrs)
            elif choice == "2":
                current_attrs = set(DEFAULT_COMPARISON_ATTRIBUTES)
                print(f"Selected default attributes ({len(current_attrs)})")
            elif choice == "3":
                current_attrs = set(all_attributes)
                print(f"Selected all attributes ({len(current_attrs)})")
            elif choice == "4":
                current_attrs = set()
                print("Cleared all attributes")
            elif choice == "5":
                if len(current_attrs) == 0:
                    print("Please select at least one attribute for comparison")
                    continue

                if save_comparison_attributes(user_id, list(current_attrs)):
                    print("✅ Comparison attributes saved successfully!")
                    break
                else:
                    print("❌ Failed to save comparison attributes")

            elif choice.lower() == "q":
                print("Cancelled - no changes saved")
                break
            else:
                print("Invalid option")

        except KeyboardInterrupt:
            print("\nCancelled.")
            break


def _toggle_comparison_attributes(all_attributes: List[str], current_attrs: set) -> None:
    """Toggle individual comparison attributes."""
    while True:
        try:
            print(f"\nCurrent selection ({len(current_attrs)} attributes):")
            for i, attr in enumerate(all_attributes, 1):
                status = "✓" if attr in current_attrs else " "
                desc = ATTRIBUTE_DESCRIPTIONS[attr]
                print(f"{i:2d}. [{status}] {desc}")

            choice = input("\nEnter attribute number to toggle (or 'b' to go back): ").strip()

            if choice.lower() == "b":
                break

            attr_num = int(choice)
            if 1 <= attr_num <= len(all_attributes):
                attr = all_attributes[attr_num - 1]
                if attr in current_attrs:
                    current_attrs.remove(attr)
                    print(f"Removed: {ATTRIBUTE_DESCRIPTIONS[attr]}")
                else:
                    current_attrs.add(attr)
                    print(f"Added: {ATTRIBUTE_DESCRIPTIONS[attr]}")
            else:
                print(f"Please enter a number between 1 and {len(all_attributes)}")

        except ValueError:
            print("Please enter a valid number or 'b' to go back")


def curate_showcase_projects_interactive(user_id: str) -> None:
    """Interactive interface for selecting showcase projects."""
    print("\n" + "=" * 70)
    print("SHOWCASE PROJECTS SELECTION (Top 3)")
    print("=" * 70)

    # Get user's projects
    projects = get_user_projects(user_id)
    if not projects:
        print("\nNo projects found. Please analyze some repositories first.")
        return

    if len(projects) <= 3:
        print(f"\nYou have {len(projects)} projects. Showing all for reference:")
    else:
        print(f"\nYou have {len(projects)} projects. Choose your top 3 to showcase:")

    # Get current showcase settings
    settings = get_user_curation_settings(user_id)
    current_showcase = set(settings.showcase_project_ids)

    print("-" * 70)

    # Show projects with selection status
    for i, project in enumerate(projects, 1):
        status = "★" if project["id"] in current_showcase else " "
        print(f"{i:2d}. [{status}] {project['project_name']}")

        # Show key details
        lang = project["primary_language"] or "Unknown"
        files = project["total_files"] or 0
        tests = "Yes" if project["has_tests"] else "No"

        print(f"     {lang} | {files} files | Tests: {tests}")

        if project["effective_last_commit_date"]:
            print(f"     Last commit: {project['effective_last_commit_date'][:10]}")
        elif project["effective_last_modified_date"]:
            print(f"     Last modified: {project['effective_last_modified_date'][:10]}")

        print()

    print("★ = currently selected for showcase")
    print(f"Currently showcasing: {len(current_showcase)}/3 projects")

    if len(projects) <= 3:
        # Auto-select all if 3 or fewer projects
        all_ids = [p["id"] for p in projects]
        if save_showcase_projects(user_id, all_ids):
            print("✅ All projects automatically selected for showcase!")
        else:
            print("❌ Failed to save showcase selection")
        return

    while True:
        try:
            print("\nOptions:")
            print("  1. Toggle project selection")
            print("  2. Clear all selections")
            print("  3. Save and exit")
            print("  4. Show comparison of selected projects")
            print("  q. Quit without saving")

            choice = input("\nEnter option: ").strip()

            if choice == "1":
                _toggle_showcase_projects(projects, current_showcase)
            elif choice == "2":
                current_showcase.clear()
                print("Cleared all showcase selections")
            elif choice == "3":
                if len(current_showcase) == 0:
                    print("Please select at least one project to showcase")
                    continue
                elif len(current_showcase) > 3:
                    print("Please select maximum 3 projects to showcase")
                    continue

                if save_showcase_projects(user_id, list(current_showcase)):
                    print("✅ Showcase projects saved successfully!")
                    break
                else:
                    print("❌ Failed to save showcase selection")

            elif choice == "4":
                if current_showcase:
                    showcase_projects = [p for p in projects if p["id"] in current_showcase]
                    print("\nComparison of selected showcase projects:")
                    print(format_project_comparison(showcase_projects, user_id))
                else:
                    print("No projects selected for showcase")

            elif choice.lower() == "q":
                print("Cancelled - no changes saved")
                break
            else:
                print("Invalid option")

        except KeyboardInterrupt:
            print("\nCancelled.")
            break


def _toggle_showcase_projects(projects: List[Dict[str, Any]], current_showcase: set) -> None:
    """Toggle individual showcase project selection."""
    while True:
        try:
            print(f"\nShowcase selection ({len(current_showcase)}/3):")
            for i, project in enumerate(projects, 1):
                status = "★" if project["id"] in current_showcase else " "
                print(f"{i:2d}. [{status}] {project['project_name']}")

            choice = input("\nEnter project number to toggle (or 'b' to go back): ").strip()

            if choice.lower() == "b":
                break

            project_num = int(choice)
            if 1 <= project_num <= len(projects):
                project = projects[project_num - 1]
                project_id = project["id"]

                if project_id in current_showcase:
                    current_showcase.remove(project_id)
                    print(f"Removed from showcase: {project['project_name']}")
                else:
                    if len(current_showcase) >= 3:
                        print("Maximum 3 projects can be showcased. Remove one first.")
                    else:
                        current_showcase.add(project_id)
                        print(f"Added to showcase: {project['project_name']}")
            else:
                print(f"Please enter a number between 1 and {len(projects)}")

        except ValueError:
            print("Please enter a valid number or 'b' to go back")


def display_curation_status(user_id: str) -> None:
    """Display user's current curation status."""
    print("\n" + "=" * 70)
    print("CURATION STATUS")
    print("=" * 70)

    try:
        # Initialize tables if needed
        init_curation_tables()

        # Get settings
        settings = get_user_curation_settings(user_id)
        corrections = get_chronology_corrections(user_id)
        showcase = get_showcase_projects(user_id)

        # Comparison attributes
        print(f"\nComparison Attributes ({len(settings.comparison_attributes)} selected):")
        for attr in settings.comparison_attributes:
            desc = ATTRIBUTE_DESCRIPTIONS.get(attr, attr)
            print(f"  • {desc}")

        # Showcase projects
        print(f"\nShowcase Projects ({len(settings.showcase_project_ids)}/3 selected):")
        if showcase:
            for project in showcase:
                print(f"  ★ {project['project_name']}")
                if project["primary_language"]:
                    print(f"    {project['primary_language']} | {project['total_files']} files")
        else:
            print("  (None selected)")

        # Chronology corrections
        print(f"\nChronology Corrections ({len(corrections)} made):")
        if corrections:
            recent_corrections = corrections[:5]  # Show 5 most recent
            for correction in recent_corrections:
                print(f"  • Project ID {correction.project_id} - {correction.correction_timestamp[:19]}")
            if len(corrections) > 5:
                print(f"  ... and {len(corrections) - 5} more")
        else:
            print("  (None made)")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"Error displaying curation status: {e}")


def display_showcase_summary(user_id: str) -> None:
    """Display a summary of user's showcase projects."""
    print("\n" + "=" * 70)
    print("SHOWCASE PROJECTS SUMMARY")
    print("=" * 70)

    showcase = get_showcase_projects(user_id)
    if not showcase:
        print("\nNo showcase projects selected.")
        print("Use 'mda curate showcase' to choose your top projects.")
        return

    for i, project in enumerate(showcase, 1):
        print(f"\n{i}. {project['project_name']}")
        print("-" * 50)

        # Key metrics
        print(f"Primary Language: {project['primary_language'] or 'Unknown'}")
        print(f"Total Files: {project['total_files'] or 0}")
        print(f"Code Files: {project['code_files'] or 0}")
        print(f"Test Files: {project['test_files'] or 0}")
        print(f"Has Tests: {'Yes' if project['has_tests'] else 'No'}")
        print(f"Has CI/CD: {'Yes' if project['has_ci_cd'] else 'No'}")

        # Dates
        if project["effective_last_commit_date"]:
            print(f"Last Commit: {project['effective_last_commit_date'][:19]}")
        elif project["effective_last_modified_date"]:
            print(f"Last Modified: {project['effective_last_modified_date'][:19]}")

        # Technologies
        if project["languages"]:
            langs = list(project["languages"].keys())[:3]
            print(f"Languages: {', '.join(langs)}")

        if project["frameworks"]:
            fws = project["frameworks"][:3]
            print(f"Frameworks: {', '.join(fws)}")

    print("\n" + "=" * 70)
