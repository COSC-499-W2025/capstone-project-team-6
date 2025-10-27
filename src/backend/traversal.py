from pathlib import Path
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Set, Protocol, Iterator
from abc import ABC, abstractmethod
import zipfile


class FileSystemEntry(Protocol):
    """Protocol defining a file system entry (file or directory)."""

    @property
    def name(self) -> str:
        """Get the name of this entry."""
        ...

    @property
    def path_str(self) -> str:
        """Get the string representation of the path."""
        ...

    def is_file(self) -> bool:
        """Check if this entry is a file."""
        ...

    def is_dir(self) -> bool:
        """Check if this entry is a directory."""
        ...


class FileSystemInterface(ABC):
    """Abstract interface for file system operations."""

    @abstractmethod
    def iterdir(self, path: str) -> Iterator[FileSystemEntry]:
        """Iterate over entries in a directory."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a path exists."""
        ...

    @abstractmethod
    def get_entry(self, path: str) -> FileSystemEntry:
        """Get a file system entry for a path."""
        ...


class RegularFileEntry:
    """Wrapper for regular file system Path objects."""

    def __init__(self, path: Path):
        self._path = path

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def path_str(self) -> str:
        return str(self._path)

    def is_file(self) -> bool:
        return self._path.is_file()

    def is_dir(self) -> bool:
        return self._path.is_dir()

    def __repr__(self):
        return f"RegularFileEntry({self._path})"


class ZipFileEntry:
    """Wrapper for ZIP file entries."""

    def __init__(self, zip_info: zipfile.ZipInfo, full_path: str):
        self._info = zip_info
        self._full_path = full_path
        # Extract just the name (last component)
        self._name = full_path.rstrip('/').split('/')[-1] if full_path else ''

    @property
    def name(self) -> str:
        return self._name

    @property
    def path_str(self) -> str:
        # Normalize by removing trailing slash for directories
        return self._full_path.rstrip('/')

    def is_file(self) -> bool:
        return not self._info.is_dir()

    def is_dir(self) -> bool:
        return self._info.is_dir()

    def __repr__(self):
        return f"ZipFileEntry({self._full_path})"


class RegularFileSystem(FileSystemInterface):
    """File system interface for regular directories."""

    def iterdir(self, path: str) -> Iterator[FileSystemEntry]:
        """Iterate over entries in a regular directory."""
        path_obj = Path(path)
        try:
            for item in path_obj.iterdir():
                yield RegularFileEntry(item)
        except (PermissionError, FileNotFoundError):
            return

    def exists(self, path: str) -> bool:
        """Check if a regular path exists."""
        return Path(path).exists()

    def get_entry(self, path: str) -> FileSystemEntry:
        """Get a file system entry for a regular path."""
        return RegularFileEntry(Path(path))


class ZipFileSystem(FileSystemInterface):
    """File system interface for ZIP archives."""

    def __init__(self, zip_path: Path):
        self.zip_path = zip_path
        self.zip_file = zipfile.ZipFile(zip_path, 'r')
        # Build a directory structure mapping
        self._build_directory_map()

    def _build_directory_map(self):
        """Build a map of directories to their immediate children."""
        self.dir_map: Dict[str, List[zipfile.ZipInfo]] = {}

        # Add root
        self.dir_map[''] = []

        # Process all entries
        for info in self.zip_file.infolist():
            path = info.filename.rstrip('/')

            # Add directory entries
            if info.is_dir():
                if path not in self.dir_map:
                    self.dir_map[path] = []

            # Determine parent directory
            if '/' in path:
                parent = '/'.join(path.split('/')[:-1])
            else:
                parent = ''

            # Add to parent's children
            if parent not in self.dir_map:
                self.dir_map[parent] = []

            # Only add if not already present (avoid duplicates)
            if not any(child.filename.rstrip('/') == path for child in self.dir_map[parent]):
                self.dir_map[parent].append(info)

    def iterdir(self, path: str) -> Iterator[FileSystemEntry]:
        """Iterate over entries in a ZIP directory."""
        # Normalize path (remove leading/trailing slashes)
        path = path.strip('/')

        if path not in self.dir_map:
            return

        for info in self.dir_map[path]:
            full_path = info.filename
            yield ZipFileEntry(info, full_path)

    def exists(self, path: str) -> bool:
        """Check if a path exists in the ZIP file."""
        path = path.strip('/')

        # Check if it's a directory in our map
        if path in self.dir_map or path == '':
            return True

        # Check if it's a file
        try:
            self.zip_file.getinfo(path)
            return True
        except KeyError:
            return False

    def get_entry(self, path: str) -> FileSystemEntry:
        """Get a file system entry for a ZIP path."""
        path = path.strip('/')

        # Try to get as file first
        try:
            info = self.zip_file.getinfo(path)
            return ZipFileEntry(info, path)
        except KeyError:
            pass

        # Try as directory
        if path in self.dir_map:
            # Create a synthetic directory entry
            info = zipfile.ZipInfo(filename=path + '/')
            return ZipFileEntry(info, path)

        raise FileNotFoundError(f"Path {path} not found in ZIP")

    def close(self):
        """Close the ZIP file."""
        self.zip_file.close()

    def __del__(self):
        """Ensure ZIP file is closed."""
        if hasattr(self, 'zip_file'):
            self.zip_file.close()


@dataclass
class DirectoryNode:
    """
    Represents a directory in the file system with project detection metadata.

    path - stores the path (can be Path for regular files or str for ZIP entries)
    is_project - tells whether the current node/directory is considered as a project or a container
    score - hueristic score on the current node for being a project
    indicators_found - shows the list of positive and negative indicators to calculate the points
    subpoject_count - is the number of subprojects to see if the current node needs to reject its project status and pass it onto the sub folders inside it
    has_files - general check

    """
    path: Path | str
    is_project: bool = False
    score: float = 0.0
    indicators_found: List[str] = field(default_factory=list)
    subproject_count: int = 0
    has_files: bool = False

    @property
    def path_str(self) -> str:
        """Get the string representation of the path."""
        return str(self.path)

    @property
    def name(self) -> str:
        """Get the name (last component) of the path."""
        if isinstance(self.path, Path):
            return self.path.name
        else:
            # For string paths (ZIP entries), get last component
            return self.path.rstrip('/').split('/')[-1] if self.path else ''

    def __repr__(self):
        return (f"DirectoryNode(path={self.name}, is_project={self.is_project}, "
                f"score={self.score:.1f}, subprojects={self.subproject_count})")
    

class ProjectHeuristics:
    """
    Defines scoring rules for project detection.

    list was generated and sorted into levels, scores were assigned manually
    """
    
    # Strong indicators - Common files found in all project roots 
    STRONG_INDICATORS = {
        '.git': 100,
        '.gitignore': 15,
        'package.json': 80,
        'pyproject.toml': 80,
        'Cargo.toml': 80,
        'go.mod': 80,
        'pom.xml': 80,
        'build.gradle': 80,
        'build.gradle.kts': 80,
        'Gemfile': 70,
        'composer.json': 70,
        'CMakeLists.txt': 70,
        'Makefile': 60,
        '.sln': 80,  # Visual Studio solution
        '.csproj': 70,
        'tsconfig.json': 60,
        'webpack.config.js': 50,
        'vite.config.js': 50,
        'rollup.config.js': 50,
    }
    
    # Medium indicators - documentation
    MEDIUM_INDICATORS = {
        'README.md': 30,
        'README.rst': 30,
        'README.txt': 25,
        'README': 20,
        'Dockerfile': 40,
        'docker-compose.yml': 40,
        'docker-compose.yaml': 40,
        '.dockerignore': 20,
        'requirements.txt': 35,
        'setup.py': 60,
        'setup.cfg': 40,
        'environment.yml': 30,
        'Pipfile': 50,
        'poetry.lock': 50,
        '.env.example': 25,
        '.editorconfig': 15,
    }
    
    # Weak indicators - misc project files
    WEAK_INDICATORS = {
        'LICENSE': 15,
        'LICENSE.txt': 15,
        'LICENSE.md': 15,
        '.gitattributes': 10,
        '.prettierrc': 10,
        '.eslintrc': 10,
        '.eslintrc.js': 10,
        '.eslintrc.json': 10,
        'jest.config.js': 15,
        'pytest.ini': 15,
        '.travis.yml': 20,
        '.gitlab-ci.yml': 20,
        '.github': 25,  # Directory
        '.circleci': 20,  # Directory
    }
    
    # Negative indicators - these suggest NOT a project root
    NEGATIVE_INDICATORS = {
        'node_modules': -50,
        '__pycache__': -30,
        '.pytest_cache': -20,
        'venv': -40,
        'env': -40,
        '.venv': -40,
        'virtualenv': -40,
        'target': -30,  # Java/Rust build output
        'build': -25,
        'dist': -25,
        '.next': -30,
        '.cache': -20,
        'coverage': -20,
        '.coverage': -15,
    }

    # Score threshold to consider a directory as a project- keep at 50 or 75
    PROJECT_THRESHOLD = 75
    
    @classmethod
    def get_all_indicators(cls) -> Dict[str, float]:
        """Combine all indicator dictionaries."""
        all_indicators = {}
        all_indicators.update(cls.STRONG_INDICATORS)
        all_indicators.update(cls.MEDIUM_INDICATORS)
        all_indicators.update(cls.WEAK_INDICATORS)
        all_indicators.update(cls.NEGATIVE_INDICATORS)
        return all_indicators
    

def calculate_project_score(directory: Path) -> tuple[float, List[str], bool, int]:
    """
    Calculate a project score for a directory based on its direct children.
    scoring and directory analysis done

    Args:
        directory: Path to the directory to analyze

    Returns:
        Tuple of (score, list of indicators found, has_files, subdirectory_count)
    """
    score = 0.0
    indicators_found = []
    has_files = False
    subdir_count = 0
    all_indicators = ProjectHeuristics.get_all_indicators()

    try:
        for item in directory.iterdir():
            item_name = item.name

            # Check if this item is a project indicator
            if item_name in all_indicators:
                points = all_indicators[item_name]
                score += points
                indicators_found.append(f"{item_name} ({points:+.0f})")

            # Count files and subdirectories
            if item.is_file():
                has_files = True
            elif item.is_dir():
                subdir_count += 1

    except (PermissionError, FileNotFoundError):
        # Can't access directory
        return 0.0, [], False, 0

    return score, indicators_found, has_files, subdir_count


def calculate_project_score_fs(fs: FileSystemInterface, directory_path: str) -> tuple[float, List[str], bool, int]:
    """
    Calculate a project score for a directory using a file system interface.
    Works with both regular file systems and ZIP archives.

    Args:
        fs: File system interface to use
        directory_path: Path to the directory to analyze

    Returns:
        Tuple of (score, list of indicators found, has_files, subdirectory_count)
    """
    score = 0.0
    indicators_found = []
    has_files = False
    subdir_count = 0
    all_indicators = ProjectHeuristics.get_all_indicators()

    try:
        for item in fs.iterdir(directory_path):
            item_name = item.name

            # Check if this item is a project indicator
            if item_name in all_indicators:
                points = all_indicators[item_name]
                score += points
                indicators_found.append(f"{item_name} ({points:+.0f})")

            # Count files and subdirectories
            if item.is_file():
                has_files = True
            elif item.is_dir():
                subdir_count += 1

    except (PermissionError, FileNotFoundError):
        # Can't access directory
        return 0.0, [], False, 0

    return score, indicators_found, has_files, subdir_count

def Folder_traversal(root_path: str | Path) -> Dict[Path, DirectoryNode]:
    """
    Performs a breadth-first traversal starting at root_path.

    What it does:
    1. scores each directory at depth 1
    2. checks direct children for nested projects
        if 2+ subdirectories then not considered a project itself
        if 1 or 0 subprojects sub project absorbed into parent

    Passes
    pass 1 - BFS traversal, score directories, stop/ prune at projects
    pass 2 - count subprojects
    pass 3 - Apply nested project rules

    args:
        root_path - start directory

    returns:
        Dictionary mapping path to directory node.
    """
    #assign absolute path
    root = Path(root_path).resolve()

    if not root.exists():
        raise FileNotFoundError(f"The path {root} does not exist.")
    if not root.is_dir():
        raise ValueError(f"The path {root} is not a directory.")

    #store all directory nodes
    node_info: Dict[Path, DirectoryNode] = {}
    
    #initialize root node
    node_info[root] = DirectoryNode(path=root)
    
    # Queue for BFS
    queue = deque([root])

    #First pass 
    while queue:
        current_dir = queue.popleft()
        current_node = node_info[current_dir]

        #parent check not needed anymore as the nodes are not needed anymore

        #dfs
        score, indicators, has_files, subdir_count = calculate_project_score(current_dir)
        #populate the data into the class
        current_node.score = score
        current_node.indicators_found = indicators
        current_node.has_files = has_files

        # check project status
        is_project = score >= ProjectHeuristics.PROJECT_THRESHOLD
        current_node.is_project = is_project


        # check if project
        if is_project:
            # check if subdirectories contain projects
            try:
                for item in current_dir.iterdir():
                    # check if folder
                    if item.is_dir():
                        #Score this immediate child to detect nested projects
                        child_score, child_indicators, child_has_files, _ = calculate_project_score(item)
                        
                        # if potential project fill in details
                        if child_score >= ProjectHeuristics.PROJECT_THRESHOLD:
                            child_node = DirectoryNode(
                                path=item,
                                score=child_score,
                                indicators_found=child_indicators,
                                is_project=True,
                                has_files=child_has_files
                            )
                            node_info[item] = child_node
                            # NOT IN QUEUE
            except (PermissionError, FileNotFoundError):
                pass
        else:
            #not a project go through sub directory and add to queue
            try:
                for item in current_dir.iterdir():
                    if item.is_dir():
                        node_info[item] = DirectoryNode(path=item)
                        queue.append(item)
            except (PermissionError, FileNotFoundError):
                continue


    # Second pass: Count subprojects
    for path, node in node_info.items():
        if node.is_project:
            parent = path.parent
            if parent in node_info:
                node_info[parent].subproject_count += 1


    # Third pass - check and deal with sub projects
    for path, node in node_info.items():
        #If a directory has 2+ subprojects, it's NOT a project itself
        #sub projects are also already labelled as projects
        if node.subproject_count >= 2:
            node.is_project = False
        
        #If a directory has exactly 1 subproject, absorb it
        elif node.subproject_count == 1:
            if node.is_project:
                #Parent is project, mark child as not a project
                for child_path, child_node in node_info.items():
                    if child_path.parent == path and child_node.is_project:
                        child_node.is_project = False
                        break

    return node_info


def Folder_traversal_fs(root_path: str | Path) -> Dict[str, DirectoryNode]:
    """
    Performs a breadth-first traversal starting at root_path.
    Supports both regular file systems and ZIP archives.

    What it does:
    1. Detects if root_path is a ZIP file
    2. Creates appropriate file system interface
    3. Scores each directory at depth 1
    4. Checks direct children for nested projects
        if 2+ subdirectories then not considered a project itself
        if 1 or 0 subprojects sub project absorbed into parent

    Passes
    pass 1 - BFS traversal, score directories, stop/prune at projects
    pass 2 - count subprojects
    pass 3 - Apply nested project rules

    Args:
        root_path - start directory or ZIP file

    Returns:
        Dictionary mapping path string to directory node.
    """
    # Convert to Path object
    root = Path(root_path).resolve()

    if not root.exists():
        raise FileNotFoundError(f"The path {root} does not exist.")

    # Determine if we're dealing with a ZIP file
    if root.is_file() and root.suffix.lower() == '.zip':
        # Use ZIP file system
        fs = ZipFileSystem(root)
        root_str = ''  # Root of ZIP is empty string
        is_zip = True
    elif root.is_dir():
        # Use regular file system
        fs = RegularFileSystem()
        root_str = str(root)
        is_zip = False
    else:
        raise ValueError(f"The path {root} is neither a directory nor a ZIP file.")

    # Store all directory nodes (using string paths for compatibility)
    node_info: Dict[str, DirectoryNode] = {}

    # Initialize root node
    node_info[root_str] = DirectoryNode(path=root_str if is_zip else root)

    # Queue for BFS (stores string paths)
    queue = deque([root_str])

    # First pass - BFS traversal
    while queue:
        current_dir_str = queue.popleft()
        current_node = node_info[current_dir_str]

        # Score this directory
        score, indicators, has_files, subdir_count = calculate_project_score_fs(fs, current_dir_str)

        # Populate the data into the node
        current_node.score = score
        current_node.indicators_found = indicators
        current_node.has_files = has_files

        # Check project status
        is_project = score >= ProjectHeuristics.PROJECT_THRESHOLD
        current_node.is_project = is_project

        # Check if project
        if is_project:
            # Check if subdirectories contain projects
            try:
                for item in fs.iterdir(current_dir_str):
                    # Check if folder
                    if item.is_dir():
                        # Score this immediate child to detect nested projects
                        child_path_str = item.path_str
                        child_score, child_indicators, child_has_files, _ = calculate_project_score_fs(fs, child_path_str)

                        # If potential project fill in details
                        if child_score >= ProjectHeuristics.PROJECT_THRESHOLD:
                            child_node = DirectoryNode(
                                path=child_path_str,
                                score=child_score,
                                indicators_found=child_indicators,
                                is_project=True,
                                has_files=child_has_files
                            )
                            node_info[child_path_str] = child_node
                            # NOT IN QUEUE
            except (PermissionError, FileNotFoundError):
                pass
        else:
            # Not a project, go through sub directory and add to queue
            try:
                for item in fs.iterdir(current_dir_str):
                    if item.is_dir():
                        child_path_str = item.path_str
                        node_info[child_path_str] = DirectoryNode(path=child_path_str)
                        queue.append(child_path_str)
            except (PermissionError, FileNotFoundError):
                continue

    # Second pass: Count subprojects
    for path_str, node in node_info.items():
        if node.is_project:
            # Find parent
            if is_zip:
                # For ZIP paths, parent is everything before the last '/'
                if '/' in path_str:
                    parent_str = '/'.join(path_str.split('/')[:-1])
                else:
                    parent_str = ''  # Root
            else:
                # For regular paths
                parent_path = Path(path_str).parent
                parent_str = str(parent_path)

            # Only increment if parent is different from current node (avoid root counting itself)
            if parent_str in node_info and parent_str != path_str:
                node_info[parent_str].subproject_count += 1

    # Third pass - check and deal with sub projects
    for path_str, node in node_info.items():
        # If a directory has 2+ subprojects, it's NOT a project itself
        if node.subproject_count >= 2:
            node.is_project = False

        # If a directory has exactly 1 subproject, absorb it
        elif node.subproject_count == 1:
            if node.is_project:
                # Parent is project, mark child as not a project
                for child_path_str, child_node in node_info.items():
                    # Check if this is a direct child
                    if is_zip:
                        # For ZIP paths
                        if '/' in child_path_str:
                            child_parent = '/'.join(child_path_str.split('/')[:-1])
                        else:
                            child_parent = ''
                        if child_parent == path_str and child_node.is_project:
                            child_node.is_project = False
                            break
                    else:
                        # For regular paths
                        if Path(child_path_str).parent == Path(path_str) and child_node.is_project:
                            child_node.is_project = False
                            break

    # Clean up ZIP file if necessary
    if is_zip:
        fs.close()

    return node_info


# informal testing
if __name__ == "__main__":
    import sys

    current_dir = Path(__file__).parent

    # Demo: Test with regular directory
    print("="*80)
    print("DEMO 1: Regular Directory Traversal")
    print("="*80)

    test_path = current_dir / "../tests/backend_test/Test-traversal"
    test_path = test_path.resolve()

    if test_path.exists():
        print(f"\nAnalyzing regular directory: {test_path}")
        print(f"Project threshold: {ProjectHeuristics.PROJECT_THRESHOLD} points\n")

        results = Folder_traversal(test_path)

        print(f"Total directories discovered: {len(results)}")
        project_count = sum(1 for n in results.values() if n.is_project)
        print(f"Projects found: {project_count}\n")

    # Demo: Test with ZIP file
    print("\n" + "="*80)
    print("DEMO 2: ZIP File Traversal (New Feature)")
    print("="*80)

    zip_test_dir = current_dir / "../tests/backend_test/Test-zip-traversal"

    if zip_test_dir.exists():
        zip_files = list(zip_test_dir.glob("*.zip"))

        if zip_files:
            # Test with the first available ZIP file
            zip_path = zip_files[0]
            print(f"\nAnalyzing ZIP file: {zip_path.name}")
            print(f"Full path: {zip_path}")
            print(f"Project threshold: {ProjectHeuristics.PROJECT_THRESHOLD} points\n")

            try:
                results = Folder_traversal_fs(zip_path)

                print(f"Total directories discovered: {len(results)}")
                project_count = sum(1 for n in results.values() if n.is_project)
                print(f"Projects found: {project_count}\n")

                print("Detected projects:")
                for path_str, node in results.items():
                    if node.is_project:
                        print(f"  ✓ {path_str or '(root)'} - Score: {node.score}")

            except Exception as e:
                print(f"Error processing ZIP: {e}")
        else:
            print("\nNo ZIP files found. Run create_test_zip.py first.")
    else:
        print(f"\nZIP test directory not found: {zip_test_dir}")

    print("\n" + "="*80)
    print("Usage Examples:")
    print("="*80)
    print("""
# For regular directories (both functions work):
from backend.traversal import Folder_traversal, Folder_traversal_fs

results = Folder_traversal("/path/to/directory")
# OR
results = Folder_traversal_fs("/path/to/directory")

# For ZIP files (use Folder_traversal_fs):
results = Folder_traversal_fs("/path/to/file.zip")

# Results are dictionaries mapping paths to DirectoryNode objects
for path, node in results.items():
    if node.is_project:
        print(f"Project found: {path}")
        print(f"  Score: {node.score}")
        print(f"  Indicators: {node.indicators_found}")
""")



