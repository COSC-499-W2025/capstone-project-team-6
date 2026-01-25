"""Tests for contribution-aware scoring in analyze.calculate_composite_score."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent.parent
for p in (SRC_DIR, SRC_DIR.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.backend.analysis.analyze import calculate_composite_score  # noqa: E402


def test_user_contribution_boost_applied():
    now_iso = datetime.now().isoformat()
    project = {
        "target_user_email": "alice@example.com",
        "target_user_stats": {
            "email": "alice@example.com",
            "percentage": 50.0,
            "last_commit_date": now_iso,
        },
        "contribution_volume": {"alice@example.com": 50, "bob@example.com": 50},
        "blame_summary": {"alice@example.com": 60, "bob@example.com": 40},
    }

    result = calculate_composite_score(project)

    assert result["user_contribution_score"] > 0
    assert result["adjusted_score"] > result["composite_score"]
    assert result["user_contribution_score"] == pytest.approx(12.0, rel=1e-2)
    assert "target_user" in result["justification"]


def test_no_target_user_has_no_boost():
    result = calculate_composite_score({})
    assert result["user_contribution_score"] == 0
    assert result["adjusted_score"] == result["composite_score"]
