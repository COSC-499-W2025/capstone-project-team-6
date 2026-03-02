"""
Comprehensive Test Suite for C OOP-Style Analyzer

Test projects are generated automatically - no downloads needed!

Requirements:
    pip install pytest libclang

Run tests:
    pytest test_c_analysis.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Fix paths for actual project structure
# test_c_analysis.py is in: src/tests/backend_test/
# c_oop_analyzer.py is in: src/backend/analysis/
current_file = Path(__file__).resolve()
backend_test_dir = current_file.parent  # src/tests/backend_test
tests_dir = backend_test_dir.parent  # src/tests
src_dir = tests_dir.parent  # src
backend_dir = src_dir / "backend"  # src/backend
analysis_dir = backend_dir / "analysis"  # src/backend/analysis

# Add to path BEFORE imports
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(analysis_dir))
sys.path.insert(0, str(backend_test_dir))

try:
    # Import the analyzer - use relative imports since we added analysis_dir to path
    # Verify libclang is available
    import clang.cindex

    # Import the project generator (in same directory as this test file)
    from project_generator import generate_all_test_projects

    from backend.analysis.c_oop_analyzer import (
        COOPAnalysis,
        analyze_c_file,
        analyze_c_project,
        calculate_encapsulation_ratio,
        calculate_memory_safety_score,
        calculate_oop_score,
        calculate_solid_score,
        get_coding_style,
    )

    CLANG_AVAILABLE = True
except ImportError as e:
    CLANG_AVAILABLE = False
    print(f"Import failed: {e}")
    print(f"\nDEBUG INFO:")
    print(f"  Current file: {current_file}")
    print(f"  Analysis dir: {analysis_dir}")
    print(f"  c_oop_analyzer.py exists: {(analysis_dir / 'c_oop_analyzer.py').exists()}")
    print(f"  project_generator.py exists: {(backend_test_dir / 'project_generator.py').exists()}")
    pytestmark = pytest.mark.skip(reason=f"Required dependencies not installed: {e}")


# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture(scope="module")
def test_projects():
    """Generate all test projects automatically."""
    if not CLANG_AVAILABLE:
        pytest.skip("libclang not available")

    result = generate_all_test_projects()
    yield result

    # Cleanup
    import shutil

    shutil.rmtree(result["base_dir"], ignore_errors=True)


@pytest.fixture(scope="module")
def test_projects_dir(test_projects):
    """Path to directory containing test project ZIP files."""
    return test_projects["base_dir"]


# ==============================================================================
# UNIT TESTS
# ==============================================================================


@pytest.mark.skipif(not CLANG_AVAILABLE, reason="libclang not installed")
class TestCOOPAnalysis:
    """Test the COOPAnalysis data class."""

    def test_oop_analysis_creation(self):
        """Test creating a COOPAnalysis object."""
        analysis = COOPAnalysis()
        assert analysis.total_structs == 0
        assert analysis.total_functions == 0
        assert analysis.static_functions == 0
        assert analysis.opaque_pointer_structs == 0
        assert analysis.design_patterns == []

    def test_oop_analysis_to_dict(self):
        """Test converting COOPAnalysis to dictionary."""
        analysis = COOPAnalysis(total_structs=5, total_functions=20, static_functions=10)
        result = analysis.to_dict()
        assert isinstance(result, dict)
        assert result["total_structs"] == 5
        assert result["total_functions"] == 20
        assert result["static_functions"] == 10


@pytest.mark.skipif(not CLANG_AVAILABLE, reason="libclang not installed")
class TestAnalyzeCFile:
    """Test the analyze_c_file function."""

    def test_empty_file(self):
        """Test analyzing an empty C file."""
        code = ""
        result = analyze_c_file(code, "test.c")

        assert result.total_structs == 0
        assert result.total_functions == 0
        assert result.static_functions == 0

    def test_simple_struct(self):
        """Test detecting a simple struct."""
        code = """
struct Point {
    int x;
    int y;
};
"""
        result = analyze_c_file(code, "test.c")

        assert result.total_structs == 1

    def test_function_detection(self):
        """Test detecting functions."""
        code = """
int add(int a, int b) {
    return a + b;
}

static int multiply(int a, int b) {
    return a * b;
}
"""
        result = analyze_c_file(code, "test.c")

        assert result.total_functions == 2
        assert result.static_functions == 1

    def test_oop_naming(self):
        """Test detecting OOP-style naming."""
        code = """
void Vector_push(int value) {}
void String_append(char* str) {}
void helper_function() {}
"""
        result = analyze_c_file(code, "test.c")

        assert result.oop_style_naming_count == 2

    def test_function_pointers(self):
        """Test detecting function pointers in structs."""
        code = """
struct Operations {
    int (*add)(int, int);
    int (*subtract)(int, int);
    int (*multiply)(int, int);
};
"""
        result = analyze_c_file(code, "test.c")

        assert result.function_pointer_fields == 3
        assert result.vtable_structs == 1

    def test_malloc_free(self):
        """Test detecting malloc and free usage."""
        code = """
#include <stdlib.h>

void* allocate() {
    return malloc(100);
}

void deallocate(void* ptr) {
    free(ptr);
}
"""
        result = analyze_c_file(code, "test.c")

        assert result.malloc_usage >= 1
        assert result.free_usage >= 1

    def test_factory_pattern(self):
        """Test detecting Factory pattern."""
        code = """
struct Object* Object_create() {
    return malloc(sizeof(struct Object));
}
"""
        result = analyze_c_file(code, "test.c")

        assert "Factory" in result.design_patterns


@pytest.mark.skipif(not CLANG_AVAILABLE, reason="libclang not installed")
class TestCompleteProjects:
    """Test analysis on complete projects."""

    def test_minimal_project(self, test_projects_dir):
        """Test minimal procedural C project."""
        zip_path = test_projects_dir / "1_minimal.zip"

        result = analyze_c_project(zip_path)
        analysis = result["c_oop_analysis"]

        assert analysis["total_functions"] >= 2
        oop_score = calculate_oop_score(COOPAnalysis(**analysis))

        assert oop_score <= 2

    def test_basic_struct_project(self, test_projects_dir):
        """Test basic struct project."""
        zip_path = test_projects_dir / "2_basic_struct.zip"

        result = analyze_c_project(zip_path)
        analysis = result["c_oop_analysis"]

        assert analysis["total_structs"] >= 1
        assert analysis["oop_style_naming_count"] >= 2

        oop_score = calculate_oop_score(COOPAnalysis(**analysis))
        assert 2 <= oop_score <= 4

    def test_vector_project(self, test_projects_dir):
        """Test vector library with OOP patterns."""
        zip_path = test_projects_dir / "3_vector.zip"

        result = analyze_c_project(zip_path)
        analysis = result["c_oop_analysis"]

        assert analysis["total_structs"] >= 1
        assert analysis["opaque_pointer_structs"] >= 1
        assert analysis["malloc_usage"] >= 1
        assert analysis["free_usage"] >= 1
        assert "Factory" in analysis["design_patterns"]

        oop_score = calculate_oop_score(COOPAnalysis(**analysis))
        assert oop_score >= 4

    def test_polymorphism_project(self, test_projects_dir):
        """Test polymorphism via function pointers."""
        zip_path = test_projects_dir / "4_polymorphism.zip"

        result = analyze_c_project(zip_path)
        analysis = result["c_oop_analysis"]

        assert analysis["function_pointer_fields"] >= 3
        assert analysis["vtable_structs"] >= 1
        assert "Strategy" in analysis["design_patterns"]

        oop_score = calculate_oop_score(COOPAnalysis(**analysis))
        assert oop_score >= 5

    def test_complete_project(self, test_projects_dir):
        """Test complete library with all patterns."""
        zip_path = test_projects_dir / "5_complete.zip"

        result = analyze_c_project(zip_path)
        analysis = result["c_oop_analysis"]

        assert analysis["total_structs"] >= 2
        assert analysis["total_functions"] >= 10

        oop_score = calculate_oop_score(COOPAnalysis(**analysis))
        assert oop_score >= 5


@pytest.mark.skipif(not CLANG_AVAILABLE, reason="libclang not installed")
class TestScoringFunctions:
    """Test OOP and SOLID scoring functions."""

    def test_calculate_oop_score_empty(self):
        """Test OOP score for empty analysis."""
        analysis = COOPAnalysis()
        score = calculate_oop_score(analysis)
        assert score == 0

    def test_calculate_oop_score_full(self):
        """Test OOP score for comprehensive analysis."""
        analysis = COOPAnalysis(
            total_structs=10,
            opaque_pointer_structs=5,
            static_functions=20,
            function_pointer_fields=10,
            vtable_structs=3,
            oop_style_naming_count=25,
            design_patterns=["Factory", "Strategy"],
        )
        score = calculate_oop_score(analysis)
        assert score == 6

    def test_calculate_solid_score(self):
        """Test SOLID score calculation."""
        analysis = COOPAnalysis(
            total_structs=10,
            total_functions=100,
            static_functions=50,
            vtable_structs=3,
            header_functions=20,
            implementation_functions=80,
        )
        score = calculate_solid_score(analysis)
        assert 0.0 <= score <= 3.0

    def test_get_coding_style(self):
        """Test coding style determination."""
        assert get_coding_style(0) == "Pure Procedural"
        assert get_coding_style(1) == "Structured C"
        assert get_coding_style(3) == "OOP-Influenced C"
        assert get_coding_style(6) == "Advanced OOP-Style C"

    def test_encapsulation_ratio(self):
        """Test encapsulation ratio calculation."""
        analysis = COOPAnalysis(total_functions=10, static_functions=7)
        ratio = calculate_encapsulation_ratio(analysis)
        assert ratio == 70.0

    def test_memory_safety_score(self):
        """Test memory safety score calculation."""
        analysis = COOPAnalysis(constructor_destructor_pairs=5, malloc_usage=10, free_usage=10)
        score = calculate_memory_safety_score(analysis)
        assert score == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
