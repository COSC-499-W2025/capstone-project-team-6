"""
Test Project Comparison Functionality
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from project_comparison import calculate_project_change_percentage, process_incremental_projects


@pytest.fixture
def base_project():
    """Base project fixture with comprehensive metadata."""
    return {
        "project_path": "test_project",
        "languages": {"python": 80, "javascript": 20},
        "metadata": {
            "total_lines_of_code": 1000,
            "files": {
                "code": {"python": [{"path": "main.py"}, {"path": "utils.py"}]},
                "summary": {"code_files": 2, "doc_files": 1, "test_files": 1},
            },
        },
        "oop_analysis": {"total_classes": 5, "private_methods": 10, "public_methods": 15},
    }


def test_identical_projects(base_project):
    """Test identical projects should have ~0% change."""
    proj_copy = base_project.copy()
    change = calculate_project_change_percentage(base_project, proj_copy)
    assert change < 5, f"Expected <5% change for identical projects, got {change:.2f}%"


def test_minor_changes(base_project):
    """Test minor changes should be <50% change."""
    project_updated = base_project.copy()
    project_updated["metadata"] = base_project["metadata"].copy()
    project_updated["metadata"]["total_lines_of_code"] = 1100  # 10% increase

    change = calculate_project_change_percentage(base_project, project_updated)
    assert change < 50, f"Expected <50% change for minor updates, got {change:.2f}%"


def test_major_changes(base_project):
    """Test major changes should be >50% change."""
    project_major = {
        "project_path": "test_project",
        "languages": {"python": 60, "javascript": 30, "typescript": 10},  # New language
        "metadata": {
            "total_lines_of_code": 2500,  # 150% increase
            "files": {
                "code": {
                    "python": [
                        {"path": "main.py"},
                        {"path": "utils.py"},
                        {"path": "new_module.py"},
                        {"path": "another_module.py"},
                    ]
                },
                "summary": {"code_files": 6, "doc_files": 3, "test_files": 4},
            },
        },
        "oop_analysis": {"total_classes": 12, "private_methods": 25, "public_methods": 30},
    }

    change = calculate_project_change_percentage(base_project, project_major)
    assert change > 50, f"Expected >50% change for major updates, got {change:.2f}%"


def test_complete_rewrite(base_project):
    """Test complete rewrite should be >80% change."""
    project_rewrite = {
        "project_path": "test_project",
        "languages": {"rust": 100},  # Completely different language
        "metadata": {
            "total_lines_of_code": 500,
            "files": {
                "code": {"rust": [{"path": "main.rs"}, {"path": "lib.rs"}]},
                "summary": {"code_files": 2, "doc_files": 0, "test_files": 0},
            },
        },
        "oop_analysis": {"total_classes": 0, "private_methods": 0, "public_methods": 0},
    }

    change = calculate_project_change_percentage(base_project, project_rewrite)
    assert change > 80, f"Expected >80% change for complete rewrite, got {change:.2f}%"


def test_process_incremental_mixed():
    """Test processing with added, updated, and skipped projects."""
    existing = [
        {
            "project_path": "project_a",
            "code_files": 10,
            "total_files": 15,
            "total_commits": 50,
            "languages": {"python": 80, "javascript": 20},
        },
        {
            "project_path": "project_b",
            "code_files": 5,
            "total_files": 8,
            "total_commits": 20,
            "languages": {"python": 100},
        },
    ]

    new = [
        {
            "project_path": "project_a",
            "code_files": 11,  # Minor change: +1 file
            "total_files": 16,
            "total_commits": 52,  # Minor change: +2 commits
            "languages": {"python": 80, "javascript": 20},
        },
        {
            "project_path": "project_b",
            "code_files": 20,  # Major change: 5 -> 20 files (300% increase)
            "total_files": 30,
            "total_commits": 100,  # Major change: 20 -> 100 commits (400% increase)
            "languages": {"python": 70, "typescript": 30},  # New language
        },
        {
            "project_path": "project_c",
            "code_files": 8,
            "total_files": 12,
            "total_commits": 30,
            "languages": {"javascript": 100},
        },
    ]

    result = process_incremental_projects(existing, new, 50.0)

    assert len(result["added_projects"]) == 1, f"Expected 1 added project, got {len(result['added_projects'])}"
    assert len(result["updated_projects"]) == 1, f"Expected 1 updated project, got {len(result['updated_projects'])}"
    assert len(result["skipped_projects"]) == 1, f"Expected 1 skipped project, got {len(result['skipped_projects'])}"
    assert len(result["merged_projects"]) == 3, f"Expected 3 total projects, got {len(result['merged_projects'])}"

    # Verify correct categorization
    assert result["added_projects"][0]["project_path"] == "project_c"
    assert result["updated_projects"][0]["project_path"] == "project_b"
    assert result["skipped_projects"][0]["project_path"] == "project_a"


def test_new_projects_only():
    """Test adding only new projects (no existing)."""
    existing = []
    new = [
        {"project_path": "project_a", "metadata": {"total_lines_of_code": 1000}},
        {"project_path": "project_b", "metadata": {"total_lines_of_code": 500}},
    ]

    result = process_incremental_projects(existing, new, 50.0)

    assert len(result["added_projects"]) == 2
    assert len(result["updated_projects"]) == 0
    assert len(result["skipped_projects"]) == 0
    assert len(result["merged_projects"]) == 2


def test_no_new_projects():
    """Test when no new projects are provided."""
    existing = [{"project_path": "project_a", "metadata": {"total_lines_of_code": 1000}}]
    new = []

    result = process_incremental_projects(existing, new, 50.0)

    assert len(result["added_projects"]) == 0
    assert len(result["updated_projects"]) == 0
    assert len(result["skipped_projects"]) == 0
    assert len(result["merged_projects"]) == 1


def test_custom_threshold_50():
    """Test with 50% threshold - should skip 30% change."""
    existing = [
        {
            "project_path": "project_a",
            "code_files": 10,
            "total_files": 15,
            "total_commits": 100,
        }
    ]
    new = [
        {
            "project_path": "project_a",
            "code_files": 13,  # 30% change
            "total_files": 19,  # ~27% change
            "total_commits": 130,  # 30% change
        }
    ]

    result = process_incremental_projects(existing, new, change_threshold=50.0)

    assert len(result["skipped_projects"]) == 1
    assert len(result["updated_projects"]) == 0


def test_custom_threshold_20():
    """Test with 20% threshold - should update 30% change."""
    existing = [
        {
            "project_path": "project_a",
            "code_files": 10,
            "total_files": 15,
            "total_commits": 100,
        }
    ]
    new = [
        {
            "project_path": "project_a",
            "code_files": 13,  # 30% change
            "total_files": 19,  # ~27% change
            "total_commits": 130,  # 30% change
        }
    ]

    result = process_incremental_projects(existing, new, change_threshold=20.0)

    assert len(result["skipped_projects"]) == 0
    assert len(result["updated_projects"]) == 1


def test_change_percentage_details():
    """Test that change percentage is calculated and reported correctly."""
    existing = [
        {
            "project_path": "project_a",
            "languages": {"python": 100},
            "code_files": 1,
            "total_files": 3,
            "test_files": 1,
            "doc_files": 1,
            "total_commits": 50,
        }
    ]
    new = [
        {
            "project_path": "project_a",
            "languages": {"python": 80, "javascript": 20},  # Added language
            "code_files": 3,  # Tripled
            "total_files": 8,  # More than doubled
            "test_files": 3,  # Tripled
            "doc_files": 2,  # Doubled
            "total_commits": 150,  # Tripled
        }
    ]

    result = process_incremental_projects(existing, new, 50.0)

    # Should be updated due to >50% change across multiple dimensions
    assert len(result["updated_projects"]) == 1, f"Expected 1 update, got {len(result['updated_projects'])}"
    assert "change_percentage" in result["updated_projects"][0]
    assert result["updated_projects"][0]["change_percentage"] > 50


def test_multiple_updates_and_adds():
    """Test scenario with multiple updates and additions."""
    existing = [
        {"project_path": "proj1", "code_files": 10, "total_files": 15, "total_commits": 50},
        {"project_path": "proj2", "code_files": 5, "total_files": 8, "total_commits": 20},
        {"project_path": "proj3", "code_files": 7, "total_files": 10, "total_commits": 30},
    ]

    new = [
        {"project_path": "proj1", "code_files": 30, "total_files": 45, "total_commits": 150},  # Major update (3x)
        {"project_path": "proj2", "code_files": 6, "total_files": 9, "total_commits": 22},  # Minor update (~10%)
        {"project_path": "proj3", "code_files": 25, "total_files": 35, "total_commits": 120},  # Major update (3-4x)
        {"project_path": "proj4", "code_files": 6, "total_files": 10, "total_commits": 25},  # New
        {"project_path": "proj5", "code_files": 8, "total_files": 12, "total_commits": 35},  # New
    ]

    result = process_incremental_projects(existing, new, 50.0)

    assert len(result["added_projects"]) == 2  # proj4, proj5
    assert len(result["updated_projects"]) == 2  # proj1, proj3
    assert len(result["skipped_projects"]) == 1  # proj2
    assert len(result["merged_projects"]) == 5  # All projects
