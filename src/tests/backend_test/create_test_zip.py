"""
Script to create test ZIP files for testing ZIP traversal functionality.
Creates ZIP files with various project structures and indicators.
"""

import zipfile
from pathlib import Path


def create_simple_project_zip(output_path: Path):
    """Create a ZIP file with a simple project structure."""
    with zipfile.ZipFile(output_path, "w") as zf:
        # Root level - should be detected as a project
        zf.writestr("package.json", '{"name": "test-project", "version": "1.0.0"}')
        zf.writestr("README.md", "# Test Project")
        zf.writestr(".gitignore", "node_modules/\n.env")

        # Source directory
        zf.writestr("src/", "")  # Directory entry
        zf.writestr("src/index.js", 'console.log("Hello World");')
        zf.writestr("src/utils.js", "export function helper() {}")

        # Test directory
        zf.writestr("tests/", "")
        zf.writestr("tests/test_index.js", 'describe("index", () => {});')

    print(f"Created simple project ZIP: {output_path}")


def create_nested_projects_zip(output_path: Path):
    """Create a ZIP file with nested project structures."""
    with zipfile.ZipFile(output_path, "w") as zf:
        # Root - not a strong project
        zf.writestr("README.md", "# Monorepo")

        # Project A - should be detected
        zf.writestr("projectA/", "")
        zf.writestr("projectA/package.json", '{"name": "project-a"}')
        zf.writestr("projectA/tsconfig.json", "{}")
        zf.writestr("projectA/README.md", "# Project A")
        zf.writestr("projectA/src/", "")
        zf.writestr("projectA/src/main.ts", 'console.log("A");')

        # Project B - should be detected
        zf.writestr("projectB/", "")
        zf.writestr("projectB/pyproject.toml", '[tool.poetry]\nname = "project-b"')
        zf.writestr("projectB/README.md", "# Project B")
        zf.writestr("projectB/src/", "")
        zf.writestr("projectB/src/__init__.py", "")
        zf.writestr("projectB/src/main.py", 'print("Hello from B")')

        # Project C - should be detected
        zf.writestr("projectC/", "")
        zf.writestr("projectC/Cargo.toml", '[package]\nname = "project-c"')
        zf.writestr("projectC/README.md", "# Project C")
        zf.writestr("projectC/src/", "")
        zf.writestr("projectC/src/main.rs", "fn main() {}")

    print(f"Created nested projects ZIP: {output_path}")


def create_python_project_zip(output_path: Path):
    """Create a ZIP file with a Python project structure."""
    with zipfile.ZipFile(output_path, "w") as zf:
        # Strong Python project indicators
        zf.writestr("pyproject.toml", '[tool.poetry]\nname = "my-project"')
        zf.writestr("setup.py", "from setuptools import setup")
        zf.writestr("requirements.txt", "pytest>=7.0.0\nrequests>=2.28.0")
        zf.writestr("README.md", "# My Python Project")
        zf.writestr("LICENSE", "MIT License")

        # Source code
        zf.writestr("src/", "")
        zf.writestr("src/__init__.py", "")
        zf.writestr("src/main.py", "def main():\n    pass")
        zf.writestr("src/utils/", "")
        zf.writestr("src/utils/__init__.py", "")
        zf.writestr("src/utils/helpers.py", "def helper(): pass")

        # Tests
        zf.writestr("tests/", "")
        zf.writestr("tests/__init__.py", "")
        zf.writestr("tests/test_main.py", "def test_main(): pass")

        # Negative indicators (should not affect project status)
        zf.writestr("__pycache__/", "")
        zf.writestr("venv/", "")

    print(f"Created Python project ZIP: {output_path}")


def create_non_project_zip(output_path: Path):
    """Create a ZIP file that should NOT be detected as a project."""
    with zipfile.ZipFile(output_path, "w") as zf:
        # Just some random files, no project indicators
        zf.writestr("documents/", "")
        zf.writestr("documents/notes.txt", "Some notes")
        zf.writestr("documents/report.txt", "A report")

        zf.writestr("images/", "")
        zf.writestr("images/photo1.txt", "fake image")
        zf.writestr("images/photo2.txt", "fake image")

        zf.writestr("data/", "")
        zf.writestr("data/data.csv", "col1,col2\n1,2")

    print(f"Created non-project ZIP: {output_path}")


def create_mixed_structure_zip(output_path: Path):
    """Create a ZIP with mixed content - some projects, some not."""
    with zipfile.ZipFile(output_path, "w") as zf:
        # Root level - just documentation
        zf.writestr("README.md", "# Archive Contents")

        # A project folder
        zf.writestr("webapp/", "")
        zf.writestr("webapp/package.json", '{"name": "webapp"}')
        zf.writestr("webapp/webpack.config.js", "module.exports = {}")
        zf.writestr("webapp/src/", "")
        zf.writestr("webapp/src/app.js", "const app = {};")

        # A non-project folder
        zf.writestr("docs/", "")
        zf.writestr("docs/manual.txt", "User manual")
        zf.writestr("docs/guide.txt", "Installation guide")

        # Another project folder
        zf.writestr("api/", "")
        zf.writestr("api/go.mod", "module example.com/api")
        zf.writestr("api/main.go", "package main")
        zf.writestr("api/README.md", "# API Server")

        # Random files
        zf.writestr("misc/", "")
        zf.writestr("misc/random.txt", "Random content")

    print(f"Created mixed structure ZIP: {output_path}")


if __name__ == "__main__":
    # Get the test directory
    current_dir = Path(__file__).parent
    test_zip_dir = current_dir / "Test-zip-traversal"

    # Create the directory if it doesn't exist
    test_zip_dir.mkdir(exist_ok=True)

    print(f"Creating test ZIP files in: {test_zip_dir}\n")

    # Create all test ZIP files
    create_simple_project_zip(test_zip_dir / "simple_project.zip")
    create_nested_projects_zip(test_zip_dir / "nested_projects.zip")
    create_python_project_zip(test_zip_dir / "python_project.zip")
    create_non_project_zip(test_zip_dir / "non_project.zip")
    create_mixed_structure_zip(test_zip_dir / "mixed_structure.zip")

    print(f"\nAll test ZIP files created successfully!")
    print(f"Location: {test_zip_dir}")
