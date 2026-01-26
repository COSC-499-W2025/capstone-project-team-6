#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for enhanced contribution ranking functionality.

Tests cover:
- Date helper functions (calculate_days_since, calculate_duration_days)
- Scoring categorization (categorize_score)
- Individual scoring functions (contribution, recency, scale, collaboration, duration)
- Enhanced calculate_composite_score integration
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add paths for imports
current_dir = Path(__file__).parent
tests_dir = current_dir.parent
src_dir = tests_dir.parent
backend_dir = src_dir / "backend"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from analysis.analyze import (
    calculate_collaboration_score,
    calculate_composite_score,
    calculate_contribution_score,
    calculate_days_since,
    calculate_duration_days,
    calculate_duration_score,
    calculate_recency_score,
    calculate_scale_score,
    categorize_score,
)


class TestDateHelpers:
    """Test date helper functions."""

    def test_calculate_days_since_recent(self):
        """Test calculating days since a recent date."""
        # Create a date 10 days ago
        recent_date = (datetime.now() - timedelta(days=10)).isoformat()
        days = calculate_days_since(recent_date)
        assert 9 <= days <= 11, f"Expected ~10 days, got {days}"

    def test_calculate_days_since_old(self):
        """Test calculating days since an old date."""
        old_date = "2023-01-01"
        days = calculate_days_since(old_date)
        assert days > 700, f"Expected >700 days since 2023-01-01, got {days}"

    def test_calculate_days_since_invalid(self):
        """Test handling of invalid date strings."""
        days = calculate_days_since("invalid-date")
        assert days == 999999, "Invalid dates should return 999999"

    def test_calculate_duration_days_positive(self):
        """Test calculating duration between two dates."""
        start = "2024-01-01"
        end = "2024-06-01"
        duration = calculate_duration_days(start, end)
        assert 150 <= duration <= 153, f"Expected ~152 days, got {duration}"

    def test_calculate_duration_days_same_date(self):
        """Test duration when start and end are the same."""
        date = "2024-01-01"
        duration = calculate_duration_days(date, date)
        assert duration == 0, "Same dates should have 0 duration"

    def test_calculate_duration_days_invalid(self):
        """Test handling of invalid dates."""
        duration = calculate_duration_days("invalid", "2024-01-01")
        assert duration == 0, "Invalid dates should return 0"


class TestCategorizeScore:
    """Test score categorization."""

    def test_flagship_project(self):
        """Test flagship project categorization (80+)."""
        assert categorize_score(85) == "Flagship Project"
        assert categorize_score(80) == "Flagship Project"
        assert categorize_score(100) == "Flagship Project"

    def test_major_project(self):
        """Test major project categorization (65-79)."""
        assert categorize_score(70) == "Major Project"
        assert categorize_score(65) == "Major Project"
        assert categorize_score(79) == "Major Project"

    def test_significant_project(self):
        """Test significant project categorization (50-64)."""
        assert categorize_score(55) == "Significant Project"
        assert categorize_score(50) == "Significant Project"
        assert categorize_score(64) == "Significant Project"

    def test_supporting_project(self):
        """Test supporting project categorization (35-49)."""
        assert categorize_score(40) == "Supporting Project"
        assert categorize_score(35) == "Supporting Project"
        assert categorize_score(49) == "Supporting Project"

    def test_minor_contribution(self):
        """Test minor contribution categorization (<35)."""
        assert categorize_score(25) == "Minor Contribution"
        assert categorize_score(0) == "Minor Contribution"
        assert categorize_score(34) == "Minor Contribution"


class TestContributionScore:
    """Test individual contribution scoring."""

    def test_solo_project(self):
        """Test solo project gets full credit."""
        project = {"git_analysis": {"is_collaborative": False}}
        result = calculate_contribution_score(project)
        assert result["score"] == 30.0
        assert result["level"] == "Solo Project"
        assert "100%" in result["justification"]

    def test_dominant_contributor(self):
        """Test dominant contributor (70%+) scoring."""
        project = {
            "git_analysis": {
                "is_collaborative": True,
                "contributors": [
                    {"email": "user@example.com", "percentage": 75, "commits": 150},
                    {"email": "other@example.com", "percentage": 25, "commits": 50},
                ],
            }
        }
        result = calculate_contribution_score(project, "user@example.com")
        assert result["score"] == 30.0
        assert result["level"] == "Dominant Contributor"

    def test_major_contributor(self):
        """Test major contributor (50-70%) scoring."""
        project = {
            "git_analysis": {
                "is_collaborative": True,
                "contributors": [
                    {"email": "user@example.com", "percentage": 60, "commits": 120},
                    {"email": "other@example.com", "percentage": 40, "commits": 80},
                ],
            }
        }
        result = calculate_contribution_score(project, "user@example.com")
        assert result["score"] == 25.0
        assert result["level"] == "Major Contributor"

    def test_moderate_contributor(self):
        """Test moderate contributor (30-50%) scoring."""
        project = {
            "git_analysis": {
                "is_collaborative": True,
                "contributors": [
                    {"email": "user@example.com", "percentage": 40, "commits": 80},
                    {"email": "other@example.com", "percentage": 60, "commits": 120},
                ],
            }
        }
        result = calculate_contribution_score(project, "user@example.com")
        assert result["score"] == 20.0
        assert result["level"] == "Moderate Contributor"

    def test_minor_contributor(self):
        """Test minor contributor (<15%) scoring."""
        project = {
            "git_analysis": {
                "is_collaborative": True,
                "contributors": [
                    {"email": "user@example.com", "percentage": 10, "commits": 20},
                    {"email": "other@example.com", "percentage": 90, "commits": 180},
                ],
            }
        }
        result = calculate_contribution_score(project, "user@example.com")
        assert result["score"] == 5.0
        assert result["level"] == "Minor Contributor"

    def test_unknown_contributor(self):
        """Test collaborative project with unknown contribution."""
        project = {"git_analysis": {"is_collaborative": True, "contributors": []}}
        result = calculate_contribution_score(project)
        assert result["score"] == 15.0
        assert result["level"] == "Collaborative (Unknown %)"


class TestRecencyScore:
    """Test recency scoring."""

    def test_very_recent(self):
        """Test very recent activity (last 30 days)."""
        recent_date = (datetime.now() - timedelta(days=15)).isoformat()
        project = {"git_analysis": {"last_commit_date": recent_date}}
        result = calculate_recency_score(project)
        assert result["score"] == 15.0
        assert result["period"] == "Last 30 days"

    def test_recent(self):
        """Test recent activity (last 90 days)."""
        recent_date = (datetime.now() - timedelta(days=60)).isoformat()
        project = {"git_analysis": {"last_commit_date": recent_date}}
        result = calculate_recency_score(project)
        assert result["score"] == 12.0
        assert result["period"] == "Last 90 days"

    def test_moderately_recent(self):
        """Test moderately recent activity (last 180 days)."""
        recent_date = (datetime.now() - timedelta(days=120)).isoformat()
        project = {"git_analysis": {"last_commit_date": recent_date}}
        result = calculate_recency_score(project)
        assert result["score"] == 9.0
        assert result["period"] == "Last 180 days"

    def test_last_year(self):
        """Test activity within last year."""
        recent_date = (datetime.now() - timedelta(days=300)).isoformat()
        project = {"git_analysis": {"last_commit_date": recent_date}}
        result = calculate_recency_score(project)
        assert result["score"] == 6.0
        assert result["period"] == "Last year"

    def test_old_project(self):
        """Test old project (>1 year)."""
        project = {"git_analysis": {"last_commit_date": "2022-01-01"}}
        result = calculate_recency_score(project)
        assert result["score"] == 3.0
        assert "year(s) ago" in result["period"]

    def test_no_date_fallback(self):
        """Test fallback to last_modified_date."""
        recent_date = (datetime.now() - timedelta(days=15)).isoformat()
        project = {"last_modified_date": recent_date}
        result = calculate_recency_score(project)
        assert result["score"] == 15.0


class TestScaleScore:
    """Test project scale scoring."""

    def test_large_project(self):
        """Test large project (500+ commits or 100+ files)."""
        project = {"total_commits": 600, "total_files": 120}
        result = calculate_scale_score(project)
        assert result["score"] == 10.0
        assert result["scale"] == "Large"

    def test_medium_large_project(self):
        """Test medium-large project (100+ commits or 50+ files)."""
        project = {"total_commits": 150, "total_files": 60}
        result = calculate_scale_score(project)
        assert result["score"] == 7.0
        assert result["scale"] == "Medium-Large"

    def test_medium_project(self):
        """Test medium project (50+ commits or 20+ files)."""
        project = {"total_commits": 75, "total_files": 30}
        result = calculate_scale_score(project)
        assert result["score"] == 5.0
        assert result["scale"] == "Medium"

    def test_small_project(self):
        """Test small project."""
        project = {"total_commits": 20, "total_files": 10}
        result = calculate_scale_score(project)
        assert result["score"] == 3.0
        assert result["scale"] == "Small"


class TestCollaborationScore:
    """Test collaboration diversity scoring."""

    def test_large_team(self):
        """Test large team (5+ contributors)."""
        project = {"git_analysis": {"total_contributors": 7}}
        result = calculate_collaboration_score(project)
        assert result["score"] == 10.0
        assert result["level"] == "Large Team"

    def test_small_team(self):
        """Test small team (3-4 contributors)."""
        project = {"git_analysis": {"total_contributors": 3}}
        result = calculate_collaboration_score(project)
        assert result["score"] == 7.0
        assert result["level"] == "Small Team"

    def test_pair(self):
        """Test pair programming (2 contributors)."""
        project = {"git_analysis": {"total_contributors": 2}}
        result = calculate_collaboration_score(project)
        assert result["score"] == 4.0
        assert result["level"] == "Pair"

    def test_solo(self):
        """Test solo project (1 contributor)."""
        project = {"git_analysis": {"total_contributors": 1}}
        result = calculate_collaboration_score(project)
        assert result["score"] == 0.0
        assert result["level"] == "Solo"


class TestDurationScore:
    """Test activity duration scoring."""

    def test_long_term(self):
        """Test long-term project (180+ days)."""
        project = {
            "git_analysis": {
                "contributors": [
                    {
                        "email": "user@example.com",
                        "commits": 200,
                        "first_commit_date": "2024-01-01",
                        "last_commit_date": "2024-12-01",
                    }
                ]
            }
        }
        result = calculate_duration_score(project, "user@example.com")
        assert result["score"] == 10.0
        assert result["period"] == "Long-term"

    def test_extended(self):
        """Test extended project (90-180 days)."""
        project = {
            "git_analysis": {
                "contributors": [
                    {
                        "email": "user@example.com",
                        "commits": 100,
                        "first_commit_date": "2024-06-01",
                        "last_commit_date": "2024-09-01",
                    }
                ]
            }
        }
        result = calculate_duration_score(project, "user@example.com")
        assert result["score"] == 8.0
        assert result["period"] == "Extended"

    def test_moderate(self):
        """Test moderate duration (30-90 days)."""
        project = {
            "git_analysis": {
                "contributors": [
                    {
                        "email": "user@example.com",
                        "commits": 50,
                        "first_commit_date": "2024-10-01",
                        "last_commit_date": "2024-11-15",
                    }
                ]
            }
        }
        result = calculate_duration_score(project, "user@example.com")
        assert result["score"] == 6.0
        assert result["period"] == "Moderate"

    def test_sprint(self):
        """Test sprint/hackathon (<7 days)."""
        project = {
            "git_analysis": {
                "contributors": [
                    {
                        "email": "user@example.com",
                        "commits": 30,
                        "first_commit_date": "2024-11-01",
                        "last_commit_date": "2024-11-03",
                    }
                ]
            }
        }
        result = calculate_duration_score(project, "user@example.com")
        assert result["score"] == 2.0
        assert result["period"] == "Sprint/Hackathon"


class TestEnhancedCompositeScore:
    """Test enhanced composite scoring integration."""

    def test_enhanced_mode_returns_all_fields(self):
        """Test that enhanced mode returns all expected fields."""
        project = {
            "total_files": 50,
            "code_files": 30,
            "test_files": 10,
            "doc_files": 5,
            "config_files": 3,
            "total_commits": 100,
            "directory_depth": 3,
            "has_readme": True,
            "has_ci_cd": True,
            "has_docker": False,
            "is_git_repo": True,
            "has_tests": True,
            "test_coverage_estimate": "medium",
            "git_analysis": {
                "is_collaborative": False,
                "total_contributors": 1,
                "last_commit_date": (datetime.now() - timedelta(days=30)).isoformat(),
            },
        }

        result = calculate_composite_score(project, use_enhanced_ranking=True)

        # Check all required fields are present
        assert "composite_score" in result
        assert "base_score" in result
        assert "breakdown" in result
        assert "justification" in result
        assert "category" in result
        assert "weights" in result

        # Check breakdown has all 9 factors
        breakdown = result["breakdown"]
        assert "code_architecture" in breakdown
        assert "code_quality" in breakdown
        assert "project_maturity" in breakdown
        assert "algorithmic_quality" in breakdown
        assert "individual_contribution" in breakdown
        assert "recency" in breakdown
        assert "project_scale" in breakdown
        assert "collaboration_diversity" in breakdown
        assert "activity_duration" in breakdown

    def test_legacy_mode(self):
        """Test that legacy mode works without enhanced features."""
        project = {
            "total_files": 50,
            "code_files": 30,
            "test_files": 10,
            "doc_files": 5,
            "config_files": 3,
            "total_commits": 100,
            "directory_depth": 3,
            "has_readme": True,
            "has_ci_cd": True,
            "is_git_repo": True,
            "has_tests": True,
            "test_coverage_estimate": "medium",
        }

        result = calculate_composite_score(project, use_enhanced_ranking=False)

        # Should have basic fields only
        assert "composite_score" in result
        assert "breakdown" in result
        assert "justification" in result
        assert "category" not in result  # No category in legacy mode
        assert "base_score" not in result  # No separate base score

        # Breakdown should only have 4 base factors
        breakdown = result["breakdown"]
        assert len(breakdown) == 4
        assert "individual_contribution" not in breakdown

    def test_score_calculation_with_user_email(self):
        """Test that user_email affects contribution scoring."""
        project = {
            "total_files": 50,
            "code_files": 30,
            "test_files": 10,
            "total_commits": 100,
            "git_analysis": {
                "is_collaborative": True,
                "total_contributors": 3,
                "contributors": [
                    {"email": "alice@example.com", "percentage": 60, "commits": 60},
                    {"email": "bob@example.com", "percentage": 30, "commits": 30},
                    {"email": "charlie@example.com", "percentage": 10, "commits": 10},
                ],
                "last_commit_date": (datetime.now() - timedelta(days=15)).isoformat(),
            },
        }

        # Score without user_email (should use top contributor)
        result1 = calculate_composite_score(project)

        # Score with specific user_email
        result2 = calculate_composite_score(project, user_email="bob@example.com")

        # Scores should be different because contribution percentages differ
        assert result1["composite_score"] != result2["composite_score"]
        assert (
            result1["breakdown"]["individual_contribution"]
            > result2["breakdown"]["individual_contribution"]
        )

    def test_weighted_calculation(self):
        """Test that weights are applied correctly."""
        project = {
            "total_files": 50,
            "code_files": 30,
            "test_files": 10,
            "total_commits": 100,
            "git_analysis": {
                "is_collaborative": False,
                "total_contributors": 1,
                "last_commit_date": (datetime.now() - timedelta(days=15)).isoformat(),
            },
        }

        result = calculate_composite_score(project)

        # Manual calculation check (approximate)
        base = result["base_score"]
        breakdown = result["breakdown"]
        weights = result["weights"]

        expected = (
            base * weights["base_score"]
            + breakdown["individual_contribution"] * weights["contribution"]
            + breakdown["recency"] * weights["recency"]
            + breakdown["project_scale"] * weights["scale"]
            + breakdown["collaboration_diversity"] * weights["collaboration"]
            + breakdown["activity_duration"] * weights["duration"]
        )

        # Allow small floating point differences
        assert abs(result["composite_score"] - expected) < 0.01


# Pytest will automatically discover and run all test classes and methods
