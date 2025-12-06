"""
Phase 2: Metadata Extraction Module (Non-LLM Analysis)

This module extracts metadata from categorized files to produce a comprehensive
JSON report about projects without using LLMs. It builds on top of FileClassifier(in project_analyzer.py by Aakash)

Key features:
- Detects multiple projects within a folder/ZIP
- Extracts technology stack and dependencies
- Analyzes project structure and complexity
- Extracts git history and contributor information (if available)
- Generates JSON output with project metadata
"""

import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .project_analyzer import FileClassifier


@dataclass
class ContributorInfo:
    # Information about a project contributor

    name: str
    email: str
    commits: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    files_touched: Set[str] = field(default_factory=set)
    first_commit: Optional[str] = None
    last_commit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary for JSON serialization
        return {
            "name": self.name,
            "email": self.email,
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_deleted": self.lines_deleted,
            "files_touched": len(self.files_touched),
            "first_commit": self.first_commit,
            "last_commit": self.last_commit,
        }


@dataclass
class ProjectMetadata:
    # Metadata for a single project

    project_name: str
    project_path: str
    primary_language: Optional[str] = None
    languages: Dict[str, int] = field(default_factory=dict)  # language -> file count
    total_files: int = 0
    total_size: int = 0
    code_files: int = 0
    test_files: int = 0
    doc_files: int = 0
    config_files: int = 0

    # Technology stack detection
    frameworks: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # package_manager -> packages

    # Project structure insights
    has_tests: bool = False
    has_readme: bool = False
    has_ci_cd: bool = False
    has_docker: bool = False
    test_coverage_estimate: Optional[str] = None  # "low", "medium", "high"

    # Git information (if available)
    is_git_repo: bool = False
    contributors: List[Dict[str, Any]] = field(default_factory=list)
    total_commits: int = 0
    last_commit_date: Optional[str] = None
    last_modified_date: Optional[str] = None  # Most recent file modification timestamp from ZIP

    # Complexity indicators
    directory_depth: int = 0
    largest_file: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary for JSON serialization
        return asdict(self)


class MetadataExtractor:
    # Extracts metadata from categorized project files

    # Dependency file patterns for different package managers
    DEPENDENCY_FILES = {
        "python": {
            "requirements.txt": r"^([a-zA-Z0-9\-_]+)",
            "Pipfile": r"^([a-zA-Z0-9\-_]+)\s*=",
            "pyproject.toml": r"^([a-zA-Z0-9\-_]+)",
            "setup.py": r"install_requires.*['\"]([a-zA-Z0-9\-_]+)",
        },
        "javascript": {
            "package.json": None,
            "package-lock.json": None,
            "yarn.lock": r"^\"?([a-zA-Z0-9@/\-_]+)@",
        },
        "java": {
            "pom.xml": r"<artifactId>([^<]+)</artifactId>",
            "build.gradle": r"implementation\s+['\"]([^:]+):([^:]+)",
            "build.gradle.kts": r"implementation\(\"([^:]+):([^:]+)",
        },
        "go": {
            "go.mod": r"require\s+([^\s]+)",
            "go.sum": r"^([^\s]+)\s",
        },
        "ruby": {
            "Gemfile": r"gem\s+['\"]([a-zA-Z0-9\-_]+)",
            "Gemfile.lock": r"^\s{4}([a-zA-Z0-9\-_]+)\s",
        },
        "php": {
            "composer.json": None,
            "composer.lock": None,
        },
    }

    # Framework detection patterns (filename or content patterns)
    FRAMEWORK_PATTERNS = {
        # Python
        "Django": ["manage.py", "settings.py", "wsgi.py"],
        "Flask": ["app.py", "application.py"],
        "FastAPI": ["main.py"],  # Check content for FastAPI imports
        # JavaScript/TypeScript
        "React": ["package.json"],  # Check for react in dependencies
        "Vue": ["package.json"],  # Check for vue
        "Angular": ["angular.json", "ng-package.json"],
        "Next.js": ["next.config.js", "next.config.ts"],
        "Express": ["package.json"],  # Check for express
        # Java
        "Spring": ["pom.xml"],  # Check for spring dependencies
        "Spring Boot": ["pom.xml"],
        # Others
        "Docker": ["Dockerfile", "docker-compose.yml"],
        "Kubernetes": ["deployment.yaml", "service.yaml"],
    }

    # CI/CD indicators
    CI_CD_FILES = [
        ".github/workflows",
        ".gitlab-ci.yml",
        ".travis.yml",
        "Jenkinsfile",
        ".circleci/config.yml",
        "azure-pipelines.yml",
        ".drone.yml",
    ]

    def __init__(self, zip_path: Path):
        # Initialize the metadata extractor.
        #  zip_path: Path to the ZIP file containing projects

        self.zip_path = zip_path
        self.zip_file = zipfile.ZipFile(zip_path, "r")
        self.classifier = FileClassifier(zip_path)

    def _is_excluded_directory(self, path: str) -> bool:
        """
        Check if a directory should be excluded from project detection.
        Excludes cache directories, virtual environments, OS metadata, etc.
        """
        normalized = path.replace("\\", "/").lower()
        parts = normalized.split("/")

        # Exclude patterns
        exclude_patterns = [
            "__macosx",  # macOS metadata
            ".pytest_cache",
            "__pycache__",
            ".cache",
            "node_modules",
            "venv",
            "env",
            ".venv",
            ".env",
            "virtualenv",
            ".git",
            ".svn",
            ".hg",
            "build",
            "dist",
            ".idea",
            ".vscode",
            ".vs",
            "target",  # Maven/Gradle build directory
            "bin",
            "obj",  # .NET build artifacts
            ".next",  # Next.js build
            ".nuxt",  # Nuxt.js build
        ]

        # Check if any part of the path matches exclude patterns
        for part in parts:
            if part in exclude_patterns:
                return True
            # Also check if part starts with excluded patterns (e.g., .pytest_cache, __pycache__)
            for pattern in exclude_patterns:
                if part.startswith(pattern) or part.endswith(pattern):
                    return True

        return False

    def _has_code_files(self, project_path: str) -> bool:
        """
        Check if a project path contains actual code files.
        Returns True if the project has code files, False otherwise.
        """
        code_extensions = {
            ".py",
            ".java",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".swift",
            ".kt",
            ".scala",
            ".clj",
            ".r",
            ".m",
            ".mm",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".vue",
            ".svelte",
            ".sql",
            ".pl",
            ".pm",
            ".lua",
            ".dart",
            ".elm",
            ".ex",
            ".exs",
        }

        prefix = f"{project_path}/" if project_path else ""

        for file_path in self.zip_file.namelist():
            if file_path.endswith("/"):
                continue

            normalized = file_path.replace("\\", "/")

            # Check if file belongs to this project
            if project_path:
                if not normalized.startswith(prefix):
                    continue
            else:
                # For root project, exclude excluded directories
                if "/" in normalized and self._is_excluded_directory(normalized.split("/")[0]):
                    continue

            # Check if it's a code file
            ext = Path(normalized).suffix.lower()
            if ext in code_extensions:
                return True

        return False

    def detect_projects(self) -> List[str]:
        # Detect projects by looking for specific files and directories
        # requirements.txt, package.json, README.md, .git, etc.
        # Returns a list of project root paths within the ZIP
        projects = []
        all_files = self.zip_file.namelist()

        # Look for project indicators at various depths
        project_indicators = set()

        for file_path in all_files:
            if file_path.endswith("/"):
                continue

            normalized_path = file_path.replace("\\", "/")
            parts = normalized_path.split("/")
            filename = parts[-1].lower()

            # Skip files in excluded directories
            if self._is_excluded_directory(normalized_path):
                continue

            # Check for dependency files
            is_dependency_file = False
            for lang_deps in self.DEPENDENCY_FILES.values():
                if filename in [f.lower() for f in lang_deps.keys()]:
                    is_dependency_file = True
                    break

            # Check for README
            is_readme = "readme" in filename

            # Check for common project root indicators
            is_project_indicator = is_dependency_file or is_readme

            if is_project_indicator:
                # Get the directory containing this file
                if len(parts) > 1:
                    project_root = "/".join(parts[:-1])
                else:
                    project_root = ""

                # Skip if the project root is in an excluded directory
                if not self._is_excluded_directory(project_root):
                    project_indicators.add(project_root)

        # If no clear projects found, treat the root as a single project
        if not project_indicators:
            # But only if root has code files and is not excluded
            if self._has_code_files(""):
                return [""]
            return []

        # Sort by depth (shallowest first) and remove nested projects
        sorted_indicators = sorted(project_indicators, key=lambda x: x.count("/"))
        final_projects = []

        for indicator in sorted_indicators:
            # Skip excluded directories
            if self._is_excluded_directory(indicator):
                continue

            # Check if this is a nested project of an already detected one
            is_nested = False
            for existing in final_projects:
                if indicator.startswith(existing + "/"):
                    is_nested = True
                    break

            if not is_nested:
                # Only add if it has code files
                if self._has_code_files(indicator):
                    final_projects.append(indicator)

        # If no valid projects found but root has code files, return root
        if not final_projects and self._has_code_files(""):
            return [""]

        return final_projects if final_projects else [""]

    def extract_dependencies(self, project_path: str, config_files: List[Dict]) -> Dict[str, List[str]]:
        # Extract dependencies from configuration files.
        # Returns a dictionary mapping package manager to list of dependencies

        dependencies = defaultdict(list)

        for config_file in config_files:
            file_path = config_file["path"]
            filename = config_file["filename"].lower()

            # Determine which dependency system this belongs to
            for lang, dep_files in self.DEPENDENCY_FILES.items():
                if filename in [f.lower() for f in dep_files.keys()]:
                    # Extract dependencies based on file type
                    deps = self._parse_dependency_file(file_path, filename, dep_files)
                    if deps:
                        dependencies[lang].extend(deps)

        return dict(dependencies)

    def _parse_dependency_file(self, file_path: str, filename: str, patterns: Dict[str, str]) -> List[str]:
        # Parse a specific dependency file.
        # Returns a list of dependency names found in the file.

        try:
            content = self.zip_file.read(file_path).decode("utf-8", errors="ignore")
        except Exception:
            return []

        dependencies = []

        # Special handling for JSON files
        if filename.endswith(".json"):
            try:
                data = json.loads(content)
                if filename == "package.json" and "dependencies" in data:
                    dependencies.extend(data["dependencies"].keys())
                if filename == "package.json" and "devDependencies" in data:
                    dependencies.extend(data["devDependencies"].keys())
                if filename == "composer.json" and "require" in data:
                    dependencies.extend(data["require"].keys())
            except json.JSONDecodeError:
                pass
        else:
            # Use regex patterns
            pattern = None
            for file_pattern, regex in patterns.items():
                if filename == file_pattern.lower() and regex:
                    pattern = regex
                    break

            if pattern:
                matches = re.findall(pattern, content, re.MULTILINE)
                dependencies.extend(matches)

        return list(set(dependencies))  # Remove duplicates

    def detect_frameworks(self, project_path: str, all_files: Dict) -> List[str]:
        # Detect frameworks used in the project.
        # Returns a list of detected frameworks

        detected_frameworks = []

        # Collect all filenames
        all_filenames = set()
        for category in ["code", "docs", "configs", "tests"]:
            if category == "code":
                for lang_files in all_files.get("code", {}).values():
                    for file_info in lang_files:
                        all_filenames.add(file_info["filename"].lower())
            else:
                for file_info in all_files.get(category, []):
                    all_filenames.add(file_info["filename"].lower())

        # Check for framework indicators
        for framework, indicators in self.FRAMEWORK_PATTERNS.items():
            for indicator in indicators:
                if indicator.lower() in all_filenames:
                    # Additional checks for package.json frameworks
                    if indicator == "package.json":
                        # Check dependencies
                        for config_file in all_files.get("configs", []):
                            if config_file["filename"].lower() == "package.json":
                                content = self._read_file_content(config_file["path"])
                                if content and framework.lower() in content.lower():
                                    detected_frameworks.append(framework)
                                    break
                    else:
                        detected_frameworks.append(framework)
                        break

        return list(set(detected_frameworks))

    def _read_file_content(self, file_path: str, max_size: int = 100000) -> Optional[str]:
        # Read file content from ZIP.
        # Returns the content of the file or None if not found or too large.

        try:
            file_info = self.zip_file.getinfo(file_path)
            if file_info.file_size > max_size:
                return None
            return self.zip_file.read(file_path).decode("utf-8", errors="ignore")
        except Exception:
            return None

    def check_ci_cd(self, all_files: Dict) -> bool:
        # Check if the project has CI/CD configuration.
        # Returns True if CI/CD is detected
        all_paths = []
        for category in ["code", "docs", "configs", "tests"]:
            if category == "code":
                for lang_files in all_files.get("code", {}).values():
                    for file_info in lang_files:
                        all_paths.append(file_info["path"].lower())
            else:
                for file_info in all_files.get(category, []):
                    all_paths.append(file_info["path"].lower())

        for ci_indicator in self.CI_CD_FILES:
            for path in all_paths:
                if ci_indicator.lower() in path:
                    return True

        return False

    def calculate_directory_depth(self, all_files: Dict) -> int:
        # Calculate the maximum directory depth in the project.
        # Returns maximum directory depth

        max_depth = 0

        for category in ["code", "docs", "configs", "tests"]:
            if category == "code":
                for lang_files in all_files.get("code", {}).values():
                    for file_info in lang_files:
                        depth = file_info["path"].count("/")
                        max_depth = max(max_depth, depth)
            else:
                for file_info in all_files.get(category, []):
                    depth = file_info["path"].count("/")
                    max_depth = max(max_depth, depth)

        return max_depth

    def find_largest_file(self, all_files: Dict) -> Optional[Dict[str, Any]]:
        # Find the largest file in the project.
        # Returns information about the largest file

        largest = None
        largest_size = 0

        for category in ["code", "docs", "configs", "tests"]:
            if category == "code":
                for lang_files in all_files.get("code", {}).values():
                    for file_info in lang_files:
                        if file_info["size"] > largest_size:
                            largest_size = file_info["size"]
                            largest = file_info
            else:
                for file_info in all_files.get(category, []):
                    if file_info["size"] > largest_size:
                        largest_size = file_info["size"]
                        largest = file_info

        if largest:
            return {
                "path": largest["path"],
                "size": largest["size"],
                "size_mb": round(largest["size"] / (1024 * 1024), 2),
            }

        return None

    def estimate_test_coverage(self, code_files: int, test_files: int) -> str:
        # Estimate test coverage based on ratio of test files to code files.
        # Returns "none", "low", "medium", or "high"

        if test_files == 0:
            return "none"

        ratio = test_files / code_files if code_files > 0 else 0

        if ratio >= 0.5:
            return "high"
        elif ratio >= 0.2:
            return "medium"
        else:
            return "low"

    def get_last_modified_date(self, project_path: str) -> Optional[str]:
        """
        Get the most recent file modification timestamp from ZIP file entries.
        This serves as a fallback when git commit date is not available.
        
        Args:
            project_path: Path prefix for the project within the ZIP
            
        Returns:
            ISO format timestamp of the most recently modified file, or None if no files found
        """
        from datetime import datetime
        
        prefix = f"{project_path}/" if project_path else ""
        most_recent_time = None
        
        for zip_info in self.zip_file.infolist():
            # Check if file belongs to this project
            if zip_info.filename.startswith(prefix):
                # Skip directories
                if zip_info.filename.endswith('/'):
                    continue
                    
                # Get modification time (date_time is a tuple: (year, month, day, hour, minute, second))
                try:
                    mod_time = datetime(*zip_info.date_time)
                    
                    if most_recent_time is None or mod_time > most_recent_time:
                        most_recent_time = mod_time
                except (ValueError, TypeError):
                    # Skip files with invalid timestamps
                    continue
        
        if most_recent_time:
            return most_recent_time.isoformat()
        
        return None

    def parse_git_log(self, project_path: str) -> tuple[Dict[str, ContributorInfo], int, Optional[str]]:
        # Parse git log if .git directory is present in the ZIP.
        # Returns a tuple of (contributors dict, total commits, last_commit_date)

        contributors = {}
        total_commits = 0
        last_commit_date = None

        # Look for .git directory or git-related files
        git_path = f"{project_path}/.git" if project_path else ".git"

        # Check if git directory exists
        has_git = False
        for file_path in self.zip_file.namelist():
            if file_path.startswith(git_path):
                has_git = True
                break

        if not has_git:
            return contributors, total_commits, last_commit_date

        # Try to use GitAnalyzer if we have a real git repository extracted
        # For ZIP files, we need to extract and analyze temporarily
        try:
            from .git_analysis import GitAnalyzer
            import tempfile
            import shutil
            
            # Create temp directory and extract project
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the project to temp directory
                temp_project_path = Path(temp_dir) / "project"
                temp_project_path.mkdir()
                
                prefix = f"{project_path}/" if project_path else ""
                for member in self.zip_file.namelist():
                    if member.startswith(prefix):
                        # Extract to temp location
                        self.zip_file.extract(member, temp_project_path)
                
                # Point to the extracted project directory
                extracted_path = temp_project_path / project_path if project_path else temp_project_path
                
                if (extracted_path / ".git").exists():
                    analyzer = GitAnalyzer(str(extracted_path))
                    
                    if analyzer.check_git_available() and analyzer.check_git_repo():
                        # Get total commits
                        total_commits = analyzer.get_total_commits()
                        
                        # Get last commit date
                        last_commit_date = analyzer.get_repository_last_commit_date()
        except Exception:
            # If git analysis fails, just return what we have
            pass

        return contributors, total_commits, last_commit_date

    def extract_project_metadata(self, project_path: str) -> ProjectMetadata:
        # Extract metadata for a single project.
        # Returns ProjectMetadata object with all extracted information

        # Get file classification from Phase 1
        classification = self.classifier.classify_project(project_path)

        files = classification["files"]
        stats = classification["stats"]

        # Initialize metadata
        project_name = project_path.split("/")[-1] if project_path else "root_project"
        if not project_name:
            project_name = Path(self.zip_path).stem

        metadata = ProjectMetadata(
            project_name=project_name,
            project_path=project_path,
            total_files=stats["total_files"],
            total_size=stats["total_size"],
        )

        # Count files by category
        metadata.code_files = sum(len(files_list) for files_list in files["code"].values())
        metadata.test_files = len(files["tests"])
        metadata.doc_files = len(files["docs"])
        metadata.config_files = len(files["configs"])

        # Language statistics
        language_counts = {lang: len(file_list) for lang, file_list in files["code"].items()}
        metadata.languages = language_counts

        if language_counts:
            metadata.primary_language = max(language_counts, key=language_counts.get)

        # Project structure indicators
        metadata.has_tests = metadata.test_files > 0
        metadata.has_readme = any("readme" in f["filename"].lower() for f in files["docs"])
        metadata.has_docker = any(
            "dockerfile" in f["filename"].lower() or "docker-compose" in f["filename"].lower() for f in files["configs"]
        )
        metadata.has_ci_cd = self.check_ci_cd(files)

        # Test coverage estimate
        metadata.test_coverage_estimate = self.estimate_test_coverage(metadata.code_files, metadata.test_files)

        # Extract dependencies
        metadata.dependencies = self.extract_dependencies(project_path, files["configs"])

        # Detect frameworks
        metadata.frameworks = self.detect_frameworks(project_path, files)

        # Complexity indicators
        metadata.directory_depth = self.calculate_directory_depth(files)
        metadata.largest_file = self.find_largest_file(files)

        # Git analysis (if available)
        contributors, total_commits, last_commit_date = self.parse_git_log(project_path)
        metadata.is_git_repo = total_commits > 0 or self._check_git_files(project_path)
        metadata.total_commits = total_commits
        metadata.last_commit_date = last_commit_date
        metadata.contributors = [c.to_dict() for c in contributors.values()]
        
        # Get last modified date from ZIP file metadata (fallback when git is not available)
        metadata.last_modified_date = self.get_last_modified_date(project_path)

        return metadata

    def _check_git_files(self, project_path: str) -> bool:
        """Check if git-related files exist in the project."""
        git_indicators = [".git/", ".gitignore", ".gitattributes"]
        prefix = f"{project_path}/" if project_path else ""

        for file_path in self.zip_file.namelist():
            normalized = file_path.replace("\\", "/")
            for indicator in git_indicators:
                if normalized.startswith(prefix + indicator) or normalized == prefix.rstrip("/") + "/" + indicator:
                    return True

        return False

    def generate_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        # Generate the full metadata report for all detected projects.
        # Returns a dictionary containing the full report

        # Detect all projects
        project_paths = self.detect_projects()

        # Extract metadata for each project
        projects_metadata = []
        for project_path in project_paths:
            # Skip excluded directories
            if self._is_excluded_directory(project_path):
                continue

            # Skip if no code files
            if not self._has_code_files(project_path):
                continue

            metadata = self.extract_project_metadata(project_path)

            # Additional validation: skip projects with no files or no code files
            if metadata.total_files == 0 or metadata.code_files == 0:
                continue

            projects_metadata.append(metadata.to_dict())

        # Build final report
        report = {
            "analysis_metadata": {
                "zip_file": str(self.zip_path),
                "analysis_timestamp": datetime.now().isoformat(),
                "total_projects": len(projects_metadata),
            },
            "projects": projects_metadata,
            "summary": {
                "total_files": sum(p["total_files"] for p in projects_metadata),
                "total_size_bytes": sum(p["total_size"] for p in projects_metadata),
                "total_size_mb": round(sum(p["total_size"] for p in projects_metadata) / (1024 * 1024), 2),
                "languages_used": list(set(lang for p in projects_metadata for lang in p["languages"].keys())),
                "frameworks_used": list(set(fw for p in projects_metadata for fw in p["frameworks"])),
            },
        }

        # Save to file if requested
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        return report

    def close(self):
        # Close resources
        if hasattr(self, "classifier"):
            self.classifier.close()
        if hasattr(self, "zip_file"):
            self.zip_file.close()

    def __enter__(self):
        # Context manager enter
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Context manager exit
        self.close()

    def __del__(self):
        # Ensure resources are closed
        self.close()
