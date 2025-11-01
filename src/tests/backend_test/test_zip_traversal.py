"""
Tests for ZIP file traversal functionality.
Tests the Folder_traversal_fs function with various ZIP file structures.
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.traversal import Folder_traversal_fs, ProjectHeuristics


class TestZipTraversal:
    """Test suite for ZIP file traversal."""

    @classmethod
    def setup_class(cls):
        """Set up test fixtures."""
        cls.test_zip_dir = Path(__file__).parent / "Test-zip-traversal"
        if not cls.test_zip_dir.exists():
            pytest.skip("Test ZIP files not found. Run create_test_zip.py first.")

    def test_simple_project_zip(self):
        """Test traversal of a simple project ZIP file."""
        zip_path = self.test_zip_dir / "simple_project.zip"
        if not zip_path.exists():
            pytest.skip("simple_project.zip not found")

        results = Folder_traversal_fs(zip_path)

        # Check that root was detected as a project
        assert '' in results, "Root directory should be in results"
        root_node = results['']

        # Root should be detected as a project (has package.json, README.md, .gitignore)
        assert root_node.is_project, "Root should be detected as a project"
        assert root_node.score >= ProjectHeuristics.PROJECT_THRESHOLD

        # Check that indicators were found
        assert len(root_node.indicators_found) > 0
        indicator_names = ' '.join(root_node.indicators_found)
        assert 'package.json' in indicator_names

        # src and tests directories should not be traversed (root is a project)
        assert 'src' not in results or not results['src'].is_project
        assert 'tests' not in results or not results['tests'].is_project

    def test_nested_projects_zip(self):
        """Test traversal of a ZIP with multiple nested projects."""
        zip_path = self.test_zip_dir / "nested_projects.zip"
        if not zip_path.exists():
            pytest.skip("nested_projects.zip not found")

        results = Folder_traversal_fs(zip_path)

        # Root should have 3 subprojects, so it should NOT be a project itself
        root_node = results['']
        assert root_node.subproject_count == 3
        assert not root_node.is_project, "Root with 3 subprojects should not be a project"

        # Each project should be detected
        assert 'projectA' in results, "projectA should be found"
        assert 'projectB' in results, "projectB should be found"
        assert 'projectC' in results, "projectC should be found"

        # Each project should be marked as a project
        assert results['projectA'].is_project, "projectA should be a project"
        assert results['projectB'].is_project, "projectB should be a project"
        assert results['projectC'].is_project, "projectC should be a project"

        # Children of projects should not be further traversed
        assert 'projectA/src' not in results
        assert 'projectB/src' not in results
        assert 'projectC/src' not in results

    def test_python_project_zip(self):
        """Test traversal of a Python project ZIP."""
        zip_path = self.test_zip_dir / "python_project.zip"
        if not zip_path.exists():
            pytest.skip("python_project.zip not found")

        results = Folder_traversal_fs(zip_path)

        # Root should be detected as a Python project
        root_node = results['']
        assert root_node.is_project, "Root should be detected as a Python project"

        # Check for Python-specific indicators
        indicator_names = ' '.join(root_node.indicators_found)
        assert any(ind in indicator_names for ind in ['pyproject.toml', 'setup.py', 'requirements.txt'])

        # Check that score is high enough
        assert root_node.score >= ProjectHeuristics.PROJECT_THRESHOLD

    def test_non_project_zip(self):
        """Test traversal of a ZIP that is NOT a project."""
        zip_path = self.test_zip_dir / "non_project.zip"
        if not zip_path.exists():
            pytest.skip("non_project.zip not found")

        results = Folder_traversal_fs(zip_path)

        # Root should NOT be detected as a project
        root_node = results['']
        assert not root_node.is_project, "Root should not be detected as a project"
        assert root_node.score < ProjectHeuristics.PROJECT_THRESHOLD

        # All subdirectories should be traversed since root is not a project
        assert 'documents' in results
        assert 'images' in results
        assert 'data' in results

    def test_mixed_structure_zip(self):
        """Test traversal of a ZIP with mixed project and non-project content."""
        zip_path = self.test_zip_dir / "mixed_structure.zip"
        if not zip_path.exists():
            pytest.skip("mixed_structure.zip not found")

        results = Folder_traversal_fs(zip_path)

        # Root should not be a strong project
        root_node = results['']

        # Should have 2 subprojects
        assert root_node.subproject_count == 2

        # webapp and api should be detected as projects
        assert 'webapp' in results, "webapp should be found"
        assert 'api' in results, "api should be found"
        assert results['webapp'].is_project, "webapp should be a project"
        assert results['api'].is_project, "api should be a project"

        # docs and misc should be present but not projects
        assert 'docs' in results
        assert 'misc' in results
        assert not results['docs'].is_project
        assert not results['misc'].is_project

    def test_zip_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent ZIP."""
        fake_path = self.test_zip_dir / "nonexistent.zip"
        with pytest.raises(FileNotFoundError):
            Folder_traversal_fs(fake_path)

    def test_directory_node_properties(self):
        """Test DirectoryNode properties work correctly for ZIP entries."""
        zip_path = self.test_zip_dir / "simple_project.zip"
        if not zip_path.exists():
            pytest.skip("simple_project.zip not found")

        results = Folder_traversal_fs(zip_path)
        root_node = results['']

        # Test path_str property
        assert isinstance(root_node.path_str, str)

        # Test name property
        assert isinstance(root_node.name, str)

        # Test score and indicators
        assert isinstance(root_node.score, float)
        assert isinstance(root_node.indicators_found, list)

    def test_nested_project_absorption(self):
        """Test that a project with exactly 1 subproject absorbs it."""
        # For this test, we'd need a specific ZIP structure
        # The nested_projects.zip has 3 subprojects, so none get absorbed
        # This test verifies the absorption logic works

        zip_path = self.test_zip_dir / "nested_projects.zip"
        if not zip_path.exists():
            pytest.skip("nested_projects.zip not found")

        results = Folder_traversal_fs(zip_path)

        # Since root has 3 subprojects, none should be absorbed
        # All 3 projects should remain as projects
        project_count = sum(1 for node in results.values() if node.is_project)
        assert project_count == 3, "All 3 projects should remain"


class TestFileSystemInterfaces:
    """Test the file system abstraction interfaces."""

    def test_zip_filesystem_iterdir(self):
        """Test that ZipFileSystem.iterdir works correctly."""
        from backend.traversal import ZipFileSystem

        test_zip_dir = Path(__file__).parent / "Test-zip-traversal"
        zip_path = test_zip_dir / "simple_project.zip"

        if not zip_path.exists():
            pytest.skip("simple_project.zip not found")

        fs = ZipFileSystem(zip_path)

        # Get root entries
        entries = list(fs.iterdir(''))
        assert len(entries) > 0, "Should have entries in root"

        # Check that entries have expected attributes
        for entry in entries:
            assert hasattr(entry, 'name')
            assert hasattr(entry, 'path_str')
            assert hasattr(entry, 'is_file')
            assert hasattr(entry, 'is_dir')

        # Check specific files exist
        entry_names = [e.name for e in entries]
        assert 'package.json' in entry_names
        assert 'README.md' in entry_names

        fs.close()

    def test_regular_filesystem_compatibility(self):
        """Test that RegularFileSystem works with existing test directory."""
        from backend.traversal import RegularFileSystem

        test_dir = Path(__file__).parent / "Test-traversal"
        if not test_dir.exists():
            pytest.skip("Test-traversal directory not found")

        fs = RegularFileSystem()

        # Get entries from test directory
        entries = list(fs.iterdir(str(test_dir)))
        assert len(entries) > 0, "Should have entries"

        # Check that entries work correctly
        for entry in entries:
            assert hasattr(entry, 'name')
            assert hasattr(entry, 'path_str')


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
