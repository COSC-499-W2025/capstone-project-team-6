#!/usr/bin/env python3
"""
Test configuration and runner for role prediction tests.

This script provides easy ways to run the comprehensive role prediction tests.
"""

import sys
from pathlib import Path

import pytest

# Add source directory to path
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))


def run_role_prediction_tests():
    """Run all role prediction tests with detailed output."""
    test_files = ["src/tests/backend_test/test_role_predictor.py", "src/tests/backend_test/test_role_prediction_integration.py"]

    print("🧪 Running comprehensive role prediction tests...")
    print("=" * 60)

    # Run tests with verbose output
    exit_code = pytest.main(
        [
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "-x",  # Stop on first failure
            "--color=yes",  # Colored output
            *test_files,
        ]
    )

    if exit_code == 0:
        print("\n✅ All role prediction tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")

    return exit_code


def run_specific_test_category(category):
    """Run specific category of tests."""
    categories = {
        "basic": "TestRolePredictorBasics",
        "scenarios": "TestRolePredictionScenarios",
        "indicators": "TestRoleIndicators",
        "edge_cases": "TestEdgeCases",
        "formatting": "TestFormatting",
        "integration": "TestIntegration",
        "performance": "TestPerformance",
        "cli": "TestRolePredictionCLIIntegration",
        "database": "TestRolePredictionDatabaseIntegration",
        "e2e": "TestEndToEndRolePrediction",
    }

    if category not in categories:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return 1

    class_name = categories[category]
    test_pattern = f"*{class_name}*"

    print(f"🧪 Running {category} tests...")
    print("=" * 40)

    exit_code = pytest.main(
        [
            "-v",
            "-k",
            class_name,
            "src/tests/backend_test/test_role_predictor.py",
            "src/tests/backend_test/test_role_prediction_integration.py",
        ]
    )

    return exit_code


def run_quick_smoke_test():
    """Run a quick smoke test to verify basic functionality."""
    print("🚀 Running quick smoke test...")
    print("=" * 30)

    try:
        # Import and test basic functionality
        from backend.analysis.role_predictor import DeveloperRole, get_available_roles, predict_developer_role

        # Test 1: Basic imports work
        roles = get_available_roles()
        assert len(roles) == 12
        print("✅ Basic imports and role enumeration work")

        # Test 2: Simple prediction works
        test_data = {
            "project_name": "Smoke Test",
            "languages": {"python": 10},
            "frameworks": ["Django"],
            "score_data": {"composite_score": 60},
        }

        prediction = predict_developer_role(test_data)
        assert prediction.predicted_role in roles
        assert 0.0 <= prediction.confidence_score <= 1.0
        print("✅ Basic role prediction works")

        # Test 3: Database integration imports
        from backend.analysis_database import init_db, record_analysis

        print("✅ Database integration imports work")

        # Test 4: CLI integration imports
        from backend.cli import analyze_folder, display_analysis

        print("✅ CLI integration imports work")

        print("\n🎉 Smoke test passed! All basic functionality works.")
        return 0

    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run role prediction tests")
    parser.add_argument(
        "--category",
        choices=[
            "basic",
            "scenarios",
            "indicators",
            "edge_cases",
            "formatting",
            "integration",
            "performance",
            "cli",
            "database",
            "e2e",
        ],
        help="Run specific category of tests",
    )
    parser.add_argument("--smoke", action="store_true", help="Run quick smoke test only")
    parser.add_argument("--all", action="store_true", help="Run all comprehensive tests (default)")

    args = parser.parse_args()

    if args.smoke:
        exit_code = run_quick_smoke_test()
    elif args.category:
        exit_code = run_specific_test_category(args.category)
    else:
        exit_code = run_role_prediction_tests()

    sys.exit(exit_code)
