import subprocess
import tempfile
from pathlib import Path

import pytest

from src.backend.analysis.git_analysis import GitAnalyzer


def _init_repo_with_commits(tmpdir: Path):
    try:
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        if "Operation not permitted" in (e.stderr or ""):
            pytest.skip("git init not permitted in this environment")
        raise
    subprocess.run(["git", "config", "user.email", "alice@example.com"], cwd=tmpdir, check=True)
    subprocess.run(["git", "config", "user.name", "Alice"], cwd=tmpdir, check=True)

    # code commit
    (tmpdir / "src").mkdir(parents=True, exist_ok=True)
    (tmpdir / "src" / "app.py").write_text("print('code')\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
    subprocess.run(["git", "commit", "-m", "code commit"], cwd=tmpdir, check=True)

    # test commit
    (tmpdir / "tests").mkdir(parents=True, exist_ok=True)
    (tmpdir / "tests" / "test_app.py").write_text("def test_x():\n    assert True\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
    subprocess.run(["git", "commit", "-m", "test commit"], cwd=tmpdir, check=True)

    # docs commit
    (tmpdir / "docs").mkdir(parents=True, exist_ok=True)
    (tmpdir / "docs" / "README.md").write_text("# Docs\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
    subprocess.run(["git", "commit", "-m", "docs commit"], cwd=tmpdir, check=True)

    # design commit
    (tmpdir / "design").mkdir(parents=True, exist_ok=True)
    (tmpdir / "design" / "wireframe.drawio").write_text("<xml />\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
    subprocess.run(["git", "commit", "-m", "design commit"], cwd=tmpdir, check=True)


def test_activity_breakdown_classification():
    # Create repo inside workspace to avoid sandbox permission issues
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
        repo_path = Path(tmp)
        _init_repo_with_commits(repo_path)

        result = GitAnalyzer(repo_path).analyze()

        # Ensure activity breakdown exists and sums are positive
        activity = result.activity_breakdown.get("alice@example.com")
        assert activity is not None
        # code commit adds lines from app.py (2 lines changed: add)
        assert activity["code"] >= 2
        # test commit
        assert activity["test"] >= 2
        # docs commit
        assert activity["docs"] >= 1
        # design commit (drawio)
        assert activity["design"] >= 1

        # total contribution volume should be at least sum of activities
        total = result.contribution_volume.get("alice@example.com", 0)
        assert total >= sum(activity.values())

