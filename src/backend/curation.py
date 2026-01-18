"""
Project curation functionality for MDA CLI.

This module provides functionality for users to curate their analyzed projects by:
- Correcting project chronology (dates)
- Selecting comparison attributes 
- Choosing showcase projects

User curation preferences are stored in the database and used to customize
project displays and comparisons.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

try:
    from .. import analysis_database as db
except ImportError:
    # Handle direct execution or testing
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    src_dir = current_dir.parent
    sys.path.insert(0, str(src_dir))
    from backend import analysis_database as db


@dataclass
class ProjectCurationSettings:
    """User's curation settings for their projects."""
    user_id: str
    comparison_attributes: List[str]
    showcase_project_ids: List[int]
    custom_project_order: List[int]
    
    
@dataclass 
class ProjectChronologyCorrection:
    """A user's correction to a project's chronological information."""
    project_id: int
    user_id: str
    last_commit_date: Optional[str] = None
    last_modified_date: Optional[str] = None
    project_start_date: Optional[str] = None
    project_end_date: Optional[str] = None
    correction_timestamp: Optional[str] = None


# Default attributes available for project comparison
DEFAULT_COMPARISON_ATTRIBUTES = [
    "total_files",
    "code_files", 
    "test_files",
    "has_tests",
    "has_readme",
    "has_ci_cd",
    "has_docker",
    "primary_language",
    "total_commits",
    "project_active_days",
    "test_coverage_estimate"
]

# Human-readable descriptions for attributes
ATTRIBUTE_DESCRIPTIONS = {
    "total_files": "Total files count",
    "code_files": "Source code files",
    "test_files": "Test files count", 
    "has_tests": "Has test suite",
    "has_readme": "Has README documentation",
    "has_ci_cd": "Has CI/CD setup",
    "has_docker": "Has Docker configuration",
    "primary_language": "Primary programming language",
    "total_commits": "Total git commits",
    "project_active_days": "Project duration (days)",
    "test_coverage_estimate": "Test coverage level",
    "target_user_commits": "Your commits count",
    "target_user_commit_pct": "Your contribution percentage", 
    "directory_depth": "Project complexity (depth)",
    "total_size": "Project size (bytes)",
    "has_remote": "Has remote repository"
}


def init_curation_tables() -> None:
    """Initialize database tables for curation functionality."""
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Table for user curation settings
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_curation_settings (
                user_id TEXT NOT NULL,
                comparison_attributes TEXT NOT NULL, -- JSON array of attribute names
                showcase_project_ids TEXT NOT NULL, -- JSON array of project IDs
                custom_project_order TEXT NOT NULL DEFAULT '[]', -- JSON array of project IDs for custom order
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id)
            );
        """)
        
        # Table for chronology corrections
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_chronology_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL,
                last_commit_date TEXT,
                last_modified_date TEXT,
                project_start_date TEXT,
                project_end_date TEXT,
                correction_timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (project_id, user_id)
            );
        """)
        
        conn.commit()


def get_user_projects(user_id: str) -> List[Dict[str, Any]]:
    """Get all projects analyzed by the user with their current chronology."""
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        
        query = """
            SELECT p.*,
                   a.analysis_timestamp,
                   a.zip_file,
                   -- Use corrections if available, otherwise original values
                   COALESCE(pcc.last_commit_date, p.last_commit_date) as effective_last_commit_date,
                   COALESCE(pcc.last_modified_date, p.last_modified_date) as effective_last_modified_date,
                   COALESCE(pcc.project_start_date, p.project_start_date) as effective_project_start_date,
                   COALESCE(pcc.project_end_date, p.project_end_date) as effective_project_end_date,
                   pcc.correction_timestamp
            FROM projects p
            JOIN analyses a ON a.id = p.analysis_id 
            LEFT JOIN project_chronology_corrections pcc ON pcc.project_id = p.id AND pcc.user_id = ?
            ORDER BY COALESCE(pcc.last_commit_date, p.last_commit_date, p.last_modified_date, a.analysis_timestamp) ASC
        """
        
        rows = conn.execute(query, (user_id,)).fetchall()
        
        projects = []
        for row in rows:
            project = dict(row)
            
            # Add language and framework info
            languages = conn.execute("""
                SELECT language, file_count FROM project_languages 
                WHERE project_id = ? ORDER BY file_count DESC
            """, (project["id"],)).fetchall()
            
            frameworks = conn.execute("""
                SELECT framework FROM project_frameworks 
                WHERE project_id = ? ORDER BY framework
            """, (project["id"],)).fetchall()
            
            project["languages"] = {lang["language"]: lang["file_count"] for lang in languages}
            project["frameworks"] = [fw["framework"] for fw in frameworks]
            
            projects.append(project)
            
        return projects


def save_chronology_correction(
    project_id: int, 
    user_id: str,
    last_commit_date: Optional[str] = None,
    last_modified_date: Optional[str] = None, 
    project_start_date: Optional[str] = None,
    project_end_date: Optional[str] = None
) -> bool:
    """Save user's corrections to project chronology."""
    try:
        with db.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            
            # Validate project exists
            project = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not project:
                return False
                
            # Insert or update correction
            conn.execute("""
                INSERT OR REPLACE INTO project_chronology_corrections 
                (project_id, user_id, last_commit_date, last_modified_date, 
                 project_start_date, project_end_date, correction_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id, user_id, last_commit_date, last_modified_date,
                project_start_date, project_end_date, datetime.now().isoformat()
            ))
            
            conn.commit()
            return True
            
    except Exception:
        return False


def get_chronology_corrections(user_id: str) -> List[ProjectChronologyCorrection]:
    """Get all chronology corrections made by the user."""
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        
        rows = conn.execute("""
            SELECT * FROM project_chronology_corrections 
            WHERE user_id = ? ORDER BY correction_timestamp DESC
        """, (user_id,)).fetchall()
        
        return [
            ProjectChronologyCorrection(
                project_id=row["project_id"],
                user_id=row["user_id"], 
                last_commit_date=row["last_commit_date"],
                last_modified_date=row["last_modified_date"],
                project_start_date=row["project_start_date"],
                project_end_date=row["project_end_date"],
                correction_timestamp=row["correction_timestamp"]
            )
            for row in rows
        ]


def save_comparison_attributes(user_id: str, attributes: List[str]) -> bool:
    """Save user's preferred comparison attributes."""
    try:
        # Validate attributes
        valid_attributes = set(DEFAULT_COMPARISON_ATTRIBUTES + list(ATTRIBUTE_DESCRIPTIONS.keys()))
        invalid = set(attributes) - valid_attributes
        if invalid:
            raise ValueError(f"Invalid attributes: {invalid}")
            
        import json
        with db.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            
            conn.execute("""
                INSERT OR REPLACE INTO user_curation_settings
                (user_id, comparison_attributes, showcase_project_ids, updated_at)
                VALUES (
                    ?, 
                    ?, 
                    COALESCE((SELECT showcase_project_ids FROM user_curation_settings WHERE user_id = ?), '[]'),
                    ?
                )
            """, (user_id, json.dumps(attributes), user_id, datetime.now().isoformat()))
            
            conn.commit()
            return True
            
    except Exception:
        return False


def save_showcase_projects(user_id: str, project_ids: List[int]) -> bool:
    """Save user's showcase project selection (max 3)."""
    try:
        if len(project_ids) > 3:
            raise ValueError("Maximum 3 showcase projects allowed")
            
        # Validate projects exist
        with db.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            
            for pid in project_ids:
                project = conn.execute("SELECT id FROM projects WHERE id = ?", (pid,)).fetchone()
                if not project:
                    raise ValueError(f"Project {pid} not found")
            
            import json
            conn.execute("""
                INSERT OR REPLACE INTO user_curation_settings
                (user_id, comparison_attributes, showcase_project_ids, updated_at)
                VALUES (
                    ?,
                    COALESCE((SELECT comparison_attributes FROM user_curation_settings WHERE user_id = ?), ?),
                    ?,
                    ?
                )
            """, (user_id, user_id, json.dumps(DEFAULT_COMPARISON_ATTRIBUTES), json.dumps(project_ids), datetime.now().isoformat()))
            
            conn.commit()
            return True
            
    except Exception:
        return False


def get_user_curation_settings(user_id: str) -> ProjectCurationSettings:
    """Get user's current curation settings."""
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        
        row = conn.execute("""
            SELECT comparison_attributes, showcase_project_ids 
            FROM user_curation_settings WHERE user_id = ?
        """, (user_id,)).fetchone()
        
        if row:
            import json
            return ProjectCurationSettings(
                user_id=user_id,
                comparison_attributes=json.loads(row["comparison_attributes"]),
                showcase_project_ids=json.loads(row["showcase_project_ids"])
            )
        else:
            # Return defaults
            return ProjectCurationSettings(
                user_id=user_id,
                comparison_attributes=DEFAULT_COMPARISON_ATTRIBUTES.copy(),
                showcase_project_ids=[]
            )


def get_showcase_projects(user_id: str) -> List[Dict[str, Any]]:
    """Get user's showcase projects with full details."""
    settings = get_user_curation_settings(user_id)
    if not settings.showcase_project_ids:
        return []
        
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Build query for showcase projects
        placeholders = ",".join("?" * len(settings.showcase_project_ids))
        query = f"""
            SELECT p.*,
                   a.analysis_timestamp,
                   a.zip_file,
                   COALESCE(pcc.last_commit_date, p.last_commit_date) as effective_last_commit_date,
                   COALESCE(pcc.last_modified_date, p.last_modified_date) as effective_last_modified_date,
                   COALESCE(pcc.project_start_date, p.project_start_date) as effective_project_start_date,
                   COALESCE(pcc.project_end_date, p.project_end_date) as effective_project_end_date
            FROM projects p
            JOIN analyses a ON a.id = p.analysis_id
            LEFT JOIN project_chronology_corrections pcc ON pcc.project_id = p.id AND pcc.user_id = ?
            WHERE p.id IN ({placeholders})
            ORDER BY 
                CASE p.id {" ".join(f"WHEN {pid} THEN {i}" for i, pid in enumerate(settings.showcase_project_ids))} END
        """
        
        rows = conn.execute(query, [user_id] + settings.showcase_project_ids).fetchall()
        
        projects = []
        for row in rows:
            project = dict(row)
            
            # Add language and framework info  
            languages = conn.execute("""
                SELECT language, file_count FROM project_languages 
                WHERE project_id = ? ORDER BY file_count DESC
            """, (project["id"],)).fetchall()
            
            frameworks = conn.execute("""
                SELECT framework FROM project_frameworks 
                WHERE project_id = ? ORDER BY framework
            """, (project["id"],)).fetchall()
            
            project["languages"] = {lang["language"]: lang["file_count"] for lang in languages}
            project["frameworks"] = [fw["framework"] for fw in frameworks]
            
            projects.append(project)
            
        return projects


def validate_date_format(date_str: str) -> bool:
    """Validate date string is in ISO format."""
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


def format_project_comparison(projects: List[Dict[str, Any]], user_id: str) -> str:
    """Format projects for comparison using user's selected attributes."""
    if not projects:
        return "No projects to compare."
        
    settings = get_user_curation_settings(user_id)
    attributes = settings.comparison_attributes
    
    # Build comparison table
    lines = []
    
    # Header
    header = f"{'Project':<25}"
    for attr in attributes[:6]:  # Limit to prevent overflow
        desc = ATTRIBUTE_DESCRIPTIONS.get(attr, attr)
        header += f" {desc:<15}"
    lines.append(header)
    lines.append("-" * len(header))
    
    # Project rows
    for project in projects:
        name = project["project_name"][:23]
        row = f"{name:<25}"
        
        for attr in attributes[:6]:
            value = project.get(attr)
            if value is None:
                value = "N/A"
            elif isinstance(value, bool):
                value = "Yes" if value else "No"
            elif isinstance(value, (int, float)) and attr == "target_user_commit_pct":
                value = f"{value:.1f}%" if value else "N/A"
            else:
                value = str(value)[:13]
                
            row += f" {value:<15}"
            
        lines.append(row)
        
    return "\n".join(lines)