'''
Analyzes Git repositories to determine authorship and collaboration patterns.

This module provides functionality to:
1. Detect Git repositories from traversal results
2. Execute local Git commands to extract contribution data
3. Calculate contribution metrics and statistics
4. Export results to JSON format
'''

from dataclasses import dataclass
from typing import Optional

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


















