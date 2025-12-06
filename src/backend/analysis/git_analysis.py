"""
Analyzes Git repositories to determine authorship and collaboration patterns.

This module provides functionality to:
1. Detect Git repositories from traversal results
2. Execute local Git commands to extract contribution data
3. Calculate contribution metrics and statistics
4. Export results to JSON format
"""

import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union


@dataclass
class ContributorStats:
    """
    Statistics for a single contributor in a Git repository.

    Attributes:
        name: Contributor's name from Git config
        email: Contributor's email address
        commit_count: Total number of commits by  contributor
        percentage: Percentage of total commits (0-100)
        first_commit_date: Date of first commit by  contributor
        last_commit_date: Date of last commit by contributor
    """

    name: str
    email: str
    commit_count: int
    percentage: float
    first_commit_date: Optional[str] = None
    last_commit_date: Optional[str] = None


@dataclass
class GitAnalysisResult:
    """
    Complete analysis result for a Git repository.
    This comment description was generated based on the parameters and method below

    Attributes:
        project_path: Absolute path to the project directory
        analysis_timestamp: When this analysis was performed
        is_git_repo: Whether a valid .git directory was found
        git_available: Whether Git command-line tool is available
        total_commits: Total number of commits in the repository
        total_contributors: Number of unique contributors
        is_solo_project: Whether this appears to be a solo project (1 contributor)
        is_collaborative: Whether this has multiple contributors
        contributors: List of contributor statistics
        target_user_email: Email of user we're specifically analyzing for
        target_user_stats: Statistics for the target user (if found)
        primary_branch: Name of the primary branch (main/master)
        total_branches: Number of branches in the repository
        has_remote: Whether the repository has remote URLs configured
        remote_urls: List of remote repository URLs
        error_message: Any error encountered during analysis
        api_data: Placeholder for future API integration data
    """

    project_path: str
    analysis_timestamp: str
    is_git_repo: bool = False
    git_available: bool = False
    total_commits: int = 0
    total_contributors: int = 0
    is_solo_project: bool = False
    is_collaborative: bool = False
    contributors: List[ContributorStats] = field(default_factory=list)
    target_user_email: Optional[str] = None
    target_user_stats: Optional[ContributorStats] = None
    primary_branch: Optional[str] = None
    total_branches: int = 0
    has_remote: bool = False
    remote_urls: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    api_data: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """
        Convert the analysis result to a dictionary for JSON serialization.
        """
        result = asdict(self)
        # convert contributorstats objects to dicts
        # check if these feilds are filled in before data extraction
        if self.contributors:
            result["contributors"] = [asdict(c) if not isinstance(c, dict) else c for c in self.contributors]
        if self.target_user_stats:
            result["target_user_stats"] = (
                asdict(self.target_user_stats) if not isinstance(self.target_user_stats, dict) else self.target_user_stats
            )
        return result


class GitAnalyzer:
    """
    This class handles:
    - Checking for Git availability
    - Executing Git commands safely
    - Parsing Git output
    - Calculating contribution statistics
    """

    def __init__(self, project_path: Union[str, Path]):
        """
        project_path: Path to the project directory to analyze
        """
        self.project_path = Path(project_path).resolve()
        self.git_dir = self.project_path / ".git"

    def analyze(self, target_user_email: Optional[str] = None, use_remote_api: bool = False) -> GitAnalysisResult:
        """
        Perform complete Git analysis on the project.

        Args:
            target_user_email: Optional email of specific user to analyze
            use_remote_api: Whether to fetch data from remote Git APIs

        Returns:
            GitAnalysisResult object containing all analysis data
        """
        # Initialize
        result = GitAnalysisResult(
            project_path=str(self.project_path),
            analysis_timestamp=datetime.now().isoformat(),
            target_user_email=target_user_email,
        )

        # check if .git directory exists
        result.is_git_repo = self.check_git_repo()
        if not result.is_git_repo:
            result.error_message = "No .git directory found"
            return result

        # check if Git command is available
        result.git_available = self.check_git_available()
        if not result.git_available:
            result.error_message = "Git command-line tool not available"
            return result

        # total commits
        try:
            result.total_commits = self.get_total_commits()
        except Exception as e:
            result.error_message = f"Error getting total commits: {str(e)}"
            return result

        # contributor statistics
        try:
            result.contributors = self.get_contributor_stats()
            result.total_contributors = len(result.contributors)
        except Exception as e:
            result.error_message = f"Error getting contributor stats: {str(e)}"
            return result

        # solo or collaborative project
        result.is_solo_project = result.total_contributors == 1
        result.is_collaborative = result.total_contributors > 1

        # target user stats if email provided
        if target_user_email and result.contributors:
            result.target_user_stats = self.find_target_user_stats(result.contributors, target_user_email)

        # branch information
        try:
            result.primary_branch = self.get_primary_branch()
            result.total_branches = self.get_total_branches()
        except Exception as e:
            print(f"Warning: Could not get branch info: {e}")

        # remote URLs
        try:
            result.remote_urls = self.get_remote_urls()
            result.has_remote = len(result.remote_urls) > 0
        except Exception as e:
            print(f"Warning: Could not get remote URLs: {e}")
            # Not critical, continue

        # API integration
        if use_remote_api:
            result.api_data = self._fetch_api_data()

        return result

    def check_git_available(self) -> bool:
        """
        Check if Git command-line tool is available on the system.
        """
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def check_git_repo(self) -> bool:
        """
        Returns: True if .git directory exists
        """
        return self.git_dir.exists() and self.git_dir.is_dir()

    def run_git_command(self, args: List[str], timeout: int = 30) -> Optional[str]:
        """
        Execute a Git command safely and return its output.

        Args:
            args: List of command arguments (e.g., ['log', '--oneline'])
            timeout: Maximum time to wait for command completion (seconds)

        Returns:
            Command output as string, or None if command failed
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Git command failed: {' '.join(args)}")
                print(f"Error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"Git command timed out after {timeout}s: {' '.join(args)}")
            return None
        except Exception as e:
            print(f"Error running git command: {e}")
            return None

    def get_total_commits(self) -> int:
        """
        Get the total number of commits in the repository.

        Returns:
            Total commit count, or 0 if unable to determine
        """
        output = self.run_git_command(["rev-list", "--all", "--count"])
        if output:
            try:
                return int(output)
            except ValueError:
                return 0
        return 0

    def get_contributor_stats(self) -> List[ContributorStats]:
        """
        Get statistics for all contributors in the repository.

        Returns:
            List of ContributorStats objects, sorted by commit count (descending)
        """
        # 123  Author Name <email@example.com>"
        output = self.run_git_command(["shortlog", "-sne", "--all"])

        if not output:
            return []

        email_to_data = {}

        # parse shortlog output
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Extract data
            match = re.match(r"(\d+)\s+(.+?)\s+<(.+?)>", line)
            if match:
                commit_count = int(match.group(1))
                name = match.group(2).strip()
                email = match.group(3).strip()

                # normalize email
                normalized_email = self.normalize_email(email)

                if normalized_email not in email_to_data:
                    email_to_data[normalized_email] = {"names": [], "commit_count": 0, "original_email": email}

                email_to_data[normalized_email]["names"].append(name)
                email_to_data[normalized_email]["commit_count"] += commit_count

        # make list
        contributors = []
        total_commits = 0

        for normalized_email, data in email_to_data.items():
            best_name = self.choose_best_name(data["names"])

            commit_count = data["commit_count"]
            original_email = data["original_email"]

            total_commits += commit_count

            first_date, last_date = self.get_author_commit_dates(original_email)

            contributors.append(
                ContributorStats(
                    name=best_name,
                    email=original_email,
                    commit_count=commit_count,
                    percentage=0.0,
                    first_commit_date=first_date,
                    last_commit_date=last_date,
                )
            )

        # calc percent
        if total_commits > 0:
            for contributor in contributors:
                contributor.percentage = round((contributor.commit_count / total_commits) * 100, 2)

        contributors.sort(key=lambda x: x.commit_count, reverse=True)

        return contributors

    def get_author_commit_dates(self, email: str) -> tuple[Optional[str], Optional[str]]:
        """
        Get first and last commit dates for a specific author in one Git call.

        Args:
            email: Author's email address

        Returns:
            Tuple of (first_commit_date, last_commit_date) or (None, None) if no commits
        """
        # Get ALL commit dates by this author, oldest first
        output = self.run_git_command(
            [
                "log",
                "--all",
                "--author=" + email,
                "--format=%aI",
                "--reverse",  # Oldest first
            ]
        )

        if not output:
            return None, None

        # Split into individual dates
        dates = output.strip().split("\n")

        if not dates or dates == [""]:
            return None, None

        first_date = dates[0]
        last_date = dates[-1]

        return first_date, last_date

    def get_repository_last_commit_date(self) -> Optional[str]:
        """
        Get the date of the most recent commit in the entire repository.

        Returns:
            ISO format timestamp of the last commit, or None if unable to determine
        """
        output = self.run_git_command(
            [
                "log",
                "--all",
                "--format=%aI",
                "-1",  # Only get the most recent commit
            ]
        )

        if not output:
            return None

        return output.strip()

    def normalize_email(self, email: str) -> str:
        """
        Normalize email addresses for consistent matching.
        Args:
            email: Raw email address

        Returns:
            Normalized email address
        """
        email = email.lower().strip()

        # GitHub noreply emails: "12345+username@users.noreply.github.com"

        return email

    def choose_best_name(self, names: List[str]) -> str:
        """
        Strategy:
        1. Prefer longer names (more complete)
        2. Prefer names with capitals (proper formatting)
        3. Prefer most common name (if tie)
        """
        if not names:
            return "Unknown"

        if len(names) == 1:
            return names[0]

        from collections import Counter

        name_counts = Counter(names)

        most_common = name_counts.most_common()

        if most_common[0][1] > most_common[1][1]:
            return most_common[0][0]

        top_names = [name for name, count in most_common if count == most_common[0][1]]

        capitalized = [n for n in top_names if any(c.isupper() for c in n)]
        if capitalized:
            return max(capitalized, key=len)

        return max(top_names, key=len)

    def get_primary_branch(self) -> Optional[str]:
        """
        Returns:
            Branch name as string, or None if unable to determine
        """
        # check if main or master exists
        output = self.run_git_command(["branch", "--list"])
        if output:
            branches = output.split("\n")
            for branch in branches:
                branch = branch.strip().lstrip("* ")
                if branch in ["main", "master"]:
                    return branch

        # fallback
        # get the default branch from remote
        output = self.run_git_command(["symbolic-ref", "refs/remotes/origin/HEAD"])
        if output:
            # extract branch name from "refs/remotes/origin/main"
            parts = output.split("/")
            if len(parts) >= 2:
                return parts[-1]
        return None

    def get_total_branches(self) -> int:
        output = self.run_git_command(["branch", "-a"])
        if output:
            branches = [line.strip() for line in output.split("\n") if line.strip()]
            return len(branches)
        return 0

    def get_remote_urls(self) -> List[str]:
        """
        Returns:
            List of remote URLs, empty list if none found
        """
        output = self.run_git_command(["remote", "-v"])
        if not output:
            return []

        urls = set()
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 2:
                urls.add(parts[1])

        return list(urls)

    def find_target_user_stats(self, contributors: List[ContributorStats], target_email: str) -> Optional[ContributorStats]:
        """
        Find statistics for a specific user by email.

        Args:
            contributors: List of all contributor statistics
            target_email: Email address to search for

        Returns:
            ContributorStats for the target user, or None if not found
        """
        # find if user match
        for contributor in contributors:
            if contributor.email.lower() == target_email.lower():
                return contributor
        target_email_lower = target_email.lower()
        for contributor in contributors:
            if target_email_lower in contributor.email.lower():
                return contributor

        return None

    def _fetch_api_data(self) -> Optional[Dict]:
        """
        TODO
        """
        return {"status": "not_implemented", "message": "API integration coming in future version"}


class GitAnalysisExporter:
    """
    Handles exporting Git analysis results to various formats.
    Currently supports JSON export
    """

    def __init__(self, output_dir: Union[str, Path] = "./analysis_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_json(self, result: GitAnalysisResult, filename: Optional[str] = None) -> Path:

        # Generate filename
        if filename is None:
            project_name = Path(result.project_path).name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{project_name}_git_analysis_{timestamp}"

        # .json extension
        if not filename.endswith(".json"):
            filename += ".json"

        output_path = self.output_dir / filename
        data = result.to_dict()

        # Write to json file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Analysis exported to: {output_path}")
        return output_path


def analyze_project(
    project_path: Union[str, Path],
    target_user_email: Optional[str] = None,
    use_remote_api: bool = False,
    export_to_file: bool = True,
    output_dir: str = "./analysis_results",
) -> GitAnalysisResult:
    """
    Convenience function to analyze a single project.
    Args:
        project_path: Path to the project directory
        target_user_email: Optional email of specific user to analyze
        use_remote_api: Whether to use remote API
        export_to_file: Whether to export results to JSON
        output_dir: Directory for output files

    Returns:
        GitAnalysisResult object

    """
    analyzer = GitAnalyzer(project_path)
    result = analyzer.analyze(target_user_email=target_user_email, use_remote_api=use_remote_api)

    if export_to_file:
        exporter = GitAnalysisExporter(output_dir)
        exporter.export_to_json(result)

    return result
