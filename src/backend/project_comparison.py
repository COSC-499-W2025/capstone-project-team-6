"""
Project Comparison Utilities
"""

from typing import Any, Dict


def calculate_project_change_percentage(old_project: Dict[str, Any], new_project: Dict[str, Any]) -> float:
    """Calculate the percentage of changes between two project versions."""
    total_checks = 0
    changes = 0

    # Compare file counts and names
    old_files = old_project.get("metadata", {}).get("files", {})
    new_files = new_project.get("metadata", {}).get("files", {})

    # Compare code files
    old_code_files = set()
    new_code_files = set()

    for lang_files in old_files.get("code", {}).values():
        if isinstance(lang_files, list):
            old_code_files.update([f.get("path", "") for f in lang_files if isinstance(f, dict)])

    for lang_files in new_files.get("code", {}).values():
        if isinstance(lang_files, list):
            new_code_files.update([f.get("path", "") for f in lang_files if isinstance(f, dict)])

    if old_code_files or new_code_files:
        total_checks += 1
        # Calculate Jaccard distance as change metric
        if old_code_files and new_code_files:
            intersection = len(old_code_files & new_code_files)
            union = len(old_code_files | new_code_files)
            if union > 0:
                similarity = intersection / union
                changes += 1 - similarity  # Convert similarity to change
        elif old_code_files or new_code_files:
            changes += 1  # Complete change if one is empty

    # Compare lines of code
    old_loc = old_project.get("metadata", {}).get("total_lines_of_code", 0)
    new_loc = new_project.get("metadata", {}).get("total_lines_of_code", 0)

    if old_loc or new_loc:
        total_checks += 1
        max_loc = max(old_loc, new_loc)
        if max_loc > 0:
            loc_change = abs(old_loc - new_loc) / max_loc
            changes += min(loc_change, 1.0)  # Cap at 1.0

    # Compare languages
    old_langs = set(old_project.get("languages", {}).keys())
    new_langs = set(new_project.get("languages", {}).keys())

    if old_langs or new_langs:
        total_checks += 1
        if old_langs and new_langs:
            lang_intersection = len(old_langs & new_langs)
            lang_union = len(old_langs | new_langs)
            if lang_union > 0:
                lang_similarity = lang_intersection / lang_union
                changes += 1 - lang_similarity
        elif old_langs or new_langs:
            changes += 1

    # Compare file counts by type
    old_file_counts = old_files.get("summary", {})
    new_file_counts = new_files.get("summary", {})

    for file_type in ["code_files", "doc_files", "test_files", "config_files"]:
        old_count = old_file_counts.get(file_type, 0)
        new_count = new_file_counts.get(file_type, 0)

        if old_count or new_count:
            total_checks += 1
            max_count = max(old_count, new_count)
            if max_count > 0:
                count_change = abs(old_count - new_count) / max_count
                changes += min(count_change, 1.0)

    # Compare OOP metrics if available
    old_oop = old_project.get("oop_analysis", {})
    new_oop = new_project.get("oop_analysis", {})

    if old_oop and new_oop:
        for metric in ["total_classes", "private_methods", "public_methods"]:
            old_val = old_oop.get(metric, 0)
            new_val = new_oop.get(metric, 0)

            if old_val or new_val:
                total_checks += 1
                max_val = max(old_val, new_val)
                if max_val > 0:
                    metric_change = abs(old_val - new_val) / max_val
                    changes += min(metric_change, 1.0)

    # Calculate overall change percentage
    if total_checks == 0:
        return 100.0  # If we can't compare, assume complete change

    change_percentage = (changes / total_checks) * 100.0
    return min(change_percentage, 100.0)


def process_incremental_projects(existing_projects: list, new_projects: list, change_threshold: float = 50.0) -> Dict[str, Any]:
    """Process new projects against existing ones with change detection.

    Args:
        existing_projects: List of existing project dictionaries
        new_projects: List of new project dictionaries to merge
        change_threshold: Minimum percentage change required to update (default: 50.0)

    Returns:
        Dictionary containing:
        - merged_projects: Combined list of projects
        - added_projects: List of newly added projects
        - updated_projects: List of updated projects with change details
        - skipped_projects: List of skipped projects with change details
    """
    # Build a map of existing projects by path for quick lookup
    existing_project_map = {p.get("project_path"): i for i, p in enumerate(existing_projects)}

    added_projects = []
    updated_projects = []
    skipped_projects = []

    # Work with a copy of existing projects to allow modifications
    merged_projects = existing_projects.copy()

    for new_project in new_projects:
        project_path = new_project.get("project_path")

        if project_path in existing_project_map:
            # Project exists, check for changes
            existing_index = existing_project_map[project_path]
            old_project = merged_projects[existing_index]

            # Calculate change percentage
            change_percentage = calculate_project_change_percentage(old_project, new_project)

            if change_percentage > change_threshold:
                # Update the existing project
                merged_projects[existing_index] = new_project
                updated_projects.append({"project_path": project_path, "change_percentage": round(change_percentage, 2)})
            else:
                # Skip update, changes are too small
                skipped_projects.append({"project_path": project_path, "change_percentage": round(change_percentage, 2)})
        else:
            # New project, add it
            merged_projects.append(new_project)
            added_projects.append(new_project)

    return {
        "merged_projects": merged_projects,
        "added_projects": added_projects,
        "updated_projects": updated_projects,
        "skipped_projects": skipped_projects,
    }
