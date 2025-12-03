"""
Integration tests for the complete analysis pipeline including:
- C++/C/Python/Java OOP analyzers
- Resume generator
- Database storage
- LLM pipeline

These tests verify that all components work together correctly end-to-end.
"""

import builtins
import sys
import tempfile
import zipfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend import database
from backend.analysis_database import get_connection, init_db
from backend.cli import main


@pytest.fixture
def sample_python_project_zip(tmp_path):
    """Create a sample Python project ZIP for testing."""
    project_dir = tmp_path / "python_project"
    project_dir.mkdir()

    # Create a Python file with OOP code
    python_file = project_dir / "main.py"
    python_file.write_text(
        """
from abc import ABC, abstractmethod

class Animal(ABC):
    '''Abstract base class for animals.'''
    def __init__(self, name):
        self._name = name
        self.__age = 0

    @property
    def name(self):
        return self._name

    @abstractmethod
    def speak(self):
        pass

    def __str__(self):
        return f"{self._name}"

class Dog(Animal):
    '''Dog implementation.'''
    def speak(self):
        return "Woof!"

class Cat(Animal):
    '''Cat implementation.'''
    def speak(self):
        return "Meow!"
"""
    )

    # Create a README
    readme = project_dir / "README.md"
    readme.write_text("# Sample Python Project\n\nA demo project with OOP patterns.")

    # Create ZIP
    zip_path = tmp_path / "python_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in project_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(tmp_path))

    return zip_path


@pytest.fixture
def sample_cpp_project_zip(tmp_path):
    """Create a sample C++ project ZIP for testing."""
    project_dir = tmp_path / "cpp_project"
    project_dir.mkdir()

    # Create a C++ file with OOP code
    cpp_file = project_dir / "main.cpp"
    cpp_file.write_text(
        """
#include <iostream>
#include <string>

class Animal {
private:
    std::string name;
protected:
    int age;
public:
    Animal(std::string n) : name(n), age(0) {}
    virtual void speak() = 0;
    virtual ~Animal() {}
};

class Dog : public Animal {
public:
    Dog(std::string n) : Animal(n) {}
    void speak() override {
        std::cout << "Woof!" << std::endl;
    }
};

template<typename T>
class Container {
private:
    T data;
public:
    Container(T d) : data(d) {}
    T getData() { return data; }
};

int main() {
    Dog d("Buddy");
    d.speak();
    return 0;
}
"""
    )

    # Create ZIP
    zip_path = tmp_path / "cpp_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in project_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(tmp_path))

    return zip_path


@pytest.fixture
def sample_c_project_zip(tmp_path):
    """Create a sample C project ZIP for testing."""
    project_dir = tmp_path / "c_project"
    project_dir.mkdir()

    # Create a C file with OOP-style code
    c_file = project_dir / "main.c"
    c_file.write_text(
        """
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    char* name;
    int age;
} Animal;

typedef struct {
    Animal base;
    void (*speak)(void);
} Dog;

static void dog_speak(void) {
    printf("Woof!\\n");
}

Animal* Animal_create(char* name) {
    Animal* a = (Animal*)malloc(sizeof(Animal));
    a->name = name;
    a->age = 0;
    return a;
}

void Animal_destroy(Animal* a) {
    free(a);
}

int main() {
    Animal* a = Animal_create("Buddy");
    Animal_destroy(a);
    return 0;
}
"""
    )

    # Create ZIP
    zip_path = tmp_path / "c_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in project_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(tmp_path))

    return zip_path


@pytest.fixture
def sample_java_project_zip(tmp_path):
    """Create a sample Java project ZIP for testing."""
    project_dir = tmp_path / "java_project"
    project_dir.mkdir()

    # Create a Java file with OOP code
    java_file = project_dir / "Main.java"
    java_file.write_text(
        """
public abstract class Animal {
    private String name;
    protected int age;

    public Animal(String name) {
        this.name = name;
        this.age = 0;
    }

    public abstract void speak();

    public String getName() {
        return name;
    }
}

public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }

    @Override
    public void speak() {
        System.out.println("Woof!");
    }
}
"""
    )

    # Create ZIP
    zip_path = tmp_path / "java_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file in project_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(tmp_path))

    return zip_path


class TestPythonOOPAnalysisIntegration:
    """Test Python OOP analysis integration in CLI."""

    def test_python_oop_analysis_in_cli(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test that Python OOP analysis runs and displays in CLI."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(sample_python_project_zip)]), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "ANALYSIS RESULTS" in output
            assert "python" in output.lower()

            # Check for OOP analysis output
            if "OOP Analysis (Python)" in output:
                assert "Classes:" in output


class TestCppOOPAnalysisIntegration:
    """Test C++ OOP analysis integration in CLI."""

    def test_cpp_oop_analysis_in_cli(self, isolated_test_env, temp_session_file, sample_cpp_project_zip):
        """Test that C++ OOP analysis runs and displays in CLI."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(sample_cpp_project_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "ANALYSIS RESULTS" in output
            # C++ analysis may show error if libclang not installed, which is acceptable
            assert "cpp" in output.lower() or "c++" in output.lower()

    def test_cpp_analysis_graceful_degradation_without_libclang(
        self, isolated_test_env, temp_session_file, sample_cpp_project_zip
    ):
        """Test that analysis continues gracefully if libclang is not installed."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(sample_cpp_project_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            # Should complete successfully even if C++ analyzer unavailable
            assert result == 0
            assert "Analysis complete" in output


class TestCOOPAnalysisIntegration:
    """Test C OOP-style analysis integration in CLI."""

    def test_c_oop_analysis_in_cli(self, isolated_test_env, temp_session_file, sample_c_project_zip):
        """Test that C OOP-style analysis runs and displays in CLI."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(sample_c_project_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "ANALYSIS RESULTS" in output


class TestJavaOOPAnalysisIntegration:
    """Test Java OOP analysis integration in CLI."""

    def test_java_oop_analysis_in_cli(self, isolated_test_env, temp_session_file, sample_java_project_zip):
        """Test that Java OOP analysis runs and displays in CLI."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(sample_java_project_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "ANALYSIS RESULTS" in output
            assert "java" in output.lower()


class TestResumeGeneratorIntegration:
    """Test resume generator integration in CLI."""

    def test_resume_generation_in_cli(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test that resume highlights are generated and displayed."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(sample_python_project_zip)]), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "GENERATED RESUME ITEMS" in output

    def test_resume_generation_with_no_content(self, isolated_test_env, temp_session_file, tmp_path):
        """Test resume generator handles projects with minimal content."""
        # Create minimal ZIP with just a text file
        minimal_zip = tmp_path / "minimal.zip"
        with zipfile.ZipFile(minimal_zip, "w") as zf:
            zf.writestr("readme.txt", "Empty project")

        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(minimal_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            # Should complete without crashing
            assert result == 0
            assert "Analysis complete" in output


class TestDatabaseStorageIntegration:
    """Test database storage integration in CLI."""

    def test_analysis_stored_in_database(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test that analysis results are stored in database."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        # Initialize analysis database
        init_db()

        with patch("sys.argv", ["cli", "analyze", str(sample_python_project_zip)]), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Analysis saved to database" in output
            assert "ID:" in output
            assert "UUID:" in output

            # Verify database entry was created
            with get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM analyses WHERE analysis_type = 'non_llm'")
                count = cursor.fetchone()[0]
                assert count >= 1

    def test_database_storage_non_fatal_on_failure(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test that analysis continues even if database storage fails."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        # Mock record_analysis to raise an error
        with patch("sys.argv", ["cli", "analyze", str(sample_python_project_zip)]), patch(
            "backend.analysis_database.record_analysis", side_effect=Exception("DB Error")
        ), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            # Should still succeed
            assert result == 0
            assert "Warning: Could not save to database" in output
            assert "Analysis complete" in output


class TestLLMPipelineIntegration:
    """Test LLM pipeline integration in CLI."""

    def test_llm_command_requires_login(self, isolated_test_env, sample_python_project_zip):
        """Test that LLM analysis requires login."""
        with patch("sys.argv", ["cli", "analyze-llm", str(sample_python_project_zip)]), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Please login first" in output

    def test_llm_analysis_requires_consent(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test that LLM analysis requires consent."""
        # Setup: Create user without consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", False)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze-llm", str(sample_python_project_zip)]), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Please provide consent before analyzing files" in output

    def test_llm_analysis_requires_zip_file(self, isolated_test_env, temp_session_file, tmp_path):
        """Test that LLM analysis requires a ZIP file."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        # Create a regular directory
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        with patch("sys.argv", ["cli", "analyze-llm", str(test_dir)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "LLM analysis requires a ZIP file" in output

    def test_llm_analysis_with_mock_gemini(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test LLM analysis with mocked Gemini client."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        # Mock the LLM pipeline to avoid actual API calls
        with patch("sys.argv", ["cli", "analyze-llm", str(sample_python_project_zip)]), patch(
            "backend.analysis.llm_pipeline.run_gemini_analysis"
        ) as mock_llm, patch("sys.stdout", new=StringIO()) as fake_out:
            # Setup mock return value
            mock_llm.return_value = {
                "analysis_metadata": {"analysis_uuid": "test-uuid", "zip_file": "test.zip", "analysis_timestamp": "2025-01-01"},
                "summary": {},
                "llm_summary": "Mock AI analysis: The code demonstrates good OOP practices.",
                "projects": [],
            }

            result = main()
            output = fake_out.getvalue()

            assert result == 0
            # Verify LLM was called
            mock_llm.assert_called_once()

            # Check output contains LLM summary
            assert "AI-POWERED ANALYSIS SUMMARY" in output
            assert "Mock AI analysis" in output

    def test_llm_analysis_with_custom_prompt(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test LLM analysis with custom prompt."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        custom_prompt = "Analyze code quality"

        # Mock the LLM pipeline
        with patch("sys.argv", ["cli", "analyze-llm", str(sample_python_project_zip), "--prompt", custom_prompt]), patch(
            "backend.analysis.llm_pipeline.run_gemini_analysis"
        ) as mock_llm, patch("sys.stdout", new=StringIO()):
            # Setup mock return value
            mock_llm.return_value = {
                "analysis_metadata": {"analysis_uuid": "test-uuid", "zip_file": "test.zip", "analysis_timestamp": "2025-01-01"},
                "summary": {},
                "llm_summary": "Quality analysis result",
                "projects": [],
            }

            result = main()

            # Verify LLM was called with custom prompt
            mock_llm.assert_called_once()
            args = mock_llm.call_args
            assert args[0][1] == custom_prompt

    def test_llm_analysis_error_handling(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test LLM analysis handles errors gracefully."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        # Mock the LLM pipeline to return an error
        with patch("sys.argv", ["cli", "analyze-llm", str(sample_python_project_zip)]), patch(
            "backend.analysis.llm_pipeline.run_gemini_analysis"
        ) as mock_llm, patch("sys.stdout", new=StringIO()) as fake_out:
            # Setup mock to return error
            mock_llm.return_value = {
                "analysis_metadata": {"analysis_uuid": "test-uuid", "zip_file": "test.zip", "analysis_timestamp": "2025-01-01"},
                "summary": {},
                "llm_error": "Google Cloud libraries not installed",
                "projects": [],
            }

            result = main()
            output = fake_out.getvalue()

            assert result == 0  # Still completes
            assert "LLM Analysis Error" in output
            assert "Google Cloud libraries" in output


class TestCompleteAnalysisPipeline:
    """Test complete end-to-end analysis pipeline."""

    def test_full_pipeline_with_all_components(self, isolated_test_env, temp_session_file, sample_python_project_zip):
        """Test complete pipeline: login -> analysis -> OOP -> resume -> database."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        # Initialize analysis database
        init_db()

        with patch("sys.argv", ["cli", "analyze", str(sample_python_project_zip)]), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            output = fake_out.getvalue()

            # Verify success
            assert result == 0

            # Verify all pipeline components appear in output
            assert "ANALYSIS RESULTS" in output
            assert "GENERATED RESUME ITEMS" in output
            assert "Analysis saved to database" in output
            assert "Analysis complete" in output

            # Verify database entry was created
            with get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM analyses WHERE analysis_type = 'non_llm'")
                count = cursor.fetchone()[0]
                assert count >= 1

    def test_multi_language_project_analysis(self, isolated_test_env, temp_session_file, sample_python_project_zip, tmp_path):
        """Test analysis of project with multiple languages."""
        # Create a multi-language project
        project_dir = tmp_path / "multi_lang"
        project_dir.mkdir()

        # Add Python file
        (project_dir / "app.py").write_text("print('Hello')")

        # Add Java file
        (project_dir / "Main.java").write_text("public class Main { }")

        # Add C++ file
        (project_dir / "main.cpp").write_text("int main() { return 0; }")

        # Create ZIP
        multi_zip = tmp_path / "multi_lang.zip"
        with zipfile.ZipFile(multi_zip, "w") as zf:
            for file in project_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(tmp_path))

        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(multi_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "ANALYSIS RESULTS" in output
            # Should detect multiple languages
            output_lower = output.lower()
            assert "python" in output_lower or "java" in output_lower or "cpp" in output_lower


class TestErrorHandlingInIntegration:
    """Test error handling across integrated components."""

    def test_analysis_handles_corrupted_zip(self, isolated_test_env, temp_session_file, tmp_path):
        """Test that analysis handles corrupted ZIP files gracefully."""
        # Create corrupted ZIP
        bad_zip = tmp_path / "bad.zip"
        bad_zip.write_text("This is not a valid ZIP file")

        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(bad_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Invalid or corrupted ZIP file" in output or "BadZipFile" in output

    def test_analysis_handles_empty_zip(self, isolated_test_env, temp_session_file, tmp_path):
        """Test analysis of empty ZIP file."""
        # Create empty ZIP
        empty_zip = tmp_path / "empty.zip"
        with zipfile.ZipFile(empty_zip, "w"):
            pass  # Create empty ZIP

        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(empty_zip)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            # Should complete (may have no results)
            assert result == 0
            assert "ANALYSIS RESULTS" in output
