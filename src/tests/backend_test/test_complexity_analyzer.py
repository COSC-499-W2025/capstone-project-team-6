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
                file_path="test.py",
                line_number=1,
                complexity_type="set_operations",
                severity="good_practice",
                description="Set",
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
                file_path="test.py",
                line_number=3,
                complexity_type="nested_loops",
                severity="suggestion",
                description="Loop",
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


class TestJavaComplexityAnalyzer:
    """Test suite for Java complexity analysis."""

    def test_nested_loops_detection_java(self):
        """Test detection of nested loops (O(n²)) in Java code."""
        code = """
public class Test {
    public boolean findDuplicates(int[] arr) {
        for (int i = 0; i < arr.length; i++) {
            for (int j = i + 1; j < arr.length; j++) {
                if (arr[i] == arr[j]) {
                    return true;
                }
            }
        }
        return false;
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        nested_loop_insights = [i for i in insights if i.complexity_type == "nested_loops"]
        assert len(nested_loop_insights) >= 1
        assert "O(n²)" in nested_loop_insights[0].description

    def test_hashset_usage_java(self):
        """Test detection of HashSet usage (efficient data structure)."""
        code = """
public class Test {
    public void removeDuplicates() {
        Set<String> uniqueNames = new HashSet<>();
        uniqueNames.add("Alice");
        return uniqueNames.contains("Bob");
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        hashset_insights = [i for i in insights if i.complexity_type == "efficient_data_structure"]
        assert len(hashset_insights) >= 1
        assert any("HashSet" in i.description for i in hashset_insights)
        assert hashset_insights[0].severity == "good_practice"

    def test_hashmap_usage_java(self):
        """Test detection of HashMap usage."""
        code = """
public class Test {
    public Map<String, Integer> countFrequencies(String[] items) {
        Map<String, Integer> freq = new HashMap<>();
        for (String item : items) {
            freq.put(item, freq.getOrDefault(item, 0) + 1);
        }
        return freq;
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        hashmap_insights = [i for i in insights if i.complexity_type == "efficient_data_structure"]
        assert len(hashmap_insights) >= 1
        assert any("HashMap" in i.description for i in hashmap_insights)

    def test_stream_operations_java(self):
        """Test detection of Java Stream API usage."""
        code = """
public class Test {
    public List<String> processData(List<Integer> numbers) {
        return numbers.stream()
            .filter(x -> x > 0)
            .map(String::valueOf)
            .collect(Collectors.toList());
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        stream_insights = [i for i in insights if i.complexity_type == "stream_operations"]
        assert len(stream_insights) >= 3  # stream(), filter(), map(), collect()
        assert all(i.severity == "good_practice" for i in stream_insights)

    def test_parallel_stream_java(self):
        """Test detection of parallel stream usage."""
        code = """
public class Test {
    public long countLargeNumbers(List<Integer> numbers) {
        return numbers.parallelStream()
            .filter(x -> x > 1000)
            .count();
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        parallel_insights = [i for i in insights if "parallel" in i.description.lower()]
        assert len(parallel_insights) >= 1
        assert "efficient" in parallel_insights[0].description.lower()

    def test_binary_search_java(self):
        """Test detection of binary search in Java."""
        code = """
public class Test {
    public int findPosition(int[] arr, int target) {
        int index = Arrays.binarySearch(arr, target);
        return index;
    }
    
    public int findInList(List<Integer> list, int target) {
        return Collections.binarySearch(list, target);
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        binary_insights = [i for i in insights if i.complexity_type == "binary_search"]
        assert len(binary_insights) >= 2
        assert all("O(log n)" in i.description for i in binary_insights)

    def test_string_builder_java(self):
        """Test detection of StringBuilder usage."""
        code = """
public class Test {
    public String concatenateStrings(List<String> items) {
        StringBuilder sb = new StringBuilder();
        for (String item : items) {
            sb.append(item);
        }
        return sb.toString();
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        sb_insights = [i for i in insights if i.complexity_type == "string_builder"]
        assert len(sb_insights) >= 1
        assert "StringBuilder" in sb_insights[0].description
        assert "O(n)" in sb_insights[0].description

    def test_inefficient_string_concat_java(self):
        """Test detection of inefficient string concatenation in loops."""
        code = """
public class Test {
    public String buildString(int n) {
        String result = "";
        for (int i = 0; i < n; i++) {
            result += "item" + i;
        }
        return result;
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        inefficient_insights = [i for i in insights if i.complexity_type == "inefficient_string_concat"]
        assert len(inefficient_insights) >= 1
        assert "StringBuilder" in inefficient_insights[0].description
        assert inefficient_insights[0].severity == "suggestion"

    def test_concurrent_hashmap_java(self):
        """Test detection of concurrent collections."""
        code = """
public class Test {
    private Map<String, Integer> cache = new ConcurrentHashMap<>();
    
    public void updateCache(String key, int value) {
        cache.put(key, value);
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        concurrent_insights = [i for i in insights if i.complexity_type == "concurrent_collection"]
        assert len(concurrent_insights) >= 1
        assert "Thread-safe" in concurrent_insights[0].description

    def test_treeset_usage_java(self):
        """Test detection of TreeSet (sorted set)."""
        code = """
public class Test {
    public void maintainSorted() {
        Set<Integer> sortedSet = new TreeSet<>();
        sortedSet.add(5);
        sortedSet.add(1);
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        treeset_insights = [i for i in insights if "TreeSet" in i.description]
        assert len(treeset_insights) >= 1
        assert "O(log n)" in treeset_insights[0].description

    def test_empty_java_file(self):
        """Test analysis of empty Java file."""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Empty.java", "")
        assert insights == []

    def test_java_syntax_error_handling(self):
        """Test that Java syntax errors don't crash the analyzer."""
        code = """
public class Broken {
    public void broken( {
        for int i
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        # Should return empty list, not crash
        insights = analyze_java_file("Broken.java", code)
        assert isinstance(insights, list)

    def test_triple_nested_loops_java(self):
        """Test detection of triple nested loops (O(n³))."""
        code = """
public class Test {
    public void processMatrix(int[][][] matrix) {
        for (int i = 0; i < matrix.length; i++) {
            for (int j = 0; j < matrix[0].length; j++) {
                for (int k = 0; k < matrix[0][0].length; k++) {
                    process(matrix[i][j][k]);
                }
            }
        }
    }
}
"""
        from backend.analysis.complexity_analyzer import analyze_java_file

        insights = analyze_java_file("Test.java", code)
        nested_loop_insights = [i for i in insights if i.complexity_type == "nested_loops"]
        # Should detect multiple levels of nesting
        assert len(nested_loop_insights) >= 2


class TestJavaProjectAnalysis:
    """Test analyzing Java projects."""

    def test_analyze_java_project(self):
        """Test analyzing multiple Java files together."""
        from backend.analysis.complexity_analyzer import analyze_java_project

        files = [
            (
                "Main.java",
                """
public class Main {
    public void nestedLoop() {
        for (int i = 0; i < 10; i++) {
            for (int j = 0; j < 10; j++) {
                System.out.println(i * j);
            }
        }
    }
}
""",
            ),
            (
                "Utils.java",
                """
public class Utils {
    public Set<String> deduplicate(List<String> items) {
        return new HashSet<>(items);
    }
}
""",
            ),
        ]

        report = analyze_java_project(files)

        assert report.total_files_analyzed == 2
        assert len(report.insights) >= 2
        assert report.optimization_score > 0


class TestMixedLanguageAnalysis:
    """Test analyzing projects with both Python and Java."""

    def test_analyze_mixed_project(self):
        """Test auto-detection and analysis of mixed Python/Java project."""
        from backend.analysis.complexity_analyzer import analyze_project

        files = [
            (
                "utils.py",
                """
def find_duplicates(items):
    seen = set()
    for item in items:
        if item in seen:
            return True
        seen.add(item)
    return False
""",
            ),
            (
                "Helper.java",
                """
public class Helper {
    public Map<String, Integer> count(String[] items) {
        Map<String, Integer> counts = new HashMap<>();
        return counts;
    }
}
""",
            ),
        ]

        report = analyze_project(files, language="auto")

        assert report.total_files_analyzed == 2
        # Should have insights from both languages
        assert len(report.insights) >= 2
        # Should have both Python and Java patterns
        assert any("set" in i.complexity_type.lower() for i in report.insights)
        assert any("efficient_data_structure" in i.complexity_type for i in report.insights)

    def test_analyze_project_python_only(self):
        """Test analyzing Python-only project with auto-detect."""
        from backend.analysis.complexity_analyzer import analyze_project

        files = [("test.py", "x = set()")]

        report = analyze_project(files, language="auto")
        assert report.total_files_analyzed == 1

    def test_analyze_project_java_only(self):
        """Test analyzing Java-only project with auto-detect."""
        from backend.analysis.complexity_analyzer import analyze_project

        files = [("Test.java", "Set<String> x = new HashSet<>();")]

        report = analyze_project(files, language="auto")
        assert report.total_files_analyzed == 1

    def test_analyze_project_explicit_language(self):
        """Test analyzing with explicit language parameter."""
        from backend.analysis.complexity_analyzer import analyze_project

        python_files = [("test.py", "x = set()")]
        java_files = [("Test.java", "Set<String> x = new HashSet<>();")]

        py_report = analyze_project(python_files, language="python")
        assert py_report.total_files_analyzed == 1

        java_report = analyze_project(java_files, language="java")
        assert java_report.total_files_analyzed == 1


class TestJavaScoreCalculation:
    """Test score calculation with Java patterns."""

    def test_score_with_java_good_practices(self):
        """Test score increases with Java good practices."""
        from backend.analysis.complexity_analyzer import (ComplexityInsight,
                                                          ComplexityReport)

        report = ComplexityReport(total_files_analyzed=1)

        # Add Java good practices
        for pattern in [
            "stream_operations",
            "efficient_data_structure",
            "string_builder",
        ]:
            report.add_insight(
                ComplexityInsight(
                    file_path="Test.java",
                    line_number=1,
                    complexity_type=pattern,
                    severity="good_practice",
                    description="Good practice",
                )
            )

        report.calculate_score()
        assert report.optimization_score > 60  # Should have good score

    def test_score_with_java_bad_practices(self):
        """Test score decreases with Java inefficiencies."""
        from backend.analysis.complexity_analyzer import (ComplexityInsight,
                                                          ComplexityReport)

        report = ComplexityReport(total_files_analyzed=1)

        # Add Java bad practices
        report.add_insight(
            ComplexityInsight(
                file_path="Test.java",
                line_number=1,
                complexity_type="nested_loops",
                severity="suggestion",
                description="Nested loops",
            )
        )
        report.add_insight(
            ComplexityInsight(
                file_path="Test.java",
                line_number=5,
                complexity_type="inefficient_string_concat",
                severity="suggestion",
                description="String concat in loop",
            )
        )

        report.calculate_score()
        assert report.optimization_score < 50  # Should have lower score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
