"""
Comprehensive tests for the complexity analyzer module.

Tests cover:
- Nested loop detection (O(n²), O(n³))
- Efficient data structure usage (sets, dicts)
- List comprehensions and generators
- Sorting operations
- Binary search usage
- Memoization
- Inefficient patterns (list lookups in loops)
"""

import zipfile
from pathlib import Path

import pytest

from backend.analysis.complexity_analyzer import (ComplexityInsight,
                                                   ComplexityReport,
                                                   analyze_python_file,
                                                   analyze_python_project,
                                                   format_report)
from backend.analysis.project_analyzer import FileClassifier


class TestComplexityAnalyzer:
    """Test suite for complexity analysis."""

    def test_nested_loops_detection(self):
        """Test detection of nested loops (O(n²))."""
        code = """
def find_duplicates(arr):
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j]:
                return True
    return False
"""
        insights = analyze_python_file("test.py", code)

        # Should detect nested loops
        nested_loop_insights = [i for i in insights if i.complexity_type == "nested_loops"]
        assert len(nested_loop_insights) >= 1
        assert "O(n²)" in nested_loop_insights[0].description

    def test_triple_nested_loops(self):
        """Test detection of triple nested loops (O(n³))."""
        code = """
def triple_loop(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            for k in range(10):
                process(matrix[i][j], k)
"""
        insights = analyze_python_file("test.py", code)

        nested_loop_insights = [i for i in insights if i.complexity_type == "nested_loops"]
        # Should detect at least 2 nested loop warnings (depth 2 and depth 3)
        assert len(nested_loop_insights) >= 2

    def test_set_usage_good_practice(self):
        """Test detection of efficient set usage."""
        code = """
def remove_duplicates(items):
    return list(set(items))

def check_membership():
    seen = set()
    seen.add(1)
    return 1 in seen
"""
        insights = analyze_python_file("test.py", code)

        set_insights = [i for i in insights if "set" in i.complexity_type.lower()]
        assert len(set_insights) >= 1
        assert any(i.severity == "good_practice" for i in set_insights)

    def test_dict_usage_good_practice(self):
        """Test detection of efficient dictionary usage."""
        code = """
def count_frequencies(items):
    freq = {}
    for item in items:
        freq[item] = freq.get(item, 0) + 1
    return freq

def lookup_table():
    cache = dict()
    return cache
"""
        insights = analyze_python_file("test.py", code)

        dict_insights = [i for i in insights if "dict" in i.complexity_type.lower()]
        assert len(dict_insights) >= 1
        assert any(i.severity == "good_practice" for i in dict_insights)

    def test_list_comprehension_detection(self):
        """Test detection of list comprehensions (good practice)."""
        code = """
def process_items(items):
    # Good: list comprehension
    squared = [x * x for x in items]
    return squared
"""
        insights = analyze_python_file("test.py", code)

        comp_insights = [i for i in insights if i.complexity_type == "list_comprehension"]
        assert len(comp_insights) >= 1
        assert comp_insights[0].severity == "good_practice"

    def test_generator_expression_detection(self):
        """Test detection of generator expressions (memory efficient)."""
        code = """
def sum_squares(n):
    return sum(x * x for x in range(n))
"""
        insights = analyze_python_file("test.py", code)

        gen_insights = [i for i in insights if i.complexity_type == "generator_expression"]
        assert len(gen_insights) >= 1
        assert gen_insights[0].severity == "good_practice"

    def test_sorting_with_key_function(self):
        """Test detection of sorting with custom key (good practice)."""
        code = """
def sort_by_length(words):
    return sorted(words, key=len)

def sort_complex():
    items.sort(key=lambda x: x.value)
"""
        insights = analyze_python_file("test.py", code)

        sort_insights = [i for i in insights if i.complexity_type == "sorting_with_key"]
        assert len(sort_insights) >= 2
        assert all(i.severity == "good_practice" for i in sort_insights)

    def test_binary_search_detection(self):
        """Test detection of binary search usage."""
        code = """
import bisect

def find_position(sorted_list, value):
    index = bisect.bisect_left(sorted_list, value)
    return index
"""
        insights = analyze_python_file("test.py", code)

        bisect_insights = [i for i in insights if i.complexity_type == "binary_search"]
        assert len(bisect_insights) >= 1
        assert "O(log n)" in bisect_insights[0].description

    def test_memoization_detection(self):
        """Test detection of memoization decorators."""
        code = """
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        insights = analyze_python_file("test.py", code)

        memo_insights = [i for i in insights if i.complexity_type == "memoization"]
        assert len(memo_insights) >= 1
        assert "caching" in memo_insights[0].description.lower()

    def test_inefficient_membership_test(self):
        """Test detection of inefficient membership tests in loops."""
        code = """
def check_items(data_list, search_items):
    found = []
    for item in search_items:
        if item in data_list:  # O(n) lookup in list
            found.append(item)
    return found
"""
        insights = analyze_python_file("test.py", code)

        inefficient = [i for i in insights if "inefficient" in i.complexity_type.lower()]
        # Should suggest using set or dict
        assert len(inefficient) >= 1

    def test_syntax_error_handling(self):
        """Test that syntax errors don't crash the analyzer."""
        code = """
def broken syntax here:
    for i in range(
"""
        # Should return empty list, not crash
        insights = analyze_python_file("test.py", code)
        assert insights == []

    def test_empty_file(self):
        """Test analysis of empty file."""
        insights = analyze_python_file("test.py", "")
        assert insights == []

    def test_no_complexity_patterns(self):
        """Test file with simple code and no notable patterns."""
        code = """
def add(a, b):
    return a + b

def greet(name):
    print(f"Hello, {name}")
"""
        insights = analyze_python_file("test.py", code)
        # Should have no insights or only neutral ones
        assert len(insights) == 0


class TestComplexityReport:
    """Test the ComplexityReport class."""

    def test_report_initialization(self):
        """Test report starts with correct defaults."""
        report = ComplexityReport()
        assert report.total_files_analyzed == 0
        assert report.insights == []
        assert report.optimization_score == 0.0
        assert report.summary == {}

    def test_add_insight(self):
        """Test adding insights to report."""
        report = ComplexityReport(total_files_analyzed=1)
        insight = ComplexityInsight(
            file_path="test.py",
            line_number=5,
            complexity_type="nested_loops",
            severity="suggestion",
            description="Test insight",
        )

        report.add_insight(insight)

        assert len(report.insights) == 1
        assert report.summary["nested_loops"] == 1

    def test_score_calculation_good_practices(self):
        """Test score calculation with good practices."""
        report = ComplexityReport(total_files_analyzed=1)

        # Add several good practices
        for i in range(5):
            report.add_insight(
                ComplexityInsight(
                    file_path="test.py",
                    line_number=i,
                    complexity_type="efficient_data_structure",
                    severity="good_practice",
                    description="Good",
                )
            )

        report.calculate_score()
        # Should have high score (50 base + good practices)
        assert report.optimization_score > 50

    def test_score_calculation_bad_practices(self):
        """Test score calculation with inefficient patterns."""
        report = ComplexityReport(total_files_analyzed=1)

        # Add nested loops
        for i in range(3):
            report.add_insight(
                ComplexityInsight(
                    file_path="test.py",
                    line_number=i,
                    complexity_type="nested_loops",
                    severity="suggestion",
                    description="Nested",
                )
            )

        report.calculate_score()
        # Should have lower score
        assert report.optimization_score < 50

    def test_score_calculation_mixed(self):
        """Test score with both good and bad patterns."""
        report = ComplexityReport(total_files_analyzed=1)

        # Add good practices
        report.add_insight(
            ComplexityInsight(
                file_path="test.py", line_number=1, complexity_type="set_operations", severity="good_practice", description="Set"
            )
        )
        report.add_insight(
            ComplexityInsight(
                file_path="test.py",
                line_number=2,
                complexity_type="list_comprehension",
                severity="good_practice",
                description="Comp",
            )
        )

        # Add bad practice
        report.add_insight(
            ComplexityInsight(
                file_path="test.py", line_number=3, complexity_type="nested_loops", severity="suggestion", description="Loop"
            )
        )

        report.calculate_score()
        # Should be around 50 (base + good - bad)
        assert 40 <= report.optimization_score <= 60

    def test_score_clamped_to_range(self):
        """Test that score stays in 0-100 range."""
        report = ComplexityReport(total_files_analyzed=1)

        # Add tons of good practices
        for i in range(20):
            report.add_insight(
                ComplexityInsight(
                    file_path="test.py",
                    line_number=i,
                    complexity_type="efficient_data_structure",
                    severity="good_practice",
                    description="Good",
                )
            )

        report.calculate_score()
        assert 0 <= report.optimization_score <= 100


class TestProjectAnalysis:
    """Test analyzing multiple files in a project."""

    def test_analyze_multiple_files(self):
        """Test analyzing several Python files together."""
        files = [
            (
                "file1.py",
                """
def nested():
    for i in range(10):
        for j in range(10):
            pass
""",
            ),
            (
                "file2.py",
                """
def efficient():
    seen = set()
    return 1 in seen
""",
            ),
        ]

        report = analyze_python_project(files)

        assert report.total_files_analyzed == 2
        assert len(report.insights) >= 2
        assert report.optimization_score > 0

    def test_empty_project(self):
        """Test analyzing project with no files."""
        report = analyze_python_project([])
        assert report.total_files_analyzed == 0
        assert report.optimization_score == 0.0


class TestFormatReport:
    """Test report formatting."""

    def test_format_empty_report(self):
        """Test formatting empty report."""
        report = ComplexityReport()
        output = format_report(report)
        assert "No Python files analyzed" in output

    def test_format_report_with_insights(self):
        """Test formatting report with insights."""
        report = ComplexityReport(total_files_analyzed=2)
        report.add_insight(
            ComplexityInsight(
                file_path="test.py",
                line_number=5,
                complexity_type="nested_loops",
                severity="suggestion",
                description="Nested loop detected",
            )
        )
        report.calculate_score()

        output = format_report(report, verbose=False)

        assert "Files Analyzed: 2" in output
        assert "Optimization Awareness Score" in output
        assert "SUMMARY" in output

    def test_format_report_verbose(self):
        """Test verbose report formatting."""
        report = ComplexityReport(total_files_analyzed=1)
        report.add_insight(
            ComplexityInsight(
                file_path="test.py",
                line_number=10,
                complexity_type="set_operations",
                severity="good_practice",
                description="Set used efficiently",
                code_snippet="seen = set()",
            )
        )
        report.calculate_score()

        output = format_report(report, verbose=True)

        assert "DETAILED FINDINGS" in output
        assert "test.py" in output
        assert "Line 10" in output
        assert "seen = set()" in output


class TestIntegrationWithFileClassifier:
    """Test integration with the FileClassifier."""

    def test_analyze_python_complexity_with_zip(self, tmp_path):
        """Test complexity analysis on a real ZIP file."""
        # Create a test ZIP with Python files
        zip_path = tmp_path / "test_project.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            # Add a Python file with nested loops
            zf.writestr(
                "project/main.py",
                """
def find_pairs(numbers):
    pairs = []
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            pairs.append((numbers[i], numbers[j]))
    return pairs
""",
            )

            # Add a Python file with good practices
            zf.writestr(
                "project/utils.py",
                """
from functools import lru_cache

@lru_cache(maxsize=128)
def compute(n):
    return n * n

def deduplicate(items):
    return list(set(items))
""",
            )

        # Analyze with FileClassifier
        with FileClassifier(zip_path) as classifier:
            result = classifier.analyze_python_complexity("project")

            assert result["total_files"] == 2
            assert result["score"] > 0
            assert "summary" in result
            assert result["insights_count"] >= 2

    def test_analyze_non_python_project(self, tmp_path):
        """Test complexity analysis on project with no Python files."""
        zip_path = tmp_path / "no_python.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("project/README.md", "# Test Project")
            zf.writestr("project/data.json", '{"key": "value"}')

        with FileClassifier(zip_path) as classifier:
            result = classifier.analyze_python_complexity("project")

            assert result["total_files"] == 0
            assert "No Python files found" in result["message"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_large_file(self):
        """Test that very large files are handled gracefully."""
        # Create a file with many lines
        code = "\n".join([f"x{i} = {i}" for i in range(10000)])
        insights = analyze_python_file("large.py", code)
        # Should complete without issues
        assert isinstance(insights, list)

    def test_unicode_content(self):
        """Test handling of Unicode characters."""
        code = """
def greet():
    message = "Hello, 世界! 🌍"
    return message
"""
        insights = analyze_python_file("unicode.py", code)
        assert isinstance(insights, list)

    def test_mixed_indentation(self):
        """Test handling of mixed tabs/spaces (may cause syntax error)."""
        code = """
def mixed():
\tx = 1
    y = 2
    return x + y
"""
        # Should handle gracefully (either parse or return empty)
        insights = analyze_python_file("mixed.py", code)
        assert isinstance(insights, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
