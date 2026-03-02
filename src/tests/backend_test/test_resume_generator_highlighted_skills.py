"""
Tests for the highlighted_skills parameter in generate_resume().

Validates that curated highlighted skills override auto-extracted skills,
and that the parameter integrates correctly through the API layer.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add src directory to path
SRC = Path(__file__).resolve().parents[2]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backend.analysis.resume_generator import generate_resume

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bundle(
    name: str = "TestProject",
    language: str = "Python",
    bullets: List[str] | None = None,
    skills: List[str] | None = None,
) -> Dict[str, Any]:
    """Create a minimal project bundle for generate_resume()."""
    project = {
        "project_name": name,
        "primary_language": language,
        "total_files": 10,
    }
    resume_items = []
    if bullets:
        resume_items = [{"resume_text": b} for b in bullets]
    portfolio = {}
    if skills:
        portfolio["skills"] = skills
    return {
        "project": project,
        "resume_items": resume_items,
        "portfolio": portfolio,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHighlightedSkillsInGenerateResume:
    """Tests for the highlighted_skills parameter."""

    def test_highlighted_skills_appear_in_resume(self):
        """When highlighted_skills are provided, they should appear in the resume."""
        bundle = _make_bundle(skills=["Django", "Flask"])
        curated = ["React", "TypeScript", "FastAPI"]

        result = generate_resume(
            projects=[bundle],
            format="markdown",
            include_skills=True,
            highlighted_skills=curated,
        )

        assert "## Skills" in result
        for skill in curated:
            assert skill in result, f"Curated skill '{skill}' not found in resume"

    def test_highlighted_skills_override_portfolio_skills(self):
        """Curated skills should replace portfolio-extracted skills entirely."""
        portfolio_skills = ["OldSkill1", "OldSkill2", "OldSkill3"]
        curated_skills = ["NewSkill1", "NewSkill2"]

        bundle = _make_bundle(skills=portfolio_skills)

        result = generate_resume(
            projects=[bundle],
            format="markdown",
            include_skills=True,
            highlighted_skills=curated_skills,
        )

        # Curated skills present
        for skill in curated_skills:
            assert skill in result

        # Portfolio skills NOT present (overridden)
        for skill in portfolio_skills:
            assert skill not in result

    def test_highlighted_skills_none_falls_back_to_portfolio(self):
        """When highlighted_skills is None, skills are extracted from portfolio."""
        portfolio_skills = ["Python", "FastAPI"]
        bundle = _make_bundle(skills=portfolio_skills)

        result = generate_resume(
            projects=[bundle],
            format="markdown",
            include_skills=True,
            highlighted_skills=None,
        )

        assert "## Skills" in result
        for skill in portfolio_skills:
            assert skill in result

    def test_highlighted_skills_empty_list_falls_back(self):
        """When highlighted_skills is an empty list, falls back to portfolio skills."""
        portfolio_skills = ["Go", "Kubernetes"]
        bundle = _make_bundle(skills=portfolio_skills)

        result = generate_resume(
            projects=[bundle],
            format="markdown",
            include_skills=True,
            highlighted_skills=[],
        )

        assert "## Skills" in result
        for skill in portfolio_skills:
            assert skill in result

    def test_highlighted_skills_with_include_skills_false(self):
        """Even if highlighted_skills are provided, include_skills=False skips the section."""
        bundle = _make_bundle()
        curated = ["React", "TypeScript"]

        result = generate_resume(
            projects=[bundle],
            format="markdown",
            include_skills=False,
            highlighted_skills=curated,
        )

        assert "## Skills" not in result
        # Skills should not appear since include_skills is False
        for skill in curated:
            assert skill not in result

    def test_highlighted_skills_deduplication(self):
        """Highlighted skills should be deduplicated (set semantics)."""
        bundle = _make_bundle()
        curated = ["Python", "Python", "React", "React", "React"]

        result = generate_resume(
            projects=[bundle],
            format="markdown",
            include_skills=True,
            highlighted_skills=curated,
        )

        skills_section = result.split("## Skills")[1].split("##")[0] if "## Skills" in result else ""
        # Each skill should appear exactly once in the skills line
        assert skills_section.count("Python") == 1
        assert skills_section.count("React") == 1

    def test_highlighted_skills_with_personal_info(self):
        """Highlighted skills work alongside personal info."""
        bundle = _make_bundle(bullets=["Built a REST API"])
        curated = ["Python", "FastAPI"]
        personal = {"name": "Jane Doe", "email": "jane@example.com"}

        result = generate_resume(
            projects=[bundle],
            format="markdown",
            include_skills=True,
            highlighted_skills=curated,
            personal_info=personal,
        )

        assert "# Jane Doe" in result
        assert "jane@example.com" in result
        assert "## Skills" in result
        assert "Python" in result
        assert "FastAPI" in result
        assert "## Projects" in result

    def test_highlighted_skills_with_max_projects(self):
        """Highlighted skills work with max_projects limit."""
        bundles = [
            _make_bundle(name="Proj1", skills=["PortfolioSkill"]),
            _make_bundle(name="Proj2"),
            _make_bundle(name="Proj3"),
        ]
        curated = ["CuratedSkillA", "CuratedSkillB"]

        result = generate_resume(
            projects=bundles,
            format="markdown",
            include_skills=True,
            max_projects=1,
            highlighted_skills=curated,
        )

        # Curated skills should appear
        assert "CuratedSkillA" in result
        assert "CuratedSkillB" in result
        # Portfolio skill should NOT appear
        assert "PortfolioSkill" not in result
        # Only 1 project in output
        assert "Proj1" in result
        assert "Proj2" not in result

    def test_highlighted_skills_multiple_bundles(self):
        """Skills from multiple bundles are ignored when highlighted_skills provided."""
        bundles = [
            _make_bundle(name="Proj1", skills=["Django"]),
            _make_bundle(name="Proj2", skills=["React"]),
        ]
        curated = ["Rust", "WebAssembly"]

        result = generate_resume(
            projects=bundles,
            format="markdown",
            include_skills=True,
            highlighted_skills=curated,
        )

        # Curated skills present
        assert "Rust" in result
        assert "WebAssembly" in result
        # Portfolio skills should NOT appear
        assert "Django" not in result
        assert "React" not in result


class TestGenerateResumeSignature:
    """Test that generate_resume() correctly accepts the highlighted_skills parameter."""

    def test_accepts_highlighted_skills_keyword(self):
        """generate_resume() should accept highlighted_skills as a keyword argument."""
        bundle = _make_bundle()
        # Should not raise TypeError
        result = generate_resume(
            projects=[bundle],
            format="markdown",
            highlighted_skills=["Python"],
        )
        assert isinstance(result, str)

    def test_default_highlighted_skills_is_none(self):
        """generate_resume() should work without highlighted_skills argument."""
        bundle = _make_bundle()
        # Should not raise TypeError
        result = generate_resume(projects=[bundle], format="markdown")
        assert isinstance(result, str)

    def test_return_type_markdown(self):
        """generate_resume() should return str for markdown format."""
        bundle = _make_bundle()
        result = generate_resume(
            projects=[bundle],
            format="markdown",
            highlighted_skills=["Skill1"],
        )
        assert isinstance(result, str)

    def test_no_projects_with_highlighted_skills(self):
        """generate_resume() should work with empty projects + highlighted_skills."""
        result = generate_resume(
            projects=[],
            format="markdown",
            include_skills=True,
            highlighted_skills=["Python", "JavaScript"],
        )
        assert isinstance(result, str)
        assert "## Skills" in result
        assert "Python" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
