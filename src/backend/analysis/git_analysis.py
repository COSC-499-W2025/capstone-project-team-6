'''
Analyzes Git repositories to determine authorship and collaboration patterns.

This module provides functionality to:
1. Detect Git repositories from traversal results
2. Execute local Git commands to extract contribution data
3. Calculate contribution metrics and statistics
4. Export results to JSON format
'''

from dataclasses import dataclass, asdict, field
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
            result['contributors'] = [asdict(c) if not isinstance(c, dict) else c 
                                     for c in self.contributors]
        if self.target_user_stats:
            result['target_user_stats'] = (asdict(self.target_user_stats) 
                                          if not isinstance(self.target_user_stats, dict) 
                                          else self.target_user_stats)
        return result

















