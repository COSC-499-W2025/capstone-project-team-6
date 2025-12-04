"""
Comprehensive test suite for git_analysis.py module

This test suite creates temporary Git repositories, runs analyses,
verifies results, and cleans up automatically.

Test Categories:
1. Basic Git Repository Detection (4 tests)
2. Solo Project Analysis (5 tests)
3. Collaborative Project Analysis (6 tests)
4. Target User Detection (5 tests)
5. Branch and Remote Information (4 tests)
6. Edge Cases and Error Handling (5 tests)
7. Export Functionality (3 tests)

Total: 34 tests

Requirements:
- pytest
- Git command-line tool installed
- git_analysis.py in the same directory or importable

Run with: pytest test_git_analysis.py -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Import the module to test
# Adjust import based on your project structure
# Structure: src/backend/analysis/git_analysis.py
#           src/tests/backend_test/test_git_analysis.py

try:
    # Try direct import first (if running from project root)
    from backend.analysis.git_analysis import (
        ContributorStats,
        GitAnalysisExporter,
        GitAnalysisResult,
        GitAnalyzer,
        analyze_project,
    )
except ImportError:
    # Add src directory to path and try again
    # Get the project root (go up from tests/backend_test to src, then to project root)
    test_dir = Path(__file__).parent  # tests/backend_test
    tests_dir = test_dir.parent  # tests
    src_dir = tests_dir.parent  # project root (contains src/)

    sys.path.insert(0, str(src_dir))

    try:
        from src.backend.analysis.git_analysis import (
            ContributorStats,
            GitAnalysisExporter,
            GitAnalysisResult,
            GitAnalyzer,
            analyze_project,
        )
    except ImportError as e:
        print(f"Error importing git_analysis module: {e}")
        print(f"Test directory: {test_dir}")
        print(f"Looking for module at: {src_dir / 'src' / 'backend' / 'analysis' / 'git_analysis.py'}")
        print("\nExpected project structure:")
        print("project_root/")
        print("├── src/")
        print("│   ├── backend/")
        print("│   │   └── analysis/")
        print("│   │       └── git_analysis.py")
        print("│   └── tests/")
        print("│       └── backend_test/")
        print("│           └── test_git_analysis.py")
        raise


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def run_git_command(repo_path, *args):
    """
    Helper to run Git commands in a repository.

    Args:
        repo_path: Path to the repository
        *args: Git command arguments

    Returns:
        Command output or None if failed
    """
    try:
        result = subprocess.run(["git"] + list(args), cwd=repo_path, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"Git command failed: {e}")
        return None


def init_git_repo(repo_path):
    """
    Initialize a Git repository and set basic config.

    Args:
        repo_path: Path where to initialize the repo
    """
    run_git_command(repo_path, "init")
    run_git_command(repo_path, "config", "user.name", "Test User")
    run_git_command(repo_path, "config", "user.email", "test@example.com")


def create_commit(repo_path, author_name, author_email, message, filename=None):
    """
    Create a commit with specified author.

    Args:
        repo_path: Path to the repository
        author_name: Author's name
        author_email: Author's email
        message: Commit message
        filename: Optional filename to create (auto-generated if None)

    Returns:
        Commit hash or None if failed
    """
    # Create a file to commit
    if filename is None:
        # Generate unique filename based on timestamp
        filename = f"file_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.txt"

    file_path = Path(repo_path) / filename
    file_path.write_text(f"Content for {message}\n")

    # Add and commit
    run_git_command(repo_path, "add", filename)

    # Set author environment variables for this commit
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_AUTHOR_EMAIL"] = author_email
    env["GIT_COMMITTER_NAME"] = author_name
    env["GIT_COMMITTER_EMAIL"] = author_email

    try:
        result = subprocess.run(
            ["git", "commit", "-m", message], cwd=repo_path, capture_output=True, text=True, env=env, timeout=10
        )
        if result.returncode == 0:
            # Get the commit hash
            return run_git_command(repo_path, "rev-parse", "HEAD")
        return None
    except Exception as e:
        print(f"Commit failed: {e}")
        return None


def setup_git_remote(repo_path, remote_name, remote_url):
    """
    Add a remote to the repository.

    Args:
        repo_path: Path to the repository
        remote_name: Name of the remote (e.g., 'origin')
        remote_url: URL of the remote
    """
    run_git_command(repo_path, "remote", "add", remote_name, remote_url)


def create_branch(repo_path, branch_name):
    """
    Create a new branch in the repository.

    Args:
        repo_path: Path to the repository
        branch_name: Name of the branch to create
    """
    run_git_command(repo_path, "branch", branch_name)


# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory that gets cleaned up after the test.
    """
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_git_repo(temp_dir):
    """
    Create an empty Git repository in a temporary directory.
    """
    repo_path = temp_dir / "test_repo"
    repo_path.mkdir()
    init_git_repo(repo_path)
    yield repo_path


@pytest.fixture
def solo_project_repo(temp_dir):
    """
    Create a solo project repository with one author and 5 commits.
    """
    repo_path = temp_dir / "solo_project"
    repo_path.mkdir()
    init_git_repo(repo_path)

    # Create 5 commits by Alice
    author_name = "Alice Developer"
    author_email = "alice@example.com"

    for i in range(5):
        create_commit(repo_path, author_name, author_email, f"Commit {i+1} by Alice", f"file{i+1}.txt")

    yield repo_path


@pytest.fixture
def collab_project_repo(temp_dir):
    """
    Create a collaborative project with 3 authors:
    - Alice: 10 commits (50%)
    - Bob: 6 commits (30%)
    - Charlie: 4 commits (20%)
    """
    repo_path = temp_dir / "collab_project"
    repo_path.mkdir()
    init_git_repo(repo_path)

    authors = [
        ("Alice Developer", "alice@example.com", 10),
        ("Bob Contributor", "bob@example.com", 6),
        ("Charlie Coder", "charlie@example.com", 4),
    ]

    commit_num = 1
    for name, email, count in authors:
        for i in range(count):
            create_commit(repo_path, name, email, f"Commit {commit_num} by {name.split()[0]}", f"file{commit_num}.txt")
            commit_num += 1

    yield repo_path


@pytest.fixture
def multi_branch_repo(temp_dir):
    """
    Create a repository with multiple branches.
    """
    repo_path = temp_dir / "multi_branch"
    repo_path.mkdir()
    init_git_repo(repo_path)

    # Create initial commit on main/master
    create_commit(repo_path, "Alice Developer", "alice@example.com", "Initial commit", "README.md")

    # Create additional branches
    create_branch(repo_path, "feature/test")
    create_branch(repo_path, "bugfix/issue-123")

    yield repo_path


@pytest.fixture
def remote_repo(temp_dir):
    """
    Create a repository with a remote URL configured.
    """
    repo_path = temp_dir / "remote_project"
    repo_path.mkdir()
    init_git_repo(repo_path)

    # Create initial commit
    create_commit(repo_path, "Alice Developer", "alice@example.com", "Initial commit", "README.md")

    # Add remote
    setup_git_remote(repo_path, "origin", "https://github.com/user/repo.git")

    yield repo_path


@pytest.fixture
def temp_output_dir(temp_dir):
    """
    Create a temporary output directory for JSON exports.
    """
    output_path = temp_dir / "analysis_results"
    output_path.mkdir()
    yield output_path


# =============================================================================
# CATEGORY 1: BASIC GIT REPOSITORY DETECTION (4 tests)
# =============================================================================


def test_detect_valid_git_repo(temp_git_repo):
    """Test that a valid Git repository is detected."""
    analyzer = GitAnalyzer(temp_git_repo)

    assert analyzer.check_git_repo() == True
    assert analyzer.git_dir.exists()
    assert analyzer.git_dir.is_dir()


def test_detect_no_git_repo(temp_dir):
    """Test that a directory without .git is handled correctly."""
    non_git_dir = temp_dir / "not_a_repo"
    non_git_dir.mkdir()

    analyzer = GitAnalyzer(non_git_dir)
    result = analyzer.analyze()

    assert result.is_git_repo == False
    assert result.error_message == "No .git directory found"
    assert result.total_commits == 0
    assert result.total_contributors == 0


def test_git_command_available(temp_git_repo):
    """Test that Git command-line tool is available."""
    analyzer = GitAnalyzer(temp_git_repo)

    assert analyzer.check_git_available() == True


def test_empty_directory(temp_dir):
    """Test analysis on a completely empty directory."""
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()

    analyzer = GitAnalyzer(empty_dir)
    result = analyzer.analyze()

    assert result.is_git_repo == False
    assert result.error_message is not None


# =============================================================================
# CATEGORY 2: SOLO PROJECT ANALYSIS (5 tests)
# =============================================================================


def test_solo_project_single_commit(temp_git_repo):
    """Test analysis of solo project with a single commit."""
    # Create one commit
    create_commit(temp_git_repo, "Alice Developer", "alice@example.com", "Initial commit", "README.md")

    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    assert result.is_git_repo == True
    assert result.total_commits == 1
    assert result.total_contributors == 1
    assert result.is_solo_project == True
    assert result.is_collaborative == False


def test_solo_project_multiple_commits(solo_project_repo):
    """Test analysis of solo project with multiple commits."""
    analyzer = GitAnalyzer(solo_project_repo)
    result = analyzer.analyze()

    assert result.is_git_repo == True
    assert result.total_commits == 5
    assert result.total_contributors == 1
    assert result.is_solo_project == True
    assert result.is_collaborative == False
    assert len(result.contributors) == 1


def test_solo_project_classification(solo_project_repo):
    """Verify solo project is correctly classified."""
    analyzer = GitAnalyzer(solo_project_repo)
    result = analyzer.analyze()

    assert result.is_solo_project == True
    assert result.is_collaborative == False
    assert result.total_contributors == 1


def test_solo_project_percentage(solo_project_repo):
    """Check that solo contributor gets 100% attribution."""
    analyzer = GitAnalyzer(solo_project_repo)
    result = analyzer.analyze()

    assert len(result.contributors) == 1
    assert result.contributors[0].percentage == 100.0
    assert result.contributors[0].commit_count == 5


def test_solo_project_commit_dates(solo_project_repo):
    """Verify first and last commit dates are captured."""
    analyzer = GitAnalyzer(solo_project_repo)
    result = analyzer.analyze()

    contributor = result.contributors[0]
    assert contributor.first_commit_date is not None
    assert contributor.last_commit_date is not None
    # Dates should be in ISO format
    assert "T" in contributor.first_commit_date
    assert "T" in contributor.last_commit_date


# =============================================================================
# CATEGORY 3: COLLABORATIVE PROJECT ANALYSIS (6 tests)
# =============================================================================


def test_two_contributors(temp_git_repo):
    """Test analysis with two contributors."""
    # Alice: 3 commits
    for i in range(3):
        create_commit(temp_git_repo, "Alice Developer", "alice@example.com", f"Alice commit {i+1}", f"alice_file{i+1}.txt")

    # Bob: 2 commits
    for i in range(2):
        create_commit(temp_git_repo, "Bob Contributor", "bob@example.com", f"Bob commit {i+1}", f"bob_file{i+1}.txt")

    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    assert result.total_contributors == 2
    assert result.total_commits == 5
    assert result.is_solo_project == False
    assert result.is_collaborative == True


def test_three_contributors(collab_project_repo):
    """Test analysis with three contributors."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze()

    assert result.total_contributors == 3
    assert result.total_commits == 20
    assert result.is_collaborative == True
    assert result.is_solo_project == False
    assert len(result.contributors) == 3


def test_collaborative_classification(collab_project_repo):
    """Verify collaborative project is correctly classified."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze()

    assert result.is_collaborative == True
    assert result.is_solo_project == False
    assert result.total_contributors > 1


def test_percentage_calculation(collab_project_repo):
    """Check that percentages add up to 100%."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze()

    total_percentage = sum(c.percentage for c in result.contributors)
    # Allow for small floating point errors
    assert abs(total_percentage - 100.0) < 0.1


def test_contributor_sorting(collab_project_repo):
    """Verify contributors are sorted by commit count (descending)."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze()

    # Alice should be first (10 commits)
    assert result.contributors[0].name == "Alice Developer"
    assert result.contributors[0].commit_count == 10

    # Bob should be second (6 commits)
    assert result.contributors[1].name == "Bob Contributor"
    assert result.contributors[1].commit_count == 6

    # Charlie should be third (4 commits)
    assert result.contributors[2].name == "Charlie Coder"
    assert result.contributors[2].commit_count == 4


def test_unequal_contributions(temp_git_repo):
    """Test 80/20 contribution split scenario."""
    # Alice: 8 commits (80%)
    for i in range(8):
        create_commit(temp_git_repo, "Alice Developer", "alice@example.com", f"Alice commit {i+1}", f"file{i+1}.txt")

    # Bob: 2 commits (20%)
    for i in range(2):
        create_commit(temp_git_repo, "Bob Contributor", "bob@example.com", f"Bob commit {i+1}", f"bob_file{i+1}.txt")

    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    assert result.contributors[0].percentage == 80.0
    assert result.contributors[1].percentage == 20.0


# =============================================================================
# CATEGORY 4: TARGET USER DETECTION (5 tests)
# =============================================================================


def test_target_user_exact_match(collab_project_repo):
    """Test that target user is found with exact email match."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze(target_user_email="alice@example.com")

    assert result.target_user_stats is not None
    assert result.target_user_stats.email == "alice@example.com"
    assert result.target_user_stats.name == "Alice Developer"
    assert result.target_user_stats.commit_count == 10


def test_target_user_case_insensitive(collab_project_repo):
    """Test that email matching is case-insensitive."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze(target_user_email="ALICE@EXAMPLE.COM")

    assert result.target_user_stats is not None
    assert result.target_user_stats.email == "alice@example.com"


def test_target_user_partial_match(collab_project_repo):
    """Test partial email matching."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze(target_user_email="charlie")

    assert result.target_user_stats is not None
    assert "charlie" in result.target_user_stats.email.lower()


def test_target_user_not_found(collab_project_repo):
    """Test when target user is not in contributors."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze(target_user_email="nonexistent@example.com")

    assert result.target_user_stats is None


def test_target_user_stats_populated(collab_project_repo):
    """Verify target user stats are correctly populated."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze(target_user_email="bob@example.com")

    assert result.target_user_stats is not None
    assert result.target_user_stats.name == "Bob Contributor"
    assert result.target_user_stats.commit_count == 6
    assert result.target_user_stats.percentage == 30.0
    assert result.target_user_stats.first_commit_date is not None
    assert result.target_user_stats.last_commit_date is not None


# =============================================================================
# CATEGORY 5: BRANCH AND REMOTE INFORMATION (4 tests)
# =============================================================================


def test_single_branch_main(temp_git_repo):
    """Test repository with only 'main' branch."""
    # Create commit to establish branch
    create_commit(temp_git_repo, "Alice Developer", "alice@example.com", "Initial commit", "README.md")

    # Rename to main if it's master
    run_git_command(temp_git_repo, "branch", "-M", "main")

    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    assert result.primary_branch in ["main", "master"]
    assert result.total_branches >= 1


def test_single_branch_master(temp_git_repo):
    """Test repository with only 'master' branch."""
    # Create commit to establish branch
    create_commit(temp_git_repo, "Alice Developer", "alice@example.com", "Initial commit", "README.md")

    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    assert result.primary_branch in ["main", "master"]


def test_multiple_branches(multi_branch_repo):
    """Test repository with multiple branches."""
    analyzer = GitAnalyzer(multi_branch_repo)
    result = analyzer.analyze()

    assert result.total_branches >= 3
    assert result.primary_branch in ["main", "master"]


def test_remote_url_detection(remote_repo):
    """Test that remote URLs are correctly detected."""
    analyzer = GitAnalyzer(remote_repo)
    result = analyzer.analyze()

    assert result.has_remote == True
    assert len(result.remote_urls) > 0
    assert "github.com/user/repo.git" in result.remote_urls[0]


# =============================================================================
# CATEGORY 6: EDGE CASES AND ERROR HANDLING (5 tests)
# =============================================================================


def test_zero_commits(temp_git_repo):
    """Test Git repository with no commits."""
    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    assert result.is_git_repo == True
    assert result.total_commits == 0
    assert result.total_contributors == 0
    assert len(result.contributors) == 0


def test_invalid_path():
    """Test analysis on non-existent directory."""
    invalid_path = Path("/definitely/does/not/exist/path")

    analyzer = GitAnalyzer(invalid_path)
    result = analyzer.analyze()

    assert result.is_git_repo == False
    assert result.error_message is not None


def test_corrupted_git_repo(temp_dir):
    """Test repository where .git exists but is not a valid directory."""
    repo_path = temp_dir / "corrupted"
    repo_path.mkdir()

    # Create .git as a file instead of directory
    git_path = repo_path / ".git"
    git_path.write_text("Not a directory")

    analyzer = GitAnalyzer(repo_path)
    result = analyzer.analyze()

    assert result.is_git_repo == False


def test_special_characters_in_name(temp_git_repo):
    """Test contributor with special characters in name."""
    create_commit(temp_git_repo, "José García-Müller", "jose@example.com", "Commit with special chars", "file1.txt")

    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    assert result.total_contributors == 1
    assert result.contributors[0].name == "José García-Müller"


def test_multiple_emails_same_author(temp_git_repo):
    """Test author with multiple email addresses (treated as different contributors)."""
    # Same person, different emails
    create_commit(temp_git_repo, "Alice Developer", "alice@work.com", "Commit from work", "file1.txt")

    create_commit(temp_git_repo, "Alice Developer", "alice@personal.com", "Commit from home", "file2.txt")

    analyzer = GitAnalyzer(temp_git_repo)
    result = analyzer.analyze()

    # Git treats different emails as different contributors
    assert result.total_contributors == 2


# =============================================================================
# CATEGORY 7: EXPORT FUNCTIONALITY (3 tests)
# =============================================================================


def test_json_export_creates_file(solo_project_repo, temp_output_dir):
    """Test that JSON export creates a file."""
    analyzer = GitAnalyzer(solo_project_repo)
    result = analyzer.analyze()

    exporter = GitAnalysisExporter(temp_output_dir)
    output_path = exporter.export_to_json(result, filename="test_export.json")

    assert output_path.exists()
    assert output_path.suffix == ".json"


def test_json_export_valid_format(solo_project_repo, temp_output_dir):
    """Test that exported JSON is valid and parseable."""
    analyzer = GitAnalyzer(solo_project_repo)
    result = analyzer.analyze()

    exporter = GitAnalysisExporter(temp_output_dir)
    output_path = exporter.export_to_json(result, filename="test_valid.json")

    # Read and parse JSON
    with open(output_path, "r") as f:
        data = json.load(f)

    # Verify it's a dictionary
    assert isinstance(data, dict)
    # Verify it has expected keys
    assert "project_path" in data
    assert "total_commits" in data
    assert "contributors" in data


def test_json_export_complete_data(collab_project_repo, temp_output_dir):
    """Test that all fields are present in exported JSON."""
    analyzer = GitAnalyzer(collab_project_repo)
    result = analyzer.analyze(target_user_email="alice@example.com")

    exporter = GitAnalysisExporter(temp_output_dir)
    output_path = exporter.export_to_json(result, filename="test_complete.json")

    with open(output_path, "r") as f:
        data = json.load(f)

    # Check all major fields are present
    required_fields = [
        "project_path",
        "analysis_timestamp",
        "is_git_repo",
        "git_available",
        "total_commits",
        "total_contributors",
        "is_solo_project",
        "is_collaborative",
        "contributors",
        "target_user_email",
        "target_user_stats",
        "primary_branch",
        "total_branches",
        "has_remote",
        "remote_urls",
        "error_message",
        "api_data",
    ]

    for field in required_fields:
        assert field in data, f"Field '{field}' missing from JSON export"

    # Verify contributors is a list
    assert isinstance(data["contributors"], list)
    assert len(data["contributors"]) == 3

    # Verify target user stats is populated
    assert data["target_user_stats"] is not None
    assert data["target_user_stats"]["email"] == "alice@example.com"


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


def test_analyze_project_convenience_function(solo_project_repo, temp_output_dir):
    """Test the analyze_project convenience function."""
    result = analyze_project(
        solo_project_repo,
        target_user_email="alice@example.com",
        use_remote_api=False,
        export_to_file=True,
        output_dir=str(temp_output_dir),
    )

    assert result.is_git_repo == True
    assert result.total_commits == 5
    assert result.total_contributors == 1
    assert result.target_user_stats is not None

    # Check that JSON file was created
    json_files = list(temp_output_dir.glob("*.json"))
    assert len(json_files) > 0


# =============================================================================
# TEST SUMMARY
# =============================================================================


def test_summary_check():
    """
    Meta-test to ensure we have the expected number of tests.
    This test always passes but prints a summary.
    """
    print("\n" + "=" * 70)
    print("Git Analysis Test Suite Summary")
    print("=" * 70)
    print("Category 1: Basic Git Repository Detection - 4 tests")
    print("Category 2: Solo Project Analysis - 5 tests")
    print("Category 3: Collaborative Project Analysis - 6 tests")
    print("Category 4: Target User Detection - 5 tests")
    print("Category 5: Branch and Remote Information - 4 tests")
    print("Category 6: Edge Cases and Error Handling - 5 tests")
    print("Category 7: Export Functionality - 3 tests")
    print("Convenience Function Tests - 1 test")
    print("=" * 70)
    print("Total: 33 tests")
    print("=" * 70)
    assert True


if __name__ == "__main__":
    """
    Run tests directly with: python test_git_analysis.py
    Or use pytest: pytest test_git_analysis.py -v
    """
    pytest.main([__file__, "-v"])
