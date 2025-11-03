from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.analysis.project_analyzer import FileClassifier

# Use absolute path based on script location
SCRIPT_DIR = Path(__file__).parent
ZIP = SCRIPT_DIR / "Test-zip-traversal" / "python_project.zip"
PROJECT = ""  # Empty string because root of ZIP is the project root

print(f"Looking for ZIP: {ZIP}")
print(f"ZIP exists: {ZIP.exists()}\n")

with FileClassifier(ZIP) as c:
    result = c.classify_project(PROJECT)
    print(f"Found {result['stats']['total_files']} files!")
    print(f"Languages: {list(result['files']['code'].keys())}")
    print(f"Tests: {len(result['files']['tests'])}")
    print(f"Docs: {len(result['files']['docs'])}")