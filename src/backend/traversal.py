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
    

#how does this fit with dfs???
def calculate_project_score(directory: Path) -> tuple[float, List[str]]:
    """
    Calculate a project score for a directory based on its immediate children.
    
    Args:
        directory: Path to the directory to score
        
    Returns:
        Tuple of (score, list of indicators found)
    """
    score = 0.0
    indicators_found = []
    all_indicators = ProjectHeuristics.get_all_indicators()
    
    try:
        for item in directory.iterdir():
            item_name = item.name
            
            # Check if this item is an indicator
            if item_name in all_indicators:
                points = all_indicators[item_name]
                score += points
                indicators_found.append(f"{item_name} ({points:+.0f})")
                
    except (PermissionError, FileNotFoundError):
        # Can't access directory
        return 0.0, []
    
    return score, indicators_found

def Folder_traversal(root_path: str | Path):
    """
    Performs a breadth-first traversal starting at root_path.
    checks if it contains files using dfs_for_file().
    returns a dictionary where each directory path maps to its 'project' boolean.
    """
    root = Path(root_path)

    if not root.exists():
        raise FileNotFoundError(f"The path {root} does not exist.")
    if not root.is_dir():
        raise ValueError(f"The path {root} is not a directory.")

    #replace with this with a class instead of a dictionary
    #dictionary to store directory info
    node_info = {root: {"project": False}}

    #Queue for BFS
    queue = deque([root])

    while queue:
        current_dir = queue.popleft()

        parent= current_dir.parent
        # if parent node is a project remove from queue
        if parent in node_info and node_info[parent]["project"]:
            # 2 checks since root wont have a parent and node_info will be false
            continue


        #dfs
        has_file = dfs_for_file(current_dir)
        node_info[current_dir]["project"] = has_file

        if has_file:
            #no need to check for the rest of the sub items
            continue

        try:
            for item in current_dir.iterdir():
                #if dir (extra check) add to queue with project false
                if item.is_dir():
                    #initialize child node with default project=False
                    node_info[item] = {"project": False}
                    queue.append(item)
        except (PermissionError, FileNotFoundError):
            continue  # Skip folders that can't be read

    return node_info




def dfs_for_file(path: str | Path) -> tuple[bool, int]:
    """
    Does a Depth first search of depth =1
    returns:
        Tuple of (has_files, subdirectory_count)
    

    """
    p = Path(path)

    has_files= False
    #check for sub dir
    subdir_count = 0

    #proceed if it’s a directory
    if not p.is_dir():
        raise ValueError(f"The path {p} is not a directory.")

    #Iterate over immediate children
    try:
        for item in p.iterdir():
            if item.is_file():
                has_files= True  # found at least one file
            elif item.is_dir():
                subdir_count+=1
    
    except (PermissionError,FileNotFoundError):
        # Can't access folder contents; treat as empty
        pass

    return has_files, subdir_count


# informal testing 
if __name__ == "__main__":
    current_dir = Path(__file__).parent      # directory where this file is
    path = current_dir / "Test-traversal"  
    results = Folder_traversal(path)
    for directory, info in results.items():
        print(f"{directory} → project: {info['project']}")


