import sys
from pathlib import Path

import pytest

current_dir = Path(__file__).parent
tests_dir = current_dir.parent
src_dir = tests_dir.parent
backend_dir = src_dir / "backend"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from backend.analysis.resume_generator import (_detect_project_type,
                                               _generate_architecture_items,
                                               _generate_opening_item,
                                               _generate_project_items,
                                               _generate_tech_items,
                                               format_resume_items,
                                               generate_formatted_resume_entry,
                                               generate_full_resume,
                                               generate_resume_items)


def test_detect_web_app():
    """Test detection of web application."""
    project = {
        "frameworks": ["React", "Express"],
        "dependencies": {"npm": ["react", "express"]},
    }
    assert _detect_project_type(project) == "web_app"


def test_detect_api():
    """Test detection of API."""
    project = {
        "frameworks": ["FastAPI"],
        "dependencies": {"pip": ["fastapi", "rest-api"]},
    }
    assert _detect_project_type(project) == "api"


def test_detect_backend():
    """Test detection of backend service."""
    project = {
        "frameworks": [],
        "dependencies": {"pip": ["sqlalchemy"]},
    }
    assert _detect_project_type(project) == "backend"


def test_detect_library():
    """Test detection of library."""
    project = {
        "code_files": 10,
        "test_files": 5,
        "frameworks": [],
        "dependencies": {},
    }
    assert _detect_project_type(project) == "library"


def test_detect_application_default():
    """Test default application type."""
    project = {
        "code_files": 5,
        "test_files": 0,
        "frameworks": [],
        "dependencies": {},
    }
    assert _detect_project_type(project) == "application"


def test_opening_item():
    """Test opening item."""
    project = {
        "project_name": "TestProject",
        "primary_language": "Python",
        "code_files": 60,
        "frameworks": ["FastAPI", "SQLAlchemy"],
    }
    item = _generate_opening_item(project, "TestProject", "web_app")
    assert "TestProject" in item
    assert "web application" in item
    assert "60" in item
    assert "FastAPI" in item


def test_directory_depth():
    """Test directory depth items."""
    project = {
        "project_name": "TestProject",
        "directory_depth": 5,
    }
    items = _generate_architecture_items(project, "TestProject", "application")
    assert any("5-level" in item or "hierarchical" in item.lower() for item in items)


def test_database_integration():
    """Test database integration."""
    project = {
        "project_name": "TestProject",
        "dependencies": {"pip": ["sqlalchemy", "flask"]},
    }
    items = _generate_tech_items(project, "TestProject", "application")
    assert any("database" in item.lower() or "sqlalchemy" in item.lower() for item in items)


def test_complete_project():
    """Test complete project with all features."""
    project = {
        "project_name": "TestProject",
        "primary_language": "Python",
        "code_files": 50,
        "frameworks": ["FastAPI"],
        "dependencies": {"pip": ["fastapi", "sqlalchemy"]},
        "oop_analysis": {
            "total_classes": 10,
            "inheritance_depth": 2,
        },
        "test_files": 15,
        "code_files": 30,
        "has_tests": True,
        "has_ci_cd": True,
        "has_docker": True,
    }
    items = _generate_project_items(project)
    assert len(items) > 0
    assert all(isinstance(item, str) for item in items)
    assert any("TestProject" in item for item in items)


def test_empty_report():
    """Test empty report."""
    report = {"projects": []}
    items = generate_resume_items(report)
    assert items == []


def test_single_project():
    """Test single project."""
    report = {
        "projects": [
            {
                "project_name": "TestProject",
                "code_files": 20,
                "primary_language": "Python",
            }
        ]
    }
    items = generate_resume_items(report)
    assert len(items) > 0


def test_multiple_projects():
    """Test multiple projects."""
    report = {
        "projects": [
            {
                "project_name": "Project1",
                "code_files": 20,
            },
            {
                "project_name": "Project2",
                "code_files": 30,
            },
        ]
    }
    items = generate_resume_items(report)
    assert len(items) > 0
    assert any("Project1" in item for item in items)
    assert any("Project2" in item for item in items)


def test_format_items():
    """Test formatting items."""
    items = ["Item 1", "Item 2", "Item 3"]
    formatted = format_resume_items(items)
    assert "Item 1" in formatted
    assert "Item 2" in formatted
    assert "•" in formatted


def test_format_empty_items():
    """Test formatting empty items."""
    items = []
    formatted = format_resume_items(items)
    assert "No resume items" in formatted


def test_formatted_entry_with_docker():
    """Test formatted entry with Docker."""
    project = {
        "project_name": "TestProject",
        "has_docker": True,
        "languages": {"python": 10},
        "dependencies": {},
    }
    entry = generate_formatted_resume_entry(project)
    assert "Docker" in entry or "docker" in entry.lower()


def test_full_resume():
    """Test full resume."""
    report = {
        "projects": [
            {
                "project_name": "TestProject",
                "code_files": 20,
                "languages": {"python": 10},
            }
        ]
    }
    resume = generate_full_resume(report)
    assert "TestProject" in resume
    assert isinstance(resume, str)
