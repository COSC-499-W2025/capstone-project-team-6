from pathlib import Path
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class DirectoryNode:
    """
    Represents a directory in the file system with project detection metadata.

    path - stores the path
    is_project - tells whether the current node/directory is considered as a project or a container
    score - hueristic score on the current node for being a project
    indicators_found - shows the list of positive and negative indicators to calculate the points
    subpoject_count - is the number of subprojects to see if the current node needs to reject its project status and pass it onto the sub folders inside it
    has_files - general check

    """
    path: Path
    is_project: bool = False
    score: float = 0.0
    indicators_found: List[str] = field(default_factory=list)
    subproject_count: int = 0
    has_files: bool = False
    
    def __repr__(self):
        return (f"DirectoryNode(path={self.path.name}, is_project={self.is_project}, "
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
    from .session import get_session
    session = get_session()
    if not session["logged_in"]:
        raise PermissionError("Please login first")
        
    root = Path(root_path)
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

def dfs_for_file(path: Union[str, Path]) -> bool:
    """
    Does a Depth first search of depth =1
    returns true if there is file in the sub items of the directory

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


# informal testing 
if __name__ == "__main__":
    current_dir = Path(__file__).parent      # directory where this file is
    test_path = current_dir / "../tests/backend_test/Test-traversal"
    test_path= test_path.resolve()

    if not test_path.exists():
        print(f"Test path {test_path} not found. Run test_traversal.py first to create it.")
        exit(1)
    
    print(f"Analyzing: {test_path}")
    print(f"Project threshold: {ProjectHeuristics.PROJECT_THRESHOLD} points\n")
    
    results = Folder_traversal(test_path)
    
    print(f"\n{'='*80}")
    print(f"OPTIMIZATION RESULTS")
    print(f"{'='*80}\n")
    print(f"Total directories discovered: {len(results)}")



