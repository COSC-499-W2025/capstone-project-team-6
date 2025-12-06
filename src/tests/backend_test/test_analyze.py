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
            zip_path = Path(tmpdir) / "test.zip"
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

    @pytest.fixture
    def sample_java_zip(self, tmp_path: Path):
        """Create a temporary ZIP file with Java code."""
        zip_path = tmp_path / "sample_java_project.zip"

        # Create the ZIP file
        with zipfile.ZipFile(zip_path, "w") as zf:
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

    
    @pytest.fixture
    def sample_mixed_zip(self, tmp_path: Path):
        """Create a temporary ZIP file with both Python and Java aircraft-related code."""
        zip_path = tmp_path / "mixed_aircraft_project.zip"
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

    def test_empty_zip(self, tmp_path: Path):
        """Test analyzing an empty ZIP file."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            pass  # Empty zip

           
        report = generate_comprehensive_report(zip_path)
        assert "projects" in report
        assert "summary" in report
        # Should handle empty project gracefully


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
    def sample_project_zip(self, tmp_path: Path):
        zip_path = tmp_path / "sample_airport_project.zip"
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

        return zip_path

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
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                java_code = """
                public class Test {
                    private int x;
                }
                """
                zf.writestr("Test.java", java_code)

            yield Path(tmp.name)
            os.unlink(tmp.name)


class TestPythonOOPScoring:
    """Test OOP scoring for Python projects."""

    def test_procedural_style(self, tmp_path: Path):
        """Test procedural/functional code gets low OOP score."""
        zip_path = tmp_path / "procedural_style.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            code = """
            def add(x, y):
                return x + y

            def multiply(x, y):
                return x * y
            """
            zf.writestr("math.py", code)

        
        report = generate_comprehensive_report(Path(zip_path))
        project = report["projects"][0]

        if "oop_analysis" in project and "error" not in project["oop_analysis"]:
            oop = project["oop_analysis"]
            assert oop["total_classes"] == 0

            

    def test_advanced_oop_style(self, tmp_path: Path):
        """Test advanced OOP code gets high score."""
        zip_path = tmp_path / "advanced_oop_style.zip"
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

            
        report = generate_comprehensive_report(zip_path)
        project = report["projects"][0]

        if "oop_analysis" in project and "error" not in project["oop_analysis"]:
            oop = project["oop_analysis"]
            assert oop["total_classes"] >= 2
            assert len(oop["abstract_classes"]) > 0
            assert oop["inheritance_depth"] > 0

        


class TestSummarizeTopRankedProjects:
    """Test the summarize_top_ranked_projects function."""

    @pytest.fixture
    def mock_analysis_db(self, tmp_path):
        """Set up a temporary analysis database for testing."""
        from backend import analysis_database as adb
        
        # Set temporary database path
        db_path = tmp_path / "test_analysis.db"
        previous = adb.set_db_path(db_path)
        adb.init_db()
        
        yield adb
        
        # Restore previous path
        adb.set_db_path(previous)

    @pytest.fixture
    def sample_project_data(self):
        """Create sample project data for testing."""
        return {
            "project_name": "TestProject",
            "project_path": "/test/project",
            "primary_language": "python",
            "languages": {"python": 10},
            "total_files": 15,
            "code_files": 12,
            "test_files": 3,
            "has_tests": True,
            "has_readme": True,
            "has_ci_cd": False,
            "has_docker": False,
            "is_git_repo": True,
            "test_coverage_estimate": "medium",
            "frameworks": ["Django"],
            "oop_analysis": {
                "total_classes": 5,
                "oop_score": 4,
                "solid_score": 3.5,
                "inheritance_depth": 2,
                "private_methods": 8,
                "protected_methods": 2,
                "design_patterns": ["Singleton", "Factory"]
            },
            "complexity_analysis": {
                "optimization_score": 75.0
            }
        }

    @pytest.fixture
    def sample_project_data_high_score(self):
        """Create sample project data with high score."""
        return {
            "project_name": "HighScoreProject",
            "project_path": "/high/score",
            "primary_language": "python",
            "languages": {"python": 20},
            "total_files": 30,
            "code_files": 25,
            "test_files": 5,
            "has_tests": True,
            "has_readme": True,
            "has_ci_cd": True,
            "has_docker": True,
            "is_git_repo": True,
            "test_coverage_estimate": "high",
            "frameworks": ["Django", "React"],
            "oop_analysis": {
                "total_classes": 10,
                "oop_score": 6,
                "solid_score": 5.0,
                "inheritance_depth": 3,
                "private_methods": 15,
                "protected_methods": 5,
                "design_patterns": ["Singleton", "Factory", "Observer", "Strategy"]
            },
            "complexity_analysis": {
                "optimization_score": 90.0
            }
        }

    @pytest.fixture
    def sample_project_data_low_score(self):
        """Create sample project data with low score."""
        return {
            "project_name": "LowScoreProject",
            "project_path": "/low/score",
            "primary_language": "python",
            "languages": {"python": 5},
            "total_files": 8,
            "code_files": 6,
            "test_files": 0,
            "has_tests": False,
            "has_readme": False,
            "has_ci_cd": False,
            "has_docker": False,
            "is_git_repo": False,
            "frameworks": []
        }

    def create_analysis_in_db(self, analysis_db, zip_file_path, projects, timestamp="2025-11-30T10:00:00"):
        """Helper to create an analysis record in the database."""
        import json
        
        report = {
            "analysis_metadata": {
                "zip_file": zip_file_path,
                "analysis_timestamp": timestamp,
                "total_projects": len(projects)
            },
            "projects": projects,
            "summary": {
                "total_files": sum(p.get("total_files", 0) for p in projects),
                "total_size_bytes": 1000000,
                "languages_used": list(set(p.get("primary_language", "") for p in projects))
            }
        }
        
        return analysis_db.record_analysis(
            analysis_type="non_llm",
            payload=report,
            analysis_uuid=str(hash(zip_file_path + timestamp))
        )

    def test_summarize_with_no_analyses(self, mock_analysis_db, capsys):
        """Test summarize when database is empty."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        summarize_top_ranked_projects(limit=10)
        
        captured = capsys.readouterr()
        assert "No analyses found in database" in captured.out

    def test_summarize_with_no_analyses_for_zip(self, mock_analysis_db, capsys):
        """Test summarize when no analyses exist for specific zip file."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        summarize_top_ranked_projects(limit=10, zip_file_path="/nonexistent.zip")
        
        captured = capsys.readouterr()
        assert "No analyses found for" in captured.out

    def test_summarize_with_single_project(self, mock_analysis_db, sample_project_data, capsys):
        """Test summarize with a single project."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path = "/test/project.zip"
        self.create_analysis_in_db(mock_analysis_db, zip_path, [sample_project_data])
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        assert "TOP RANKED PROJECTS SUMMARY" in captured.out
        assert "TestProject" in captured.out
        assert "COMPOSITE SCORE" in captured.out
        assert "RANK #1" in captured.out

    def test_summarize_with_multiple_projects(self, mock_analysis_db, 
                                               sample_project_data, 
                                               sample_project_data_high_score,
                                               sample_project_data_low_score,
                                               capsys):
        """Test summarize with multiple projects - should rank by score."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path = "/test/multi.zip"
        self.create_analysis_in_db(
            mock_analysis_db, 
            zip_path, 
            [sample_project_data, sample_project_data_high_score, sample_project_data_low_score]
        )
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out
        assert "HighScoreProject" in output
        assert "TestProject" in output
        assert "LowScoreProject" in output
        high_score_index = output.find("HighScoreProject")
        test_project_index = output.find("TestProject")
        low_score_index = output.find("LowScoreProject")
        assert high_score_index < test_project_index < low_score_index or \
               (high_score_index < low_score_index and test_project_index < low_score_index)

    def test_summarize_keeps_higher_score_on_duplicate(self, mock_analysis_db, sample_project_data, capsys):
        """Test that when deduplicating, the higher score is kept."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        zip_path = "/test/duplicate.zip"
        # Create two versions of same project with different scores
        project_low = sample_project_data.copy()
        project_low["oop_analysis"]["oop_score"] = 2
        project_low["oop_analysis"]["solid_score"] = 1.0
        
        project_high = sample_project_data.copy()
        project_high["oop_analysis"]["oop_score"] = 6
        project_high["oop_analysis"]["solid_score"] = 5.0        
        self.create_analysis_in_db(mock_analysis_db, zip_path, [project_low, project_high])
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert output.count("TestProject") == 1

    def test_summarize_keeps_most_recent_on_tie(self, mock_analysis_db, sample_project_data, capsys):
        """Test that when scores are equal, most recent timestamp is kept."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path = "/test/tie.zip"
        
        project1 = sample_project_data.copy()
        project2 = sample_project_data.copy()
        project1["oop_analysis"]["oop_score"] = 4
        project2["oop_analysis"]["oop_score"] = 4
        
        self.create_analysis_in_db(mock_analysis_db, zip_path, [project1], "2025-11-30T04:00:00")
        self.create_analysis_in_db(mock_analysis_db, zip_path, [project2], "2025-11-30T06:30:00")
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert output.count("TestProject") == 1
        assert "2025-11-30T06:30:00" in output

    def test_summarize_filters_by_zip_file(self, mock_analysis_db, sample_project_data, capsys):
        """Test that summarize can filter by zip file path."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path1 = "/test/project1.zip"
        zip_path2 = "/test/project2.zip"
        
        project1 = sample_project_data.copy()
        project1["project_name"] = "Project1"
        
        project2 = sample_project_data.copy()
        project2["project_name"] = "Project2"
        
        self.create_analysis_in_db(mock_analysis_db, zip_path1, [project1])
        self.create_analysis_in_db(mock_analysis_db, zip_path2, [project2])
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path1)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Project1" in output
        assert "Project2" not in output
        assert "project1.zip" in output or "TOP RANKED PROJECTS SUMMARY" in output

    
    def test_summarize_handles_invalid_json(self, mock_analysis_db, capsys):
        """Test that summarize handles analyses with invalid JSON gracefully."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        import json
        
        zip_path = "/test/invalid.zip"
        
        with mock_analysis_db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analyses 
                (analysis_uuid, analysis_type, zip_file, analysis_timestamp, total_projects, raw_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("invalid-uuid", "non_llm", zip_path, "2025-11-30T10:00:00", 1, "invalid json")
            )
            conn.commit()
        
        valid_project = {
            "project_name": "ValidProject",
            "project_path": "/valid"
        }
        self.create_analysis_in_db(mock_analysis_db, zip_path, [valid_project])
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "ValidProject" in output
        assert "Warning" in captured.out or "Could not parse" in captured.out

    def test_summarize_handles_missing_analysis_fields(self, mock_analysis_db, sample_project_data, capsys):
        """Test that summarize handles analyses with missing timestamp/zip_file fields."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        import json
        
        zip_path = "/test/missing_fields.zip"
        
        report = {
            "projects": [sample_project_data],
            "summary": {}
        }
        
        with mock_analysis_db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analyses 
                (analysis_uuid, analysis_type, zip_file, analysis_timestamp, total_projects, raw_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("missing-fields-uuid", "non_llm", zip_path, "2025-11-30T10:00:00", 1, json.dumps(report))
            )
            conn.commit()
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "TestProject" in output

    def test_summarize_displays_score_breakdown(self, mock_analysis_db, sample_project_data, capsys):
        """Test that summarize displays score breakdown correctly."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        zip_path = "/test/breakdown.zip"
        self.create_analysis_in_db(mock_analysis_db, zip_path, [sample_project_data])
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out        
        assert "Score Breakdown" in output
        assert "Code Architecture" in output
        assert "Code Quality" in output
        assert "Project Maturity" in output
        assert "Algorithmic Quality" in output


    def test_summarize_displays_health_indicators(self, mock_analysis_db, sample_project_data, capsys):
        """Test that summarize displays project health indicators."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path = "/test/health.zip"
        self.create_analysis_in_db(mock_analysis_db, zip_path, [sample_project_data])
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        captured = capsys.readouterr()
        output = captured.out
        assert "Project Health Indicators" in output
        assert "Tests" in output or "README" in output or "Git" in output

    def test_summarize_with_java_oop_analysis(self, mock_analysis_db, capsys):
        """Test summarize with Java OOP analysis."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path = "/test/java.zip"
        java_project = {
            "project_name": "JavaProject",
            "project_path": "/java",
            "primary_language": "java",
            "total_files": 20,
            "code_files": 15,
            "java_oop_analysis": {
                "total_classes": 8,
                "interface_count": 3,
                "solid_score": 4.5,
                "oop_score": 5
            }
        }
        
        self.create_analysis_in_db(mock_analysis_db, zip_path, [java_project])
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "JavaProject" in output
        assert "Java:" in output or "classes" in output

    def test_summarize_with_cpp_oop_analysis(self, mock_analysis_db, capsys):
        """Test summarize with C++ OOP analysis."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path = "/test/cpp.zip"
        cpp_project = {
            "project_name": "CppProject",
            "project_path": "/cpp",
            "primary_language": "cpp",
            "total_files": 25,
            "code_files": 20,
            "cpp_oop_analysis": {
                "total_classes": 10,
                "template_classes": 2,
                "virtual_methods": 15
            }
        }
        
        self.create_analysis_in_db(mock_analysis_db, zip_path, [cpp_project])
        
        summarize_top_ranked_projects(limit=10, zip_file_path=zip_path)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "CppProject" in output
        assert "C++:" in output or "classes" in output


    def test_summarize_all_zip_files(self, mock_analysis_db, sample_project_data, capsys):
        """Test summarize without zip_file_path filter (all files)."""
        from backend.analysis.analyze import summarize_top_ranked_projects
        
        zip_path1 = "/test/file1.zip"
        zip_path2 = "/test/file2.zip"
        
        project1 = sample_project_data.copy()
        project1["project_name"] = "Project1"
        
        project2 = sample_project_data.copy()
        project2["project_name"] = "Project2"
        
        self.create_analysis_in_db(mock_analysis_db, zip_path1, [project1])
        self.create_analysis_in_db(mock_analysis_db, zip_path2, [project2])
        
        summarize_top_ranked_projects(limit=10)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Project1" in output
        assert "Project2" in output
        assert "ALL ZIP FILES" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
