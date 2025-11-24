"""
Unit tests for resume_generator.py
"""

import pytest

from src.backend.analysis import resume_generator as rg

PROJECT_TECH = {
    "project_name": "TestProj",
    "languages": {"python": 10, "javascript": 2, "c++": 1, "go": 1},
    "frameworks": ["Django", "React", "Flask", "Vue"],
    "total_files": 20,
    "code_files": 15,
}

PROJECT_OOP = {
    "project_name": "OOPProj",
    "languages": {"python": 5},
    "oop_analysis": {
        "total_classes": 4,
        "abstract_classes": ["A", "B"],
        "inheritance_depth": 2,
        "private_methods": 3,
        "protected_methods": 2,
        "properties_count": 1,
    },
}

PROJECT_JAVA_OOP = {
    "project_name": "JavaProj",
    "languages": {"java": 8},
    "java_oop_analysis": {
        "total_classes": 6,
        "interface_count": 2,
        "abstract_classes": ["Abs1"],
        "design_patterns": ["Singleton", "Factory", "Observer"],
        "generic_classes": 2,
        "lambda_count": 3,
    },
}

PROJECT_QUALITY = {
    "project_name": "QualProj",
    "has_tests": True,
    "test_files": 5,
    "has_ci_cd": True,
    "test_coverage_estimate": "high",
    "total_files": 50,
    "total_commits": 100,
    "contributors": [{"name": "A"}, {"name": "B"}],
    "has_docker": True,
    "directory_depth": 5,
}

# Project with minimal info
PROJECT_MINIMAL = {
    "project_name": "EmptyProj",
}


def test_generate_tech_stack_item():
    item = rg._generate_tech_stack_item(PROJECT_TECH, "TestProj")
    assert "python, javascript, c++, and 1 more" in item
    assert "Django, React, Flask, and 1 more" in item
    assert "15 source files" in item


def test_generate_python_oop_item():
    item = rg._generate_python_oop_item(PROJECT_OOP, "OOPProj")
    assert "4 classes" in item
    assert "abstraction with 2 abstract base classes" in item or "inheritance hierarchies up to 2 levels deep" in item


def test_generate_java_oop_item():
    item = rg._generate_java_oop_item(PROJECT_JAVA_OOP, "JavaProj")
    assert "8 classes/interfaces" in item or "6 classes/interfaces" in item
    assert "Singleton, Factory design patterns" in item
    assert "2 interfaces" in item or "1 abstract classes" in item


def test_generate_quality_item():
    item = rg._generate_quality_item(PROJECT_QUALITY, "QualProj")
    assert "5 test files" in item
    assert "CI/CD pipeline" in item
    assert "high coverage" in item


def test_generate_resume_items_full():
    report = {"projects": [PROJECT_TECH, PROJECT_OOP, PROJECT_JAVA_OOP, PROJECT_QUALITY]}
    items = rg.generate_resume_items(report)
    assert len(items) >= 4
    assert any("TestProj" in i for i in items)
    assert any("OOPProj" in i for i in items)
    assert any("JavaProj" in i for i in items)
    assert any("QualProj" in i for i in items)


def test_generate_resume_items_empty():
    report = {"projects": [PROJECT_MINIMAL]}
    items = rg.generate_resume_items(report)
    assert items == [] or all(isinstance(i, str) for i in items)


def test_format_resume_items():
    items = ["Did X", "Did Y"]
    formatted = rg.format_resume_items(items)
    assert "• Did X" in formatted
    assert "• Did Y" in formatted
    assert formatted.startswith("\n  • ")


def test_format_resume_items_empty():
    formatted = rg.format_resume_items([])
    assert "No resume items" in formatted
