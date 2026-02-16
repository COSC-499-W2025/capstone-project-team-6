"""
Project Comparison Utilities
"""

from typing import Any, Dict


def calculate_project_change_percentage(old_project: Dict[str, Any], new_project: Dict[str, Any]) -> float:
    """Calculate the percentage of changes between two project versions."""
    import logging

    logger = logging.getLogger(__name__)

    total_checks = 0
    changes = 0

    # Compare file counts (direct fields, not nested in metadata)
    for field in ["code_files", "total_files", "test_files", "doc_files", "config_files"]:
        old_count = old_project.get(field, 0)
        new_count = new_project.get(field, 0)

        if old_count or new_count:
            total_checks += 1
            max_count = max(old_count, new_count)
            if max_count > 0:
                count_change = abs(old_count - new_count) / max_count
                changes += min(count_change, 1.0)

    # Compare code ownership if available
    old_ownership = old_project.get("code_ownership", [])
    new_ownership = new_project.get("code_ownership", [])

    if old_ownership or new_ownership:
        total_checks += 1
        old_files = {item.get("path") for item in old_ownership if isinstance(item, dict)}
        new_files = {item.get("path") for item in new_ownership if isinstance(item, dict)}

        if old_files and new_files:
            intersection = len(old_files & new_files)
            union = len(old_files | new_files)
            if union > 0:
                similarity = intersection / union
                changes += 1 - similarity
        elif old_files or new_files:
            changes += 1

    # Compare blame summary (contributor lines)
    old_blame = old_project.get("blame_summary", {})
    new_blame = new_project.get("blame_summary", {})

    if old_blame or new_blame:
        total_checks += 1
        old_total = sum(v for v in old_blame.values() if isinstance(v, (int, float)))
        new_total = sum(v for v in new_blame.values() if isinstance(v, (int, float)))

        if old_total or new_total:
            max_total = max(old_total, new_total)
            if max_total > 0:
                blame_change = abs(old_total - new_total) / max_total
                changes += min(blame_change, 1.0)

    # Compare activity breakdown
    old_activity = old_project.get("activity_breakdown", {})
    new_activity = new_project.get("activity_breakdown", {})

    if old_activity or new_activity:
        total_checks += 1
        old_contributors = set(old_activity.keys())
        new_contributors = set(new_activity.keys())

        if old_contributors and new_contributors:
            contributor_intersection = len(old_contributors & new_contributors)
            contributor_union = len(old_contributors | new_contributors)
            if contributor_union > 0:
                contributor_similarity = contributor_intersection / contributor_union
                changes += 1 - contributor_similarity
        elif old_contributors or new_contributors:
            changes += 1

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

    # Compare commit counts
    old_commits = old_project.get("total_commits", 0)
    new_commits = new_project.get("total_commits", 0)

    if old_commits or new_commits:
        total_checks += 1
        max_commits = max(old_commits, new_commits)
        if max_commits > 0:
            commit_change = abs(old_commits - new_commits) / max_commits
            changes += min(commit_change, 1.0)

    # Compare branch counts
    old_branches = old_project.get("branch_count", 0)
    new_branches = new_project.get("branch_count", 0)

    if old_branches or new_branches:
        total_checks += 1
        max_branches = max(old_branches, new_branches)
        if max_branches > 0:
            branch_change = abs(old_branches - new_branches) / max_branches
            changes += min(branch_change, 1.0)

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
        logger.warning(f"No comparable data found between projects - assuming 100% change")
        return 100.0  # If we can't compare, assume complete change

    change_percentage = (changes / total_checks) * 100.0
    logger.info(f"Change calculation: {changes:.2f} changes across {total_checks} checks = {change_percentage:.2f}%")
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
    import logging

    logger = logging.getLogger(__name__)

    # Build a map of existing projects for quick lookup
    # Use project_path as primary key, but also track by project_name for fallback matching
    existing_by_path = {}
    existing_by_name = {}

    for i, p in enumerate(existing_projects):
        path = p.get("project_path") or ""
        name = p.get("project_name") or p.get("name", "")

        # Only map by path if it's not empty
        if path:
            existing_by_path[path] = i

        # Map by name for fallback
        if name:
            existing_by_name[name] = i

    added_projects = []
    updated_projects = []
    skipped_projects = []

    # Work with a copy of existing projects to allow modifications
    merged_projects = existing_projects.copy()

    for new_project in new_projects:
        project_path = new_project.get("project_path") or ""
        project_name = new_project.get("project_name") or new_project.get("name", "")

        # Try to find a match - first by path, then by name
        existing_index = None
        match_type = None

        if project_path and project_path in existing_by_path:
            existing_index = existing_by_path[project_path]
            match_type = "path"
        elif project_name and project_name in existing_by_name:
            existing_index = existing_by_name[project_name]
            match_type = "name"

        if existing_index is not None:
            # Project exists, check for changes
            old_project = merged_projects[existing_index]

            logger.info(f"Matching project '{project_name}' (path: '{project_path}') by {match_type}")
            logger.info(f"  Old project metadata keys: {list(old_project.get('metadata', {}).keys())}")
            logger.info(f"  New project metadata keys: {list(new_project.get('metadata', {}).keys())}")

            # Calculate change percentage
            change_percentage = calculate_project_change_percentage(old_project, new_project)

            logger.info(f"  Calculated change percentage: {change_percentage:.2f}%")

            if change_percentage > change_threshold:
                # Update the existing project
                merged_projects[existing_index] = new_project
                updated_projects.append({"project_path": project_path, "change_percentage": round(change_percentage, 2)})
            else:
                # Skip update, changes are too small
                skipped_projects.append({"project_path": project_path, "change_percentage": round(change_percentage, 2)})
        else:
            # New project, add it
            logger.info(f"Adding new project '{project_name}' (path: '{project_path}')")
            merged_projects.append(new_project)
            added_projects.append(new_project)

    return {
        "merged_projects": merged_projects,
        "added_projects": added_projects,
        "updated_projects": updated_projects,
        "skipped_projects": skipped_projects,
    }
