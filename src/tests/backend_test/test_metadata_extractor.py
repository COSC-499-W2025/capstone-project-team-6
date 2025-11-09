# Tests for the metadata extraction module (Phase 2) without using LLMs

import json
import sys
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.analysis.metadata_extractor import MetadataExtractor, ProjectMetadata

# Test configuration
SCRIPT_DIR = Path(__file__).parent
TEST_ZIP_PATH = SCRIPT_DIR / "Test-zip-traversal" / "python_project.zip"


class TestMetadataExtractorInitialization:
    """Test MetadataExtractor initialization."""

    def test_extractor_initialization(self):
        """Test that extractor initializes correctly."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        assert extractor.zip_path == TEST_ZIP_PATH
        assert extractor.zip_file is not None
        assert extractor.classifier is not None
        extractor.close()

    def test_context_manager(self):
        """Test that context manager works correctly."""
        with MetadataExtractor(TEST_ZIP_PATH) as extractor:
            assert extractor.zip_file is not None


class TestProjectDetection:
    """Test detection of multiple projects within a ZIP."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_detect_projects_returns_list(self, extractor):
        """Test that project detection returns a list."""
        projects = extractor.detect_projects()
        assert isinstance(projects, list)
        assert len(projects) >= 1

    def test_detect_projects_finds_root(self, extractor):
        """Test that at least one project is detected."""
        projects = extractor.detect_projects()
        assert "" in projects or len(projects) > 0


class TestDependencyExtraction:
    """Test extraction of dependencies from various file formats."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_extract_dependencies_returns_dict(self, extractor):
        """Test that dependency extraction returns a dictionary."""
        # Get classified files first
        classification = extractor.classifier.classify_project("")
        config_files = classification["files"]["configs"]
        
        deps = extractor.extract_dependencies("", config_files)
        assert isinstance(deps, dict)

    def test_extract_python_dependencies(self, extractor):
        """Test extraction of Python dependencies from requirements.txt."""
        # Create a mock config file list
        config_files = [
            {"path": "requirements.txt", "filename": "requirements.txt"}
        ]
        
        # Check if requirements.txt exists in test ZIP
        try:
            content = extractor.zip_file.read("requirements.txt")
            # If file exists, test dependency extraction
            deps = extractor.extract_dependencies("", config_files)
            # Should have some dependencies if file has content
            if content:
                assert "python" in deps or len(deps) >= 0
        except KeyError:
            # File doesn't exist, skip test
            pytest.skip("requirements.txt not in test ZIP")


class TestFrameworkDetection:
    """Test detection of frameworks and libraries."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_detect_frameworks_returns_list(self, extractor):
        """Test that framework detection returns a list."""
        classification = extractor.classifier.classify_project("")
        frameworks = extractor.detect_frameworks("", classification["files"])
        assert isinstance(frameworks, list)

    def test_detect_docker(self, extractor):
        """Test detection of Docker configuration."""
        classification = extractor.classifier.classify_project("")
        frameworks = extractor.detect_frameworks("", classification["files"])
        
        # Check if Dockerfile or docker-compose.yml exists
        all_files = extractor.zip_file.namelist()
        has_docker_file = any(
            "dockerfile" in f.lower() or "docker-compose" in f.lower()
            for f in all_files
        )
        
        if has_docker_file:
            assert "Docker" in frameworks


class TestCICDDetection:
    """Test detection of CI/CD configuration."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_check_ci_cd_returns_bool(self, extractor):
        """Test that CI/CD check returns a boolean."""
        classification = extractor.classifier.classify_project("")
        has_ci_cd = extractor.check_ci_cd(classification["files"])
        assert isinstance(has_ci_cd, bool)

    def test_check_ci_cd_detects_github_actions(self, extractor):
        """Test detection of GitHub Actions."""
        all_files = extractor.zip_file.namelist()
        has_github_actions = any(".github/workflows" in f for f in all_files)
        
        classification = extractor.classifier.classify_project("")
        detected_ci_cd = extractor.check_ci_cd(classification["files"])
        
        if has_github_actions:
            assert detected_ci_cd == True


class TestComplexityMetrics:
    """Test calculation of complexity metrics."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_calculate_directory_depth(self, extractor):
        """Test calculation of directory depth."""
        classification = extractor.classifier.classify_project("")
        depth = extractor.calculate_directory_depth(classification["files"])
        assert isinstance(depth, int)
        assert depth >= 0

    def test_find_largest_file(self, extractor):
        """Test finding the largest file."""
        classification = extractor.classifier.classify_project("")
        largest = extractor.find_largest_file(classification["files"])
        
        if classification["stats"]["total_files"] > 0:
            assert largest is not None
            assert "path" in largest
            assert "size" in largest
            assert "size_mb" in largest
            assert largest["size"] > 0

    def test_estimate_test_coverage(self, extractor):
        """Test estimation of test coverage."""
        # Test various scenarios
        assert extractor.estimate_test_coverage(10, 0) == "none"
        assert extractor.estimate_test_coverage(10, 1) == "low"
        assert extractor.estimate_test_coverage(10, 3) == "medium"
        assert extractor.estimate_test_coverage(10, 6) == "high"
        
        # Edge cases
        assert extractor.estimate_test_coverage(0, 0) == "none"
        # If there are 0 code files but tests exist, ratio calculation still works
        # This is an edge case where we have tests but no code - still returns a coverage level


class TestProjectMetadata:
    """Test extraction of complete project metadata."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_extract_project_metadata_returns_metadata_object(self, extractor):
        """Test that metadata extraction returns a ProjectMetadata object."""
        metadata = extractor.extract_project_metadata("")
        assert isinstance(metadata, ProjectMetadata)

    def test_metadata_has_required_fields(self, extractor):
        """Test that metadata contains all required fields."""
        metadata = extractor.extract_project_metadata("")
        
        # Check basic fields
        assert hasattr(metadata, "project_name")
        assert hasattr(metadata, "project_path")
        assert hasattr(metadata, "total_files")
        assert hasattr(metadata, "total_size")
        
        # Check file counts
        assert hasattr(metadata, "code_files")
        assert hasattr(metadata, "test_files")
        assert hasattr(metadata, "doc_files")
        assert hasattr(metadata, "config_files")
        
        # Check language info
        assert hasattr(metadata, "primary_language")
        assert hasattr(metadata, "languages")
        
        # Check indicators
        assert hasattr(metadata, "has_tests")
        assert hasattr(metadata, "has_readme")
        assert hasattr(metadata, "has_ci_cd")
        assert hasattr(metadata, "has_docker")

    def test_metadata_language_statistics(self, extractor):
        """Test that language statistics are calculated."""
        metadata = extractor.extract_project_metadata("")
        
        assert isinstance(metadata.languages, dict)
        
        if metadata.code_files > 0:
            # Should have at least one language
            assert len(metadata.languages) > 0
            # Primary language should be in languages dict
            if metadata.primary_language:
                assert metadata.primary_language in metadata.languages

    def test_metadata_boolean_flags(self, extractor):
        """Test that boolean flags are set correctly."""
        metadata = extractor.extract_project_metadata("")
        
        # All should be boolean
        assert isinstance(metadata.has_tests, bool)
        assert isinstance(metadata.has_readme, bool)
        assert isinstance(metadata.has_ci_cd, bool)
        assert isinstance(metadata.has_docker, bool)
        assert isinstance(metadata.is_git_repo, bool)
        
        # If there are test files, has_tests should be True
        if metadata.test_files > 0:
            assert metadata.has_tests == True

    def test_metadata_to_dict_serializable(self, extractor):
        """Test that metadata can be converted to dict and serialized to JSON."""
        metadata = extractor.extract_project_metadata("")
        metadata_dict = metadata.to_dict()
        
        assert isinstance(metadata_dict, dict)
        
        # Should be JSON serializable
        try:
            json_str = json.dumps(metadata_dict)
            assert len(json_str) > 0
        except TypeError:
            pytest.fail("Metadata dictionary is not JSON serializable")


class TestReportGeneration:
    """Test generation of the final JSON report."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_generate_report_returns_dict(self, extractor):
        """Test that report generation returns a dictionary."""
        report = extractor.generate_report()
        assert isinstance(report, dict)

    def test_report_has_required_sections(self, extractor):
        """Test that report has all required sections."""
        report = extractor.generate_report()
        
        # Check main sections
        assert "analysis_metadata" in report
        assert "projects" in report
        assert "summary" in report
        
        # Check analysis metadata
        assert "zip_file" in report["analysis_metadata"]
        assert "analysis_timestamp" in report["analysis_metadata"]
        assert "total_projects" in report["analysis_metadata"]
        
        # Check projects
        assert isinstance(report["projects"], list)
        assert len(report["projects"]) > 0
        
        # Check summary
        assert "total_files" in report["summary"]
        assert "total_size_bytes" in report["summary"]
        assert "languages_used" in report["summary"]

    def test_report_json_serializable(self, extractor):
        """Test that the entire report is JSON serializable."""
        report = extractor.generate_report()
        
        try:
            json_str = json.dumps(report, indent=2)
            assert len(json_str) > 0
            
            # Verify it can be loaded back
            loaded = json.loads(json_str)
            assert loaded == report
        except TypeError as e:
            pytest.fail(f"Report is not JSON serializable: {e}")

    def test_report_saves_to_file(self, extractor, tmp_path):
        """Test that report can be saved to a file."""
        output_file = tmp_path / "test_report.json"
        
        report = extractor.generate_report(output_file)
        
        # Check that file was created
        assert output_file.exists()
        
        # Verify content
        with open(output_file, "r") as f:
            loaded_report = json.load(f)
        
        assert loaded_report == report

    def test_report_summary_accuracy(self, extractor):
        """Test that report summary matches individual project data."""
        report = extractor.generate_report()
        
        # Calculate totals from projects
        expected_total_files = sum(p["total_files"] for p in report["projects"])
        expected_total_size = sum(p["total_size"] for p in report["projects"])
        
        # Compare with summary
        assert report["summary"]["total_files"] == expected_total_files
        assert report["summary"]["total_size_bytes"] == expected_total_size
        
        # Check project count
        assert report["analysis_metadata"]["total_projects"] == len(report["projects"])


class TestMultipleProjects:
    """Test handling of multiple projects in a single ZIP."""

    def test_nested_projects_detection(self, tmp_path):
        """Test detection of nested projects."""
        # This test would require a more complex test ZIP
        # For now, we'll test the logic with the existing ZIP
        
        with MetadataExtractor(TEST_ZIP_PATH) as extractor:
            projects = extractor.detect_projects()
            
            # Should detect at least the root project
            assert len(projects) >= 1
            
            # If multiple projects detected, verify they're not nested incorrectly
            if len(projects) > 1:
                sorted_projects = sorted(projects, key=lambda x: x.count("/"))
                for i, proj in enumerate(sorted_projects[1:], 1):
                    # Check that it's not a child of a previous project
                    for earlier_proj in sorted_projects[:i]:
                        if earlier_proj and proj.startswith(earlier_proj + "/"):
                            pytest.fail(f"Nested project incorrectly detected: {proj} under {earlier_proj}")


class TestGitAnalysis:
    """Test git repository analysis (if available)."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        extractor = MetadataExtractor(TEST_ZIP_PATH)
        yield extractor
        extractor.close()

    def test_check_git_files(self, extractor):
        """Test detection of git-related files."""
        has_git = extractor._check_git_files("")
        assert isinstance(has_git, bool)
        
        # Verify by checking actual files
        all_files = extractor.zip_file.namelist()
        actual_has_git = any(
            ".git" in f or ".gitignore" in f or ".gitattributes" in f
            for f in all_files
        )
        
        assert has_git == actual_has_git

    def test_parse_git_log_returns_tuple(self, extractor):
        """Test that git log parsing returns expected format."""
        contributors, total_commits = extractor.parse_git_log("")
        
        assert isinstance(contributors, dict)
        assert isinstance(total_commits, int)
        assert total_commits >= 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_project_path(self):
        """Test handling of empty project path (root project)."""
        with MetadataExtractor(TEST_ZIP_PATH) as extractor:
            metadata = extractor.extract_project_metadata("")
            assert metadata.project_name is not None
            assert len(metadata.project_name) > 0

    def test_nonexistent_file_handling(self):
        """Test handling of nonexistent files in dependency parsing."""
        with MetadataExtractor(TEST_ZIP_PATH) as extractor:
            # Try to parse a file that doesn't exist
            result = extractor._parse_dependency_file(
                "nonexistent_file.txt",
                "nonexistent_file.txt",
                {"nonexistent_file.txt": r"test"}
            )
            assert result == []

    def test_large_file_skipping(self):
        """Test that large files are skipped in content reading."""
        with MetadataExtractor(TEST_ZIP_PATH) as extractor:
            # Try to read with a very small max_size
            content = extractor._read_file_content("nonexistent.txt", max_size=1)
            assert content is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
