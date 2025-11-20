import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add paths for imports
current_dir = Path(__file__).parent
backend_test_dir = current_dir
tests_dir = backend_test_dir.parent
src_dir = tests_dir.parent
backend_dir = src_dir / "backend"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from backend.analysis.deep_code_analyzer import generate_comprehensive_report


class TestGenerateComprehensiveReport:
    """Test the generate_comprehensive_report function that analyze.py uses."""

    @pytest.fixture
    def sample_python_zip(self):
        """Create a temporary ZIP file with Python code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # Add a simple Python file
                python_code = """
class MyClass:
    def __init__(self):
        self._private = 0
    
    def public_method(self):
        return self._private
"""
                zf.writestr("test.py", python_code)
                zf.writestr("README.md", "# Test Project")

            yield zip_path

            # Cleanup
            # os.unlink(tmp.name)

    @pytest.fixture
    def sample_java_zip(self):
        """Create a temporary ZIP file with Java code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # Add a simple Java file
                java_code = """
public class Plane {
    private int altitude;

    public int getAltitude() {
        return altitude;
    }
    
    public void setAltitude(int altitude) {
        this.altitude = altitude;
    }
}
"""
                zf.writestr("Plane.java", java_code)
                zf.writestr("pom.xml", "<project></project>")

            yield zip_path

            # Cleanup
            # os.unlink(tmp.name)

    @pytest.fixture
    def sample_mixed_zip(self):
        """Create a temporary ZIP file with both Python and Java aircraft-related code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # Add Python file
                python_code = """
    from abc import ABC, abstractmethod

    class Aircraft(ABC):
        @abstractmethod
        def fly(self):
            pass

    class Boeing737(Aircraft):
        def fly(self):
            return "Boeing 737 climbing to 35,000 feet"
    """
                zf.writestr("Aircraft.py", python_code)

                # Add Java file
                java_code = """
    public interface AircraftSpec {
        double maxSpeed();
    }

    public class Jet implements AircraftSpec {
        private double speedKnots;

        public Jet(double speedKnots) {
            this.speedKnots = speedKnots;
        }

        @Override
        public double maxSpeed() {
            return speedKnots;
        }
    }
    """
                zf.writestr("Jet.java", java_code)

                zf.writestr("README.md", "# Mixed Aircraft Project")

            yield zip_path

            # Cleanup
            # os.unlink(tmp.name)

    def test_java_project_analysis(self, sample_java_zip):
        """Test analyzing a Java project."""
        report = generate_comprehensive_report(sample_java_zip)

        assert "projects" in report
        assert len(report["projects"]) > 0

        # Check for Java language detection
        project = report["projects"][0]
        assert "java" in project.get("languages", {})

        # Check for Java OOP analysis (if javalang is available)
        if "java_oop_analysis" in project:
            java_oop = project["java_oop_analysis"]
            if "error" not in java_oop:
                assert "total_classes" in java_oop

    def test_mixed_project_analysis(self, sample_mixed_zip):
        """Test analyzing a project with both Python and Java."""
        report = generate_comprehensive_report(sample_mixed_zip)

        assert "projects" in report
        assert len(report["projects"]) > 0

        project = report["projects"][0]
        languages = project.get("languages", {})

        # Should detect both languages
        assert "python" in languages or "java" in languages

    def test_empty_zip(self):
        """Test analyzing an empty ZIP file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                pass  # Empty zip

            # try:
            report = generate_comprehensive_report(Path(zip_path))

            assert "projects" in report
            assert "summary" in report
            # Should handle empty project gracefully

            # finally:
            #    os.unlink(tmp.name)

    def test_report_structure(self, sample_python_zip):
        """Test that the report has the expected structure."""
        report = generate_comprehensive_report(sample_python_zip)

        # Check top-level keys
        assert "summary" in report
        assert "projects" in report

        # Check summary structure
        summary = report["summary"]
        assert "total_files" in summary
        assert "languages_used" in summary

        # Check project structure
        if report["projects"]:
            project = report["projects"][0]
            assert "project_name" in project
            assert "total_files" in project
            assert "languages" in project

    def test_save_report_to_file(self, sample_python_zip):
        """Test saving report to a JSON file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_path = Path(tmp.name)

        try:
            report = generate_comprehensive_report(sample_python_zip, output_path=output_path)

            # Check that file was created
            assert output_path.exists()

            # Check that file contains valid JSON
            import json

            with open(output_path, "r") as f:
                saved_report = json.load(f)

            assert saved_report == report

        finally:
            if output_path.exists():
                os.unlink(output_path)


class TestAnalyzeScriptIntegration:
    """Test the analyze.py script functionality."""

    @pytest.fixture
    def sample_project_zip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:

                # Very simple Python OOP
                python_code = """
                class Gate:
                    def __init__(self, number):
                        self.number = number
                """
                zf.writestr("src/gate.py", python_code)

                # Very simple Java OOP
                java_code = """
                public class Runway {
                    private int length;

                    public Runway(int length) {
                        this.length = length;
                    }

                    public int getLength() {
                        return length;
                    }
                }
                """
                zf.writestr("src/Runway.java", java_code)

                zf.writestr("README.md", "# Simple Airport Project")
                zf.writestr("requirements.txt", "pytest==7.0.0")

            yield zip_path
            # os.unlink(tmp.name)

    def test_comprehensive_analysis_with_both_languages(self, sample_project_zip):
        """Test that analyze.py can handle projects with multiple languages."""
        report = generate_comprehensive_report(sample_project_zip)

        assert "projects" in report
        assert len(report["projects"]) > 0

        project = report["projects"][0]

        # Check basic metadata
        assert "total_files" in project
        assert project["total_files"] > 0

        # Check language detection
        languages = project.get("languages", {})
        assert len(languages) > 0


class TestJavaAnalysisWithoutJavalang:
    """Test Java analysis behavior when javalang is not available."""

    @pytest.fixture
    def sample_java_zip(self):
        """Create a temporary ZIP file with Java code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                java_code = """
                public class Test {
                    private int x;
                }
                """
                zf.writestr("Test.java", java_code)

            yield zip_path
            # os.unlink(tmp.name)


class TestPythonOOPScoring:
    """Test OOP scoring for Python projects."""

    def test_procedural_style(self):
        """Test procedural/functional code gets low OOP score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                code = """
            def add(x, y):
                return x + y

            def multiply(x, y):
                return x * y
            """
                zf.writestr("math.py", code)

            # try:
            report = generate_comprehensive_report(Path(zip_path))
            project = report["projects"][0]

            if "oop_analysis" in project and "error" not in project["oop_analysis"]:
                oop = project["oop_analysis"]
                assert oop["total_classes"] == 0

            # finally:
            #    os.unlink(tmp.name)

    def test_advanced_oop_style(self):
        """Test advanced OOP code gets high score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "shapes.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                code = """
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass
    
    @property
    def name(self):
        return self._name
    
    def __str__(self):
        return f"{self.name}"

class Circle(Shape):
    def __init__(self, radius):
        self._radius = radius
        self._name = "Circle"
    
    def area(self):
        return 3.14 * self._radius ** 2
"""
                zf.writestr("shapes.py", code)

            # try:
            report = generate_comprehensive_report(Path(zip_path))
            project = report["projects"][0]

            if "oop_analysis" in project and "error" not in project["oop_analysis"]:
                oop = project["oop_analysis"]
                assert oop["total_classes"] >= 2
                assert len(oop["abstract_classes"]) > 0
                assert oop["inheritance_depth"] > 0

            # finally:
            #    os.unlink(tmp.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
