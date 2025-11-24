"""
Time Complexity Analysis for Python Code

Analyzes Python source code to detect patterns indicating awareness (or lack thereof)
of algorithmic complexity and optimization techniques.

Detects:
- Nested loops (O(n²), O(n³))
- Use of efficient data structures (sets, dicts vs lists for lookups)
- Sorting operations
- Known algorithm patterns (binary search, two-pointer, etc.)
- Optimization opportunities
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ComplexityInsight:
    """Represents a complexity-related finding in code."""

    file_path: str
    line_number: int
    complexity_type: str  # e.g., "nested_loops", "inefficient_lookup", "good_optimization"
    severity: str  # "info", "suggestion", "good_practice"
    description: str
    code_snippet: Optional[str] = None


@dataclass
class ComplexityReport:
    """Report summarizing complexity analysis for a project."""

    total_files_analyzed: int = 0
    insights: List[ComplexityInsight] = field(default_factory=list)
    optimization_score: float = 0.0  # 0-100, higher is better
    summary: Dict[str, int] = field(default_factory=dict)

    def add_insight(self, insight: ComplexityInsight) -> None:
        """Add an insight to the report."""
        self.insights.append(insight)
        # Update summary counts
        key = insight.complexity_type
        self.summary[key] = self.summary.get(key, 0) + 1

    def calculate_score(self) -> None:
        """Calculate optimization awareness score based on findings."""
        if self.total_files_analyzed == 0:
            self.optimization_score = 0.0
            return

        # Start with base score
        score = 50.0

        # Positive indicators (add points)
        good_practices = self.summary.get("efficient_data_structure", 0)
        good_practices += self.summary.get("sorting_with_key", 0)
        good_practices += self.summary.get("set_operations", 0)
        good_practices += self.summary.get("dict_lookup", 0)
        good_practices += self.summary.get("list_comprehension", 0)
        good_practices += self.summary.get("generator_expression", 0)
        good_practices += self.summary.get("binary_search", 0)
        good_practices += self.summary.get("memoization", 0)

        score += min(good_practices * 5, 40)  # Cap at +40

        # Negative indicators (subtract points)
        nested_loops = self.summary.get("nested_loops", 0)
        inefficient_lookups = self.summary.get("inefficient_lookup", 0)
        inefficient_membership = self.summary.get("inefficient_membership_test", 0)

        score -= min(nested_loops * 10, 30)  # Cap at -30
        score -= min(inefficient_lookups * 8, 25)  # Cap at -25
        score -= min(inefficient_membership * 5, 15)  # Cap at -15

        # Clamp between 0 and 100
        self.optimization_score = max(0.0, min(100.0, score))


class ComplexityAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes Python code for complexity patterns."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_lines = source_code.splitlines()
        self.insights: List[ComplexityInsight] = []
        self.loop_depth = 0  # Track nested loop depth
        self.function_locals: Set[str] = set()  # Track local variables in current function

    def get_line(self, line_no: int) -> str:
        """Get source code line by number (1-indexed)."""
        if 1 <= line_no <= len(self.source_lines):
            return self.source_lines[line_no - 1].strip()
        return ""

    def visit_For(self, node: ast.For) -> None:
        """Detect for loops and nested loops."""
        self.loop_depth += 1

        # Check for nested loops (O(n²) or worse)
        if self.loop_depth >= 2:
            severity = "suggestion" if self.loop_depth == 2 else "info"
            complexity = "O(n²)" if self.loop_depth == 2 else f"O(n^{self.loop_depth})"
            self.insights.append(
                ComplexityInsight(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    complexity_type="nested_loops",
                    severity=severity,
                    description=f"Nested loop detected ({complexity} complexity). "
                    f"Consider if this can be optimized with better data structures or algorithms.",
                    code_snippet=self.get_line(node.lineno),
                )
            )

        # Check for inefficient membership tests in loops (x in list)
        for child in ast.walk(node.body[0]) if node.body else []:
            if isinstance(child, ast.Compare):
                # Look for patterns like: if x in some_list
                for op in child.ops:
                    if isinstance(op, (ast.In, ast.NotIn)):
                        # Check if comparing against a list (inefficient)
                        if isinstance(child.comparators[0], ast.Name):
                            var_name = child.comparators[0].id
                            # Heuristic: if variable name suggests it's a list
                            if any(hint in var_name.lower() for hint in ["list", "array", "items"]):
                                self.insights.append(
                                    ComplexityInsight(
                                        file_path=self.file_path,
                                        line_number=child.lineno,
                                        complexity_type="inefficient_membership_test",
                                        severity="suggestion",
                                        description=f"Membership test inside loop on '{var_name}'. "
                                        f"Consider using a set or dict for O(1) lookups instead of O(n).",
                                        code_snippet=self.get_line(child.lineno),
                                    )
                                )

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        """Track while loops for nesting."""
        self.loop_depth += 1

        if self.loop_depth >= 2:
            self.insights.append(
                ComplexityInsight(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    complexity_type="nested_loops",
                    severity="suggestion",
                    description=f"Nested while loop detected. Review for potential optimization.",
                    code_snippet=self.get_line(node.lineno),
                )
            )

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_ListComp(self, node: ast.ListComp) -> None:
        """Detect list comprehensions (good practice)."""
        # List comprehensions are generally more efficient than explicit loops
        if len(node.generators) == 1:  # Single-level comprehension
            self.insights.append(
                ComplexityInsight(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    complexity_type="list_comprehension",
                    severity="good_practice",
                    description="List comprehension used (efficient and Pythonic).",
                    code_snippet=self.get_line(node.lineno),
                )
            )
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        """Detect generator expressions (memory efficient)."""
        self.insights.append(
            ComplexityInsight(
                file_path=self.file_path,
                line_number=node.lineno,
                complexity_type="generator_expression",
                severity="good_practice",
                description="Generator expression used (memory efficient, lazy evaluation).",
                code_snippet=self.get_line(node.lineno),
            )
        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Detect function calls related to complexity."""
        func_name = None

        # Extract function name
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name:
            # Detect sorting operations
            if func_name in ["sort", "sorted"]:
                # Check if using key parameter (good practice)
                has_key = any(kw.arg == "key" for kw in node.keywords)
                if has_key:
                    self.insights.append(
                        ComplexityInsight(
                            file_path=self.file_path,
                            line_number=node.lineno,
                            complexity_type="sorting_with_key",
                            severity="good_practice",
                            description="Sorting with custom key function (demonstrates awareness of sort optimization).",
                            code_snippet=self.get_line(node.lineno),
                        )
                    )

            # Detect binary search (indicates algorithm knowledge)
            if func_name in ["bisect", "bisect_left", "bisect_right"]:
                self.insights.append(
                    ComplexityInsight(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        complexity_type="binary_search",
                        severity="good_practice",
                        description="Binary search used (O(log n) - demonstrates algorithm knowledge).",
                        code_snippet=self.get_line(node.lineno),
                    )
                )

            # Detect set() or dict() calls (even nested in other calls)
            if func_name == "set":
                self.insights.append(
                    ComplexityInsight(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        complexity_type="set_operations",
                        severity="good_practice",
                        description="Set created for efficient O(1) operations.",
                        code_snippet=self.get_line(node.lineno),
                    )
                )
            elif func_name == "dict":
                self.insights.append(
                    ComplexityInsight(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        complexity_type="dict_lookup",
                        severity="good_practice",
                        description="Dictionary created for efficient O(1) lookups.",
                        code_snippet=self.get_line(node.lineno),
                    )
                )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Analyze function definitions."""
        # Look for memoization decorators
        for decorator in node.decorator_list:
            decorator_name = None
            if isinstance(decorator, ast.Name):
                decorator_name = decorator.id
            elif isinstance(decorator, ast.Attribute):
                decorator_name = decorator.attr
            elif isinstance(decorator, ast.Call):
                # Handle @lru_cache() or @lru_cache(maxsize=...)
                if isinstance(decorator.func, ast.Name):
                    decorator_name = decorator.func.id
                elif isinstance(decorator.func, ast.Attribute):
                    decorator_name = decorator.func.attr

            if decorator_name in ["lru_cache", "cache", "memoize"]:
                self.insights.append(
                    ComplexityInsight(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        complexity_type="memoization",
                        severity="good_practice",
                        description=f"Memoization decorator (@{decorator_name}) used - reduces time complexity through caching.",
                        code_snippet=self.get_line(node.lineno),
                    )
                )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect data structure usage patterns."""
        # Check for set or dict creation (efficient data structures)
        if isinstance(node.value, ast.Set):
            self.insights.append(
                ComplexityInsight(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    complexity_type="efficient_data_structure",
                    severity="good_practice",
                    description="Set used for O(1) membership tests (efficient choice).",
                    code_snippet=self.get_line(node.lineno),
                )
            )
        elif isinstance(node.value, ast.Dict):
            self.insights.append(
                ComplexityInsight(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    complexity_type="efficient_data_structure",
                    severity="good_practice",
                    description="Dictionary used for O(1) lookups (efficient choice).",
                    code_snippet=self.get_line(node.lineno),
                )
            )
        elif isinstance(node.value, ast.Call):
            # Check for set() or dict() constructor calls
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id == "set":
                    self.insights.append(
                        ComplexityInsight(
                            file_path=self.file_path,
                            line_number=node.lineno,
                            complexity_type="set_operations",
                            severity="good_practice",
                            description="Set created for efficient operations.",
                            code_snippet=self.get_line(node.lineno),
                        )
                    )
                elif node.value.func.id == "dict":
                    self.insights.append(
                        ComplexityInsight(
                            file_path=self.file_path,
                            line_number=node.lineno,
                            complexity_type="dict_lookup",
                            severity="good_practice",
                            description="Dictionary created for efficient lookups.",
                            code_snippet=self.get_line(node.lineno),
                        )
                    )

        self.generic_visit(node)


def analyze_python_file(file_path: str, source_code: str) -> List[ComplexityInsight]:
    """
    Analyze a single Python file for complexity patterns.

    Args:
        file_path: Path to the Python file
        source_code: Source code content

    Returns:
        List of complexity insights found
    """
    try:
        tree = ast.parse(source_code)
        analyzer = ComplexityAnalyzer(file_path, source_code)
        analyzer.visit(tree)
        return analyzer.insights
    except SyntaxError:
        # Skip files with syntax errors
        return []
    except Exception:
        # Skip files that can't be analyzed
        return []


def analyze_python_project(python_files: List[Tuple[str, str]]) -> ComplexityReport:
    """
    Analyze multiple Python files in a project.

    Args:
        python_files: List of (file_path, source_code) tuples

    Returns:
        ComplexityReport with aggregated insights
    """
    report = ComplexityReport(total_files_analyzed=len(python_files))

    for file_path, source_code in python_files:
        insights = analyze_python_file(file_path, source_code)
        for insight in insights:
            report.add_insight(insight)

    report.calculate_score()
    return report


def format_report(report: ComplexityReport, verbose: bool = False) -> str:
    """
    Format a complexity report for display.

    Args:
        report: ComplexityReport to format
        verbose: If True, include all details; if False, show summary only

    Returns:
        Formatted string
    """
    if report.total_files_analyzed == 0:
        return "No Python files analyzed."

    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("TIME COMPLEXITY ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append(f"\nFiles Analyzed: {report.total_files_analyzed}")
    lines.append(f"Optimization Awareness Score: {report.optimization_score:.1f}/100")

    # Interpret score
    if report.optimization_score >= 75:
        lines.append("Assessment: Strong awareness of algorithmic optimization ✓")
    elif report.optimization_score >= 50:
        lines.append("Assessment: Moderate awareness, some optimization opportunities exist")
    else:
        lines.append("Assessment: Limited optimization awareness, review suggestions below")

    lines.append("\n" + "-" * 70)
    lines.append("SUMMARY")
    lines.append("-" * 70)

    # Group by category
    good_practices = []
    suggestions = []

    for key, count in sorted(report.summary.items()):
        display_name = key.replace("_", " ").title()
        if any(
            x in key
            for x in [
                "efficient",
                "comprehension",
                "generator",
                "sorting_with_key",
                "binary_search",
                "memoization",
                "set_operations",
                "dict_lookup",
            ]
        ):
            good_practices.append(f"  ✓ {display_name}: {count}")
        else:
            suggestions.append(f"  • {display_name}: {count}")

    if good_practices:
        lines.append("\nGood Practices Found:")
        lines.extend(good_practices)

    if suggestions:
        lines.append("\nOptimization Opportunities:")
        lines.extend(suggestions)

    if verbose and report.insights:
        lines.append("\n" + "-" * 70)
        lines.append("DETAILED FINDINGS")
        lines.append("-" * 70)

        # Group insights by file
        by_file: Dict[str, List[ComplexityInsight]] = {}
        for insight in report.insights:
            by_file.setdefault(insight.file_path, []).append(insight)

        for file_path in sorted(by_file.keys()):
            lines.append(f"\n📄 {file_path}")
            for insight in by_file[file_path]:
                icon = "✓" if insight.severity == "good_practice" else "💡"
                lines.append(f"  {icon} Line {insight.line_number}: {insight.description}")
                if insight.code_snippet:
                    lines.append(f"     Code: {insight.code_snippet}")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)
