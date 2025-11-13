"""
Phase 3: Deep Code Analysis Module (OOP Principles Detection)

This module performs deep analysis of Python code to detect object-oriented programming
principles and design patterns. It builds on top of MetadataExtractor (Phase 2) and 
FileClassifier (Phase 1).

Key features:
- Detects OOP principles: abstraction, encapsulation, polymorphism, inheritance
- Analyzes code structure using Python AST
- Measures inheritance depth and class complexity
- Identifies design patterns and coding practices
- Integrates with existing analysis pipeline

Analysis Phases:
1. FileClassifier - Categorizes files by type
2. MetadataExtractor - Extracts project metadata
3. DeepCodeAnalyzer - Analyzes OOP principles (THIS MODULE)
"""

import ast
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    from .metadata_extractor import MetadataExtractor
    from .project_analyzer import FileClassifier
except ImportError:
    # For standalone execution
    MetadataExtractor = None
    FileClassifier = None


@dataclass
class OOPAnalysis:
    # Abstraction
    abstract_classes: List[str] = field(default_factory=list)
    total_classes: int = 0

    # Encapsulation
    private_methods: int = 0
    protected_methods: int = 0
    public_methods: int = 0
    properties_count: int = 0

    # Polymorphism
    method_overrides: int = 0
    operator_overloads: int = 0

    # Inheritance
    inheritance_depth: int = 0
    classes_with_inheritance: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class PythonOOPAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.analysis = OOPAnalysis()
        self.classes: Dict[str, ast.ClassDef] = {}
        self.current_class: Optional[str] = None

    def _analyze_method(self, node: ast.FunctionDef):
        method_name = node.name
        if method_name.startswith("__") and not method_name.endswith("__"):
            self.analysis.private_methods += 1
        elif method_name.startswith("_"):
            self.analysis.protected_methods += 1
        else:
            self.analysis.public_methods += 1

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "property":
                self.analysis.properties_count += 1

        if method_name.startswith("__") and method_name.endswith("__"):
            if method_name not in ("__init__", "__new__", "__del__"):
                self.analysis.operator_overloads += 1

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes[node.name] = node
        self.analysis.total_classes += 1

        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ("ABC", "Protocol"):
                self.analysis.abstract_classes.append(node.name)
                break
        if len(node.bases) > 0:
            self.analysis.classes_with_inheritance += 1

        # Analyze methods
        old_class = self.current_class
        self.current_class = node.name

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._analyze_method(item)

        self.current_class = old_class
        self.generic_visit(node)

    def calculate_inheritance_depth(self):
        def get_depth(class_name: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()

            if class_name in visited or class_name not in self.classes:
                return 0

            visited.add(class_name)
            node = self.classes[class_name]

            if not node.bases:
                return 0

            max_depth = 0
            for base in node.bases:
                if isinstance(base, ast.Name):
                    depth = get_depth(base.id, visited.copy())
                    max_depth = max(max_depth, depth)

            return max_depth + 1

        max_depth = 0
        for class_name in self.classes:
            depth = get_depth(class_name)
            max_depth = max(max_depth, depth)

        self.analysis.inheritance_depth = max_depth


def analyze_python_file(content: str) -> OOPAnalysis:
    """
    Analyze a single Python file for OOP principles.

    Args:
        content: Python source code as string

    Returns:
        OOPAnalysis object with detected OOP metrics
    """
    try:
        tree = ast.parse(content)
        analyzer = PythonOOPAnalyzer()
        analyzer.visit(tree)
        analyzer.calculate_inheritance_depth()
        return analyzer.analysis
    except SyntaxError:
        # Return empty analysis for invalid Python
        return OOPAnalysis()


def analyze_project_deep(zip_path: Path, project_path: str = "") -> Dict:
    """
    Perform deep OOP analysis on a Python project in a ZIP file.
    This builds upon the metadata extractor's analysis.

    Args:
        zip_path: Path to ZIP file
        project_path: Path within ZIP to analyze (empty string for root)

    Returns:
        Dictionary with combined metadata and OOP analysis

    Raises:
        ImportError: If MetadataExtractor or FileClassifier not available
    """
    if MetadataExtractor is None or FileClassifier is None:
        raise ImportError("MetadataExtractor and FileClassifier are required for project analysis")

    # First, get basic metadata using existing MetadataExtractor
    with MetadataExtractor(zip_path) as extractor:
        metadata = extractor.extract_project_metadata(project_path)

    # Now perform deep OOP analysis on Python files
    combined_oop = OOPAnalysis()

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Get list of Python files from metadata
        python_files = []

        # Build file list from classification
        classifier = FileClassifier(zip_path)
        classification = classifier.classify_project(project_path)

        if "python" in classification["files"]["code"]:
            python_files = classification["files"]["code"]["python"]

        # Analyze each Python file
        for file_info in python_files:
            try:
                content = zf.read(file_info["path"]).decode("utf-8", errors="ignore")
                file_analysis = analyze_python_file(content)

                # Aggregate results
                combined_oop.total_classes += file_analysis.total_classes
                combined_oop.abstract_classes.extend(file_analysis.abstract_classes)
                combined_oop.private_methods += file_analysis.private_methods
                combined_oop.protected_methods += file_analysis.protected_methods
                combined_oop.public_methods += file_analysis.public_methods
                combined_oop.properties_count += file_analysis.properties_count
                combined_oop.operator_overloads += file_analysis.operator_overloads
                combined_oop.classes_with_inheritance += file_analysis.classes_with_inheritance
                combined_oop.inheritance_depth = max(combined_oop.inheritance_depth, file_analysis.inheritance_depth)

            except Exception:
                # Skip files that can't be read
                continue

        classifier.close()

    # Combine results
    result = {
        "project_name": metadata.project_name,
        "project_path": metadata.project_path,
        "metadata": metadata.to_dict(),
        "oop_analysis": combined_oop.to_dict(),
    }

    return result


def generate_comprehensive_report(zip_path: Path, output_path: Optional[Path] = None) -> Dict:
    """
    Generate a comprehensive analysis report combining all analysis phases.

    This function orchestrates:
    - Phase 1: File classification (FileClassifier)
    - Phase 2: Metadata extraction (MetadataExtractor)
    - Phase 3: Deep code analysis (DeepCodeAnalyzer)

    Args:
        zip_path: Path to ZIP file
        output_path: Optional path to save JSON report

    Returns:
        Complete analysis report as dictionary

    Raises:
        ImportError: If MetadataExtractor is not available
    """
    if MetadataExtractor is None:
        raise ImportError("MetadataExtractor is required for comprehensive report")

    with MetadataExtractor(zip_path) as extractor:
        # Generate base report (Phases 1 & 2)
        report = extractor.generate_report()
        # Add Phase 3: Deep OOP analysis for each Python project
        for i, project in enumerate(report["projects"]):
            project_path = project.get("project_path", "")
            # Only analyze if project has Python files
            if "python" in project.get("languages", {}):
                try:
                    deep_analysis = analyze_project_deep(zip_path, project_path)
                    report["projects"][i]["oop_analysis"] = deep_analysis["oop_analysis"]
                except Exception as e:
                    # If deep analysis fails, add error info
                    report["projects"][i]["oop_analysis"] = {"error": str(e), "total_classes": 0}
            if "java" in project.get("languages", {}):
                try:
                    from .java_oop_analyzer import analyze_java_project
                    java_analysis = analyze_java_project(zip_path, project_path)
                    report["projects"][i]["java_oop_analysis"] = java_analysis["java_oop_analysis"]
                except ImportError:
                    report["projects"][i]["java_oop_analysis"] = {
                        "error": "Java analyzer not available (javalang not installed)",
                        "total_classes": 0
                    }
                except Exception as e:
                    # If deep analysis fails, add error info
                    report["projects"][i]["java_oop_analysis"] = {"error": str(e), "total_classes": 0}
    # Save to file if requested
    if output_path:
        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    return report


if __name__ == "__main__":
    import sys

    # Check if a file path was provided
    if len(sys.argv) > 1:
        # Analyze a file provided by the user
        file_path = Path(sys.argv[1])

        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        print("\n" + "=" * 70)
        print(f"ANALYZING: {file_path.name}")
        print("=" * 70)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            result = analyze_python_file(content)

            print(f"\nOOP ANALYSIS RESULTS:")
            print(f"\n  Classes:")
            print(f"    Total classes: {result.total_classes}")
            if result.abstract_classes:
                print(f"    Abstract classes: {', '.join(result.abstract_classes)}")
            print(f"    With inheritance: {result.classes_with_inheritance}")
            print(f"    Max inheritance depth: {result.inheritance_depth}")

            print(f"\n  Encapsulation:")
            print(f"    Private methods (__name): {result.private_methods}")
            print(f"    Protected methods (_name): {result.protected_methods}")
            print(f"    Public methods: {result.public_methods}")
            print(f"    Properties (@property): {result.properties_count}")

            print(f"\n  Polymorphism:")
            print(f"    Operator overloads: {result.operator_overloads}")

            # Quick assessment
            print(f"\nQUICK ASSESSMENT:")
            if result.total_classes == 0:
                print(f"    - No classes found (procedural/functional style)")
            else:
                print(f"    - Uses OOP (found {result.total_classes} classes)")
                if result.abstract_classes:
                    print(f"    - Uses abstraction")
                if result.private_methods > 0 or result.protected_methods > 0:
                    print(f"    - Practices encapsulation")
                if result.inheritance_depth > 0:
                    print(f"    - Uses inheritance")
                if result.operator_overloads > 0:
                    print(f"    - Implements polymorphism")

            print("\n" + "=" * 70 + "\n")

        except Exception as e:
            print(f"Error analyzing file: {e}")
            sys.exit(1)

    else:
        # Run built-in test
        print("=" * 70)
        print("PYTHON OOP ANALYZER - Built-in Test")
        print("=" * 70)
        print("\nUsage: python src/backend/analysis/deep_code_analyzer.py <path_to_file.py>")
        print("\nExample:")
        print("  python src/backend/analysis/deep_code_analyzer.py src/backend/cli.py")
        print("  python src/backend/analysis/deep_code_analyzer.py ~/mycode.py")

        test_code = """
from abc import ABC, abstractmethod

class Animal(ABC):
    def __init__(self, name):
        self._name = name  # Protected
        self.__age = 0     # Private
    
    @property
    def name(self):
        return self._name
    
    @abstractmethod
    def speak(self):
        pass
    
    def __str__(self):  # Operator overload
        return f"{self._name}"

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"
"""

        print("\nRunning test with sample code...\n")
        result = analyze_python_file(test_code)
        print(f"  Total classes: {result.total_classes}")
        print(f"  Abstract classes: {result.abstract_classes}")
        print(f"  Classes with inheritance: {result.classes_with_inheritance}")
        print(f"  Inheritance depth: {result.inheritance_depth}")
        print(f"  Private methods: {result.private_methods}")
        print(f"  Protected methods: {result.protected_methods}")
        print(f"  Public methods: {result.public_methods}")
        print(f"  Properties: {result.properties_count}")
        print(f"  Operator overloads: {result.operator_overloads}")
        print("\n" + "=" * 70)
