import pytest
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.analysis.project_analyzer import FileClassifier


# Test configuration - change in accordance to project being tested. 
# in this case the root of zip is the project, all asserts are specific to the python zip test that was created during the zip folder traversal testing
SCRIPT_DIR = Path(__file__).parent
TEST_ZIP_PATH = SCRIPT_DIR / "Test-zip-traversal" / "python_project.zip"
PROJECT_PATH = ""  # Root of ZIP is the project

#first test all the individual methods

class TestFileClassifierInitialization:
    """Test FileClassifier initialization and setup"""
    
    def test_zip_file_exists(self):
        """Test that the test ZIP file exists."""
        assert TEST_ZIP_PATH.exists(), f"Test ZIP not found at {TEST_ZIP_PATH}"
    
    def test_classifier_initialization(self):
        """Test that classifier initializes correctly."""
        classifier = FileClassifier(TEST_ZIP_PATH)
        assert classifier.zip_path == TEST_ZIP_PATH
        assert classifier.zip_file is not None
        classifier.close()
    
    def test_context_manager(self):
        """Test that context manager works correctly."""
        with FileClassifier(TEST_ZIP_PATH) as classifier:
            assert classifier.zip_file is not None
        # ZIP should be closed after exiting context (no exception means success)


class TestIgnorePatterns:
    """Test directory and file ignore patterns"""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        classifier = FileClassifier(TEST_ZIP_PATH)
        yield classifier
        classifier.close()
    
    def test_should_ignore_node_modules(self, classifier):
        """Test that node_modules is ignored."""
        assert classifier.should_ignore_path("project/node_modules/package.js") == True
    
    def test_should_ignore_pycache(self, classifier):
        """Test that __pycache__ is ignored."""
        assert classifier.should_ignore_path("project/__pycache__/file.pyc") == True
        assert classifier.should_ignore_path("__pycache__/file.pyc") == True
    
    def test_should_ignore_venv(self, classifier):
        """Test that virtual environments are ignored."""
        assert classifier.should_ignore_path("project/.venv/lib/python") == True
        assert classifier.should_ignore_path("project/venv/lib/python") == True
        assert classifier.should_ignore_path("project/env/bin/activate") == True
    
    def test_should_ignore_build_dirs(self, classifier):
        """Test that build directories are ignored."""
        assert classifier.should_ignore_path("project/build/output.js") == True
        assert classifier.should_ignore_path("project/dist/bundle.js") == True
        assert classifier.should_ignore_path("project/target/release/app") == True
    
    def test_should_ignore_git(self, classifier):
        """Test that .git directory is ignored."""
        assert classifier.should_ignore_path("project/.git/config") == True
    
    def test_should_not_ignore_source(self, classifier):
        """Test that source files are NOT ignored."""
        assert classifier.should_ignore_path("project/src/main.py") == False
        assert classifier.should_ignore_path("src/utils/helpers.py") == False
        assert classifier.should_ignore_path("README.md") == False
        assert classifier.should_ignore_path("tests/test_main.py") == False


class TestTestFileDetection:
    """Test detection of test files"""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        classifier = FileClassifier(TEST_ZIP_PATH)
        yield classifier
        classifier.close()
    
    def test_detect_test_prefix(self, classifier):
        """Test detection of test_ prefix."""
        assert classifier.is_test_file("project/test_main.py", "test_main.py") == True
        assert classifier.is_test_file("test_utils.py", "test_utils.py") == True
    
    def test_detect_test_suffix(self, classifier):
        """Test detection of _test suffix."""
        assert classifier.is_test_file("project/main_test.py", "main_test.py") == True
        assert classifier.is_test_file("utils_test.js", "utils_test.js") == True
    
    def test_detect_test_directory(self, classifier):
        """Test detection of test directories."""
        assert classifier.is_test_file("project/tests/test_utils.py", "test_utils.py") == True
        assert classifier.is_test_file("tests/utils.py", "utils.py") == True
        assert classifier.is_test_file("src/__tests__/app.test.js", "app.test.js") == True
    
    def test_detect_spec_files(self, classifier):
        """Test detection of spec files."""
        assert classifier.is_test_file("project/app.spec.js", "app.spec.js") == True
        assert classifier.is_test_file("specs/utils.spec.ts", "utils.spec.ts") == True
    
    def test_non_test_files(self, classifier):
        """Test that regular files are NOT detected as tests."""
        assert classifier.is_test_file("project/src/main.py", "main.py") == False
        assert classifier.is_test_file("src/utils.py", "utils.py") == False
        assert classifier.is_test_file("README.md", "README.md") == False


class TestLanguageDetection:
    """Test programming language detection"""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        classifier = FileClassifier(TEST_ZIP_PATH)
        yield classifier
        classifier.close()
    
    def test_python_detection(self, classifier):
        """Test Python file detection."""
        assert classifier.get_language_from_extension(".py") == "python"
        assert classifier.get_language_from_extension(".pyw") == "python"
    
    def test_javascript_detection(self, classifier):
        """Test JavaScript file detection."""
        assert classifier.get_language_from_extension(".js") == "javascript"
        assert classifier.get_language_from_extension(".mjs") == "javascript"
        assert classifier.get_language_from_extension(".cjs") == "javascript"
    
    def test_typescript_detection(self, classifier):
        """Test TypeScript file detection."""
        assert classifier.get_language_from_extension(".ts") == "typescript"
        assert classifier.get_language_from_extension(".tsx") == "typescript"
    
    def test_compiled_languages(self, classifier):
        """Test compiled language detection."""
        assert classifier.get_language_from_extension(".java") == "java"
        assert classifier.get_language_from_extension(".cpp") == "cpp"
        assert classifier.get_language_from_extension(".c") == "cpp"
        assert classifier.get_language_from_extension(".go") == "go"
        assert classifier.get_language_from_extension(".rs") == "rust"
    
    def test_case_insensitive(self, classifier):
        """Test that extension matching is case-insensitive."""
        assert classifier.get_language_from_extension(".PY") == "python"
        assert classifier.get_language_from_extension(".JS") == "javascript"
        assert classifier.get_language_from_extension(".Rs") == "rust"
    
    def test_unknown_extension(self, classifier):
        """Test that unknown extensions return 'unknown'."""
        assert classifier.get_language_from_extension(".xyz") == "unknown"
        assert classifier.get_language_from_extension(".random") == "unknown"


class TestFileClassification:
    """Test individual file classification"""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        classifier = FileClassifier(TEST_ZIP_PATH)
        yield classifier
        classifier.close()
    
    def test_classify_python_file(self, classifier):
        """Test classification of a Python source file."""
        result = classifier.classify_file("src/main.py")
        
        assert result is not None
        assert result['type'] == 'code'
        assert result['language'] == 'python'
        assert result['filename'] == 'main.py'
        assert result['path'] == 'src/main.py'
        assert result['is_test'] == False
        assert result['size'] > 0
    
    def test_classify_test_file(self, classifier):
        """Test classification of a test file."""
        result = classifier.classify_file("tests/test_main.py")
        
        assert result is not None
        assert result['type'] == 'code'
        assert result['language'] == 'python'
        assert result['is_test'] == True
    
    def test_classify_readme(self, classifier):
        """Test classification of README file."""
        result = classifier.classify_file("README.md")
        
        assert result is not None
        assert result['type'] == 'doc'
        assert result['filename'] == 'README.md'
        assert result.get('is_readme') == True
    
    def test_classify_config_file(self, classifier):
        """Test classification of configuration files."""
        result = classifier.classify_file("pyproject.toml")
        
        assert result is not None
        assert result['type'] == 'config'
        assert result['filename'] == 'pyproject.toml'
    
    def test_classify_requirements(self, classifier):
        """Test classification of requirements.txt."""
        result = classifier.classify_file("requirements.txt")
        
        assert result is not None
        assert result['type'] == 'doc'
    
    def test_classify_license(self, classifier):
        """Test classification of LICENSE file."""
        result = classifier.classify_file("LICENSE")
        
        assert result is not None
        assert result['type'] == 'other'
    
    def test_classify_nonexistent_file(self, classifier):
        """Test that classifying a non-existent file returns None."""
        result = classifier.classify_file("does_not_exist.py")
        assert result is None


class TestProjectClassification:
    """Test full project classification"""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        classifier = FileClassifier(TEST_ZIP_PATH)
        yield classifier
        classifier.close()
    
    @pytest.fixture
    def result(self, classifier):
        """Get classification result for the test project."""
        return classifier.classify_project(PROJECT_PATH)
    
    def test_result_structure(self, result):
        """Test that result has correct structure."""
        assert 'project_path' in result
        assert 'files' in result
        assert 'stats' in result
        
        # Check file categories
        assert 'code' in result['files']
        assert 'docs' in result['files']
        assert 'tests' in result['files']
        assert 'configs' in result['files']
        assert 'other' in result['files']
        assert 'skipped' in result['files']
        
        # Check stats
        assert 'total_files' in result['stats']
        assert 'total_size' in result['stats']
    
    def test_code_organization(self, result):
        """Test that code files are organized by language."""
        assert isinstance(result['files']['code'], dict)
        assert 'python' in result['files']['code']
        assert len(result['files']['code']['python']) > 0
    
    def test_file_counts(self, result):
        """Test that file counts are reasonable."""
        # Should have found multiple files
        assert result['stats']['total_files'] > 0
        assert result['stats']['total_size'] > 0
        
        # Should have Python code
        python_files = result['files']['code'].get('python', [])
        assert len(python_files) > 0
        
        # Should have at least one test
        assert len(result['files']['tests']) > 0
        
        # Should have documentation
        assert len(result['files']['docs']) > 0
    
    def test_total_count_consistency(self, result):
        """Test that total file count matches sum of categories."""
        total = 0
        total += sum(len(files) for files in result['files']['code'].values())
        total += len(result['files']['docs'])
        total += len(result['files']['tests'])
        total += len(result['files']['configs'])
        total += len(result['files']['other'])
        total += len(result['files']['skipped'])
        
        assert result['stats']['total_files'] == total
    
    def test_specific_files_found(self, result):
        """Test that specific expected files are found."""
        all_files = []
        
        # Collect all file paths
        for lang_files in result['files']['code'].values():
            all_files.extend([f['path'] for f in lang_files])
        all_files.extend([f['path'] for f in result['files']['docs']])
        all_files.extend([f['path'] for f in result['files']['tests']])
        all_files.extend([f['path'] for f in result['files']['configs']])
        all_files.extend([f['path'] for f in result['files']['other']])
        
        # Check for expected files
        assert any('main.py' in f for f in all_files)
        assert any('README.md' in f for f in all_files)
        assert any('test_' in f for f in all_files)
    
    def test_ignored_files_excluded(self, result):
        """Test that ignored directories are excluded."""
        all_files = []
        
        # Collect all file paths
        for lang_files in result['files']['code'].values():
            all_files.extend([f['path'] for f in lang_files])
        all_files.extend([f['path'] for f in result['files']['tests']])
        
        # Should NOT find files from ignored directories
        assert not any('__pycache__' in f for f in all_files)
        assert not any('venv/' in f for f in all_files)
    
    def test_readme_flagged(self, result):
        """Test that README is properly flagged."""
        readme_files = [f for f in result['files']['docs'] if f.get('is_readme')]
        assert len(readme_files) > 0
    
    def test_tests_separated_from_code(self, result):
        """Test that test files are in 'tests' category, not 'code'."""
        # Get all test file paths
        test_paths = [f['path'] for f in result['files']['tests']]
        
        # Get all code file paths
        code_paths = []
        for lang_files in result['files']['code'].values():
            code_paths.extend([f['path'] for f in lang_files])
        
        # Test files should not be in code category
        for test_path in test_paths:
            assert test_path not in code_paths
    
    def test_file_metadata_complete(self, result):
        """Test that all files have complete metadata."""
        # Check a few files from different categories
        if result['files']['code'].get('python'):
            file_info = result['files']['code']['python'][0]
            assert 'path' in file_info
            assert 'filename' in file_info
            assert 'size' in file_info
            assert 'extension' in file_info
            assert 'type' in file_info
            assert 'language' in file_info
        
        if result['files']['docs']:
            file_info = result['files']['docs'][0]
            assert 'path' in file_info
            assert 'filename' in file_info
            assert 'size' in file_info


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_nonexistent_zip(self):
        """Test handling of non-existent ZIP file."""
        fake_path = Path("nonexistent.zip")
        with pytest.raises(FileNotFoundError):
            classifier = FileClassifier(fake_path)
    
    def test_empty_project_path(self):
        """Test classification with empty project path (root)."""
        with FileClassifier(TEST_ZIP_PATH) as classifier:
            result = classifier.classify_project("")
            assert result['stats']['total_files'] > 0
    
    def test_project_path_with_trailing_slash(self):
        """Test that trailing slashes are handled correctly."""
        with FileClassifier(TEST_ZIP_PATH) as classifier:
            result1 = classifier.classify_project("")
            result2 = classifier.classify_project("/")
            
            # Both should work (though may have different file counts)
            assert result1 is not None
            assert result2 is not None
    
    def test_nonexistent_project_path(self):
        """Test classification of non-existent project path."""
        with FileClassifier(TEST_ZIP_PATH) as classifier:
            result = classifier.classify_project("nonexistent/project")
            # Should return empty results, not crash
            assert result['stats']['total_files'] == 0


# Utility test for debugging
class TestDebugOutput:
    """Tests that produce useful debug output"""
    
    def test_print_project_summary(self):
        """Print a detailed summary of the classified project."""
        with FileClassifier(TEST_ZIP_PATH) as classifier:
            result = classifier.classify_project(PROJECT_PATH)
            
            print("\n" + "="*80)
            print(f"Project: {result['project_path']}")
            print("="*80)
            print(f"\nTotal files: {result['stats']['total_files']}")
            print(f"Total size: {result['stats']['total_size']:,} bytes")
            
            print("\n--- Code Files by Language ---")
            for language, files in result['files']['code'].items():
                print(f"  {language}: {len(files)} files")
                for file_info in files[:5]:
                    print(f"    - {file_info['filename']} ({file_info['size']} bytes)")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
            
            print(f"\n--- Documentation ---")
            print(f"  Total: {len(result['files']['docs'])} files")
            for file_info in result['files']['docs']:
                readme = " [README]" if file_info.get('is_readme') else ""
                print(f"    - {file_info['filename']}{readme}")
            
            print(f"\n--- Tests ---")
            print(f"  Total: {len(result['files']['tests'])} files")
            for file_info in result['files']['tests']:
                print(f"    - {file_info['filename']}")
            
            print(f"\n--- Configuration ---")
            print(f"  Total: {len(result['files']['configs'])} files")
            for file_info in result['files']['configs']:
                print(f"    - {file_info['filename']}")
            
            if result['files']['other']:
                print(f"\n--- Other Files ---")
                for file_info in result['files']['other']:
                    print(f"    - {file_info['filename']}")
            
            print("\n" + "="*80)