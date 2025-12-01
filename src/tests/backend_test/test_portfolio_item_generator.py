# test_portfolio_item_generator.py

import pytest

from backend.analysis.portfolio_item_generator import (
    _calculate_project_quality_score, _generate_architecture_description,
    _generate_contributions_summary, _generate_skills_list,
    generate_portfolio_item)

# ------------------------------------------------------------
# FIXTURES
# ------------------------------------------------------------


@pytest.fixture
def basic_project():
    """Basic project: 1 class, has readme, no tests."""
    return {
        "project_name": "BasicProj",
        "languages": {"python": 3},
        "frameworks": [],
        "total_files": 5,
        "code_files": 3,
        "test_files": 0,
        "doc_files": 1,
        "has_tests": False,
        "has_readme": True,
        "has_ci_cd": False,
        "has_docker": False,
        "test_coverage_estimate": "none",
        "oop_analysis": {
            "total_classes": 1,
            "classes_with_inheritance": 0,
            "abstract_classes": [],
            "inheritance_depth": 0,
            "properties_count": 0,
            "operator_overloads": 0,
        },
        "java_oop_analysis": {},
    }


@pytest.fixture
def intermediate_project():
    """Intermediate project: 8 classes, some OOP, 1 pattern, medium tests."""
    return {
        "project_name": "IntermediateProj",
        "languages": {"python": 7, "java": 3},
        "frameworks": ["Flask"],
        "total_files": 15,
        "code_files": 12,
        "test_files": 2,
        "doc_files": 1,
        "has_tests": True,
        "has_readme": True,
        "has_ci_cd": False,
        "has_docker": False,
        "test_coverage_estimate": "medium",
        "oop_analysis": {
            "total_classes": 5,
            "classes_with_inheritance": 2,
            "abstract_classes": ["BaseClass"],
            "inheritance_depth": 1,
            "properties_count": 3,
            "operator_overloads": 1,
        },
        "java_oop_analysis": {
            "total_classes": 3,
            "classes_with_inheritance": 1,
            "abstract_classes": [],
            "inheritance_depth": 1,
            "design_patterns": ["Factory"],
            "lambda_count": 2,
        },
    }


@pytest.fixture
def advanced_project():
    """Advanced project: 15 classes, full OOP, patterns, high test coverage."""
    return {
        "project_name": "AdvancedProj",
        "languages": {"python": 10, "java": 5},
        "frameworks": ["Flask", "Spring"],
        "total_files": 25,
        "code_files": 18,
        "test_files": 5,
        "doc_files": 2,
        "has_tests": True,
        "has_readme": True,
        "has_ci_cd": True,
        "has_docker": True,
        "test_coverage_estimate": "high",
        "oop_analysis": {
            "total_classes": 9,
            "classes_with_inheritance": 4,
            "abstract_classes": ["BaseA", "BaseB"],
            "inheritance_depth": 2,
            "properties_count": 8,
            "operator_overloads": 2,
        },
        "java_oop_analysis": {
            "total_classes": 6,
            "classes_with_inheritance": 3,
            "abstract_classes": ["AbstractX"],
            "inheritance_depth": 2,
            "design_patterns": ["Factory", "Singleton"],
            "lambda_count": 5,
        },
    }


@pytest.fixture
def empty_project():
    """Edge case: project with no OOP, no tests, minimal structure."""
    return {
        "project_name": "EmptyProj",
        "languages": {"python": 1},
        "frameworks": [],
        "total_files": 3,
        "code_files": 2,
        "test_files": 0,
        "doc_files": 0,
        "has_tests": False,
        "has_readme": False,
        "has_ci_cd": False,
        "has_docker": False,
        "test_coverage_estimate": "none",
        "oop_analysis": {
            "total_classes": 0,
            "classes_with_inheritance": 0,
            "abstract_classes": [],
            "inheritance_depth": 0,
            "properties_count": 0,
            "operator_overloads": 0,
        },
        "java_oop_analysis": {},
    }


# ------------------------------------------------------------
# TESTS: QUALITY SCORE CALCULATION
# ------------------------------------------------------------


def test_quality_score_basic(basic_project):
    """Basic project should score low and be classified as 'basic'."""
    quality = _calculate_project_quality_score(basic_project)

    assert quality["sophistication_level"] == "basic"
    assert quality["quality_score"] < 30
    assert quality["total_classes"] == 1
    assert not quality["uses_inheritance"]
    assert not quality["uses_abstraction"]


def test_quality_score_intermediate(intermediate_project):
    """Intermediate project should score 30-49 and be 'intermediate'."""
    quality = _calculate_project_quality_score(intermediate_project)

    assert quality["sophistication_level"] == "intermediate"
    assert 30 <= quality["quality_score"] < 50
    assert quality["total_classes"] == 8
    assert quality["uses_inheritance"]
    assert quality["uses_abstraction"]
    assert "Factory" in quality["design_patterns"]


def test_quality_score_advanced(advanced_project):
    """Advanced project should score 50+ and be 'advanced'."""
    quality = _calculate_project_quality_score(advanced_project)

    assert quality["sophistication_level"] == "advanced"
    assert quality["quality_score"] >= 50
    assert quality["total_classes"] == 15
    assert quality["uses_inheritance"]
    assert quality["uses_abstraction"]
    assert len(quality["design_patterns"]) == 2


def test_quality_score_empty(empty_project):
    """Empty project should score very low."""
    quality = _calculate_project_quality_score(empty_project)

    assert quality["sophistication_level"] == "basic"
    assert quality["quality_score"] == 0
    assert quality["total_classes"] == 0


# ------------------------------------------------------------
# TESTS: ARCHITECTURE DESCRIPTION
# ------------------------------------------------------------


def test_architecture_basic(basic_project):
    """Basic project should have foundational description."""
    quality = _calculate_project_quality_score(basic_project)
    text = _generate_architecture_description(basic_project, quality)

    assert "1 Python classes" in text
    assert "foundational" in text.lower()


def test_architecture_intermediate(intermediate_project):
    """Intermediate project should mention OOP principles."""
    quality = _calculate_project_quality_score(intermediate_project)
    text = _generate_architecture_description(intermediate_project, quality)

    assert "5 Python classes" in text
    assert "3 Java classes" in text
    assert "object-oriented principles" in text.lower()
    assert "Factory patterns" in text


def test_architecture_advanced(advanced_project):
    """Advanced project should have detailed OOP description."""
    quality = _calculate_project_quality_score(advanced_project)
    text = _generate_architecture_description(advanced_project, quality)

    assert "9 Python classes" in text
    assert "6 Java classes" in text
    assert "advanced" in text.lower()
    assert "abstract classes" in text.lower()


def test_architecture_empty(empty_project):
    """Empty project should use fallback description."""
    quality = _calculate_project_quality_score(empty_project)
    text = _generate_architecture_description(empty_project, quality)

    assert "modular structure" in text.lower()


# ------------------------------------------------------------
# TESTS: CONTRIBUTIONS SUMMARY
# ------------------------------------------------------------


def test_contributions_basic(basic_project):
    """Basic project should mention documentation."""
    quality = _calculate_project_quality_score(basic_project)
    text = _generate_contributions_summary(basic_project, quality)

    assert "writing documentation" in text.lower()


def test_contributions_intermediate(intermediate_project):
    """Intermediate project should mention patterns and tests."""
    quality = _calculate_project_quality_score(intermediate_project)
    text = _generate_contributions_summary(intermediate_project, quality)

    assert "abstract classes" in text.lower()
    assert "factory pattern" in text.lower()
    assert "lambda expressions" in text.lower()
    assert "tests" in text.lower()
    assert "medium coverage" in text.lower()


def test_contributions_advanced(advanced_project):
    """Advanced project should mention all advanced features."""
    quality = _calculate_project_quality_score(advanced_project)
    text = _generate_contributions_summary(advanced_project, quality)

    assert "abstract classes" in text.lower()
    assert "factory" in text.lower()
    assert "singleton" in text.lower()
    assert "lambda expressions" in text.lower()
    assert "operator overloading" in text.lower()
    assert "ci/cd" in text.lower()


def test_contributions_empty(empty_project):
    """Empty project should use fallback text."""
    quality = _calculate_project_quality_score(empty_project)
    text = _generate_contributions_summary(empty_project, quality)

    assert "core logic" in text.lower()
    assert "maintaining project structure" in text.lower()


# ------------------------------------------------------------
# TESTS: SKILLS LIST
# ------------------------------------------------------------


def test_skills_basic(basic_project):
    """Basic project should list minimal skills."""
    quality = _calculate_project_quality_score(basic_project)
    skills = _generate_skills_list(basic_project, quality)

    assert "Python OOP" in skills
    assert "Technical documentation" in skills
    assert "Unit testing" not in skills


def test_skills_intermediate(intermediate_project):
    """Intermediate project should list moderate skills."""
    quality = _calculate_project_quality_score(intermediate_project)
    skills = _generate_skills_list(intermediate_project, quality)

    assert "Python OOP" in skills
    assert "Java OOP" in skills
    assert "Flask framework" in skills
    assert "Factory design pattern" in skills
    assert "Functional programming" in skills
    assert "Test-driven development" in skills


def test_skills_advanced(advanced_project):
    """Advanced project should list many advanced skills."""
    quality = _calculate_project_quality_score(advanced_project)
    skills = _generate_skills_list(advanced_project, quality)

    assert "Python OOP" in skills
    assert "Java OOP" in skills
    assert "Factory design pattern" in skills
    assert "Singleton design pattern" in skills
    assert "Functional programming" in skills
    assert "Operator overloading" in skills
    assert "Abstract design" in skills
    assert "Test-driven development" in skills
    assert "CI/CD pipelines" in skills
    assert "Docker" in skills


# ------------------------------------------------------------
# TESTS: FULL PORTFOLIO GENERATION
# ------------------------------------------------------------


def test_generate_portfolio_basic(basic_project):
    """Full generation for basic project."""
    item = generate_portfolio_item(basic_project)

    assert item["project_name"] == "BasicProj"
    assert "software project" in item["overview"]
    assert "foundational" in item["architecture"].lower()
    assert item["project_statistics"]["sophistication_level"] == "basic"
    assert len(item["skills_exercised"]) >= 2
    assert len(item["text_summary"]) > 50


def test_generate_portfolio_intermediate(intermediate_project):
    """Full generation for intermediate project."""
    item = generate_portfolio_item(intermediate_project)

    assert item["project_name"] == "IntermediateProj"
    assert "well-structured" in item["overview"]
    assert item["project_statistics"]["sophistication_level"] == "intermediate"
    assert "Factory" in item["text_summary"]
    assert len(item["skills_exercised"]) >= 5


def test_generate_portfolio_advanced(advanced_project):
    """Full generation for advanced project."""
    item = generate_portfolio_item(advanced_project)

    assert item["project_name"] == "AdvancedProj"
    assert "advanced" in item["overview"]
    assert item["project_statistics"]["sophistication_level"] == "advanced"
    assert "Factory" in item["text_summary"]
    assert "Singleton" in item["text_summary"]
    assert len(item["skills_exercised"]) >= 8
    assert len(item["text_summary"]) > 200


def test_generate_portfolio_empty(empty_project):
    """Full generation should handle edge case gracefully."""
    item = generate_portfolio_item(empty_project)

    assert item["project_name"] == "EmptyProj"
    assert item["project_statistics"]["sophistication_level"] == "basic"
    assert len(item["text_summary"]) > 0  # Should still generate something


# ------------------------------------------------------------
# TESTS: EDGE CASES
# ------------------------------------------------------------


def test_missing_oop_analysis():
    """Should handle missing OOP analysis gracefully."""
    project = {
        "project_name": "NoOOP",
        "languages": {"javascript": 5},
        "frameworks": [],
        "total_files": 5,
        "code_files": 5,
        "test_files": 0,
        "doc_files": 0,
        "has_tests": False,
        "has_readme": False,
        "has_ci_cd": False,
        "has_docker": False,
        "test_coverage_estimate": "none",
    }

    item = generate_portfolio_item(project)
    assert item["project_name"] == "NoOOP"
    assert item["project_statistics"]["quality_score"] == 0


def test_boundary_exactly_30_points():
    """Test project scoring exactly 30 points (intermediate boundary)."""
    project = {
        "project_name": "Boundary30",
        "languages": {"python": 5},
        "frameworks": [],
        "total_files": 10,
        "code_files": 8,
        "test_files": 0,
        "doc_files": 1,
        "has_tests": False,
        "has_readme": True,
        "has_ci_cd": False,
        "has_docker": False,
        "test_coverage_estimate": "none",
        "oop_analysis": {
            "total_classes": 6,  # 18 points
            "classes_with_inheritance": 2,
            "abstract_classes": ["Base"],  # 2 points
            "inheritance_depth": 1,
            "properties_count": 5,
            "operator_overloads": 3,  # 2 points
        },
        "java_oop_analysis": {
            "total_classes": 0,
            "design_patterns": ["Factory"],  # 5 points
            "lambda_count": 2,  # 3 points
        },
    }

    quality = _calculate_project_quality_score(project)
    # 18 (classes) + 2+5+3+2 (advanced=12, capped at 10) + 1 (readme) = 29-30 points
    assert quality["sophistication_level"] == "intermediate"
