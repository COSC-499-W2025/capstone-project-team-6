"""
Phase 3: C++ OOP Analysis Module 

This module performs deep analysis of C++ code using libclang's AST parser
to detect object-oriented programming principles, design patterns, and 
structural OOP features.

Requirements:
    pip install libclang

Analysis Phases:
1. FileClassifier - Categorizes files by type
2. MetadataExtractor - Extracts project metadata
3. CppOOPAnalyzer - Analyzes C++ OOP principles (THIS MODULE)
"""

import re
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import clang.cindex
    from clang.cindex import AccessSpecifier, CursorKind

    CLANG_AVAILABLE = True
except ImportError:
    CLANG_AVAILABLE = False
    print("Warning: libclang not installed. Install with: pip install libclang")

try:
    from .metadata_extractor import MetadataExtractor
    from .project_analyzer import FileClassifier
except ImportError:
    MetadataExtractor = None
    FileClassifier = None


@dataclass
class CppOOPAnalysis:
    """Stores C++ OOP analysis results."""

    # Basic structure
    total_classes: int = 0
    struct_count: int = 0
    abstract_classes: List[str] = field(default_factory=list)
    classes_with_inheritance: int = 0
    inheritance_depth: int = 0

    # Encapsulation metrics
    private_methods: int = 0
    protected_methods: int = 0
    public_methods: int = 0
    private_fields: int = 0
    protected_fields: int = 0
    public_fields: int = 0

    # Polymorphism
    virtual_methods: int = 0
    override_methods: int = 0
    operator_overloads: int = 0

    # C++ features
    template_classes: int = 0
    namespaces_used: int = 0

    # Design patterns detected
    design_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CppClassInfo:
    """Information about a single C++ class or struct."""

    name: str
    is_struct: bool = False
    is_abstract: bool = False
    inherits: List[str] = field(default_factory=list)

    methods: List[Dict] = field(default_factory=list)
    fields: List[Dict] = field(default_factory=list)

    is_template: bool = False
    namespace: Optional[str] = None
    has_virtual_methods: bool = False


class CppOOPAnalyzer:
    """Analyzes C++ source code for OOP principles using libclang."""

    def __init__(self):
        self.analysis = CppOOPAnalysis()
        self.classes: Dict[str, CppClassInfo] = {}
        self.inheritance_tree: Dict[str, List[str]] = defaultdict(list)
        self.namespaces: Set[str] = set()

    def analyze_file(self, content: str, filename: str = "temp.cpp") -> CppOOPAnalysis:
        """Main entry point: analyze a single C++ file using libclang."""

        if not CLANG_AVAILABLE:
            return self.analysis

        try:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".cpp", delete=False) as f:
                f.write(content)
                temp_path = f.name

            index = clang.cindex.Index.create()
            translation_unit = index.parse(temp_path, args=["-std=c++17", "-x", "c++"])

            self._traverse_ast(translation_unit.cursor)

            self._compute_inheritance_depth()
            self._detect_design_patterns()

            import os

            os.unlink(temp_path)

        except Exception as e:
            print(f"Warning: Failed to parse C++ file: {e}")

        return self.analysis

    def _traverse_ast(self, cursor, parent_class=None):
        """Recursively traverse the AST."""

        if cursor.kind == CursorKind.CLASS_DECL:
            self._analyze_class(cursor, is_struct=False)

        elif cursor.kind == CursorKind.STRUCT_DECL:
            self._analyze_class(cursor, is_struct=True)

        elif cursor.kind == CursorKind.NAMESPACE:
            namespace_name = cursor.spelling
            if namespace_name:  # Skip anonymous namespaces
                self.namespaces.add(namespace_name)
                self.analysis.namespaces_used = len(self.namespaces)

        # Method declarations (when inside a class)
        elif cursor.kind in (CursorKind.CXX_METHOD, CursorKind.FUNCTION_DECL) and parent_class:
            self._analyze_method(cursor, parent_class)

        # Field declarations (when inside a class)
        elif cursor.kind == CursorKind.FIELD_DECL and parent_class:
            self._analyze_field(cursor, parent_class)

        for child in cursor.get_children():
            new_parent = parent_class
            if cursor.kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL):
                new_parent = cursor.spelling
            self._traverse_ast(child, new_parent)

    def _analyze_class(self, cursor, is_struct=False):
        """Analyze a class or struct declaration."""

        class_name = cursor.spelling
        if not class_name:  # Skip anonymous classes
            return

        # Skip forward declarations
        if not cursor.is_definition():
            return

        class_info = CppClassInfo(name=class_name, is_struct=is_struct)

        if is_struct:
            self.analysis.struct_count += 1
        else:
            self.analysis.total_classes += 1

        if cursor.get_num_template_arguments() >= 0:
            class_info.is_template = True
            self.analysis.template_classes += 1

        for base in self._get_base_classes(cursor):
            class_info.inherits.append(base)
            self.inheritance_tree[base].append(class_name)

        if class_info.inherits:
            self.analysis.classes_with_inheritance += 1

        has_pure_virtual = False
        for child in cursor.get_children():
            if child.kind == CursorKind.CXX_METHOD:
                self._analyze_method(child, class_name)

                if child.is_pure_virtual_method():
                    has_pure_virtual = True
                    class_info.has_virtual_methods = True
                elif child.is_virtual_method():
                    class_info.has_virtual_methods = True

            elif child.kind == CursorKind.FIELD_DECL:
                self._analyze_field(child, class_name)

        if has_pure_virtual:
            class_info.is_abstract = True
            if class_name not in self.analysis.abstract_classes:
                self.analysis.abstract_classes.append(class_name)

        self.classes[class_name] = class_info

    def _get_base_classes(self, cursor) -> List[str]:
        """Extract base class names from a class cursor."""
        bases = []
        for child in cursor.get_children():
            if child.kind == CursorKind.CXX_BASE_SPECIFIER:
                base_type = child.type.spelling
                # Clean up
                base_name = re.sub(r"<.*>", "", base_type)
                base_name = base_name.split("::")[-1]
                base_name = base_name.strip()
                if base_name:
                    bases.append(base_name)
        return bases

    def _analyze_method(self, cursor, class_name):
        """Analyze a method declaration."""

        method_name = cursor.spelling
        if not method_name:
            return

        access = cursor.access_specifier

        if method_name.startswith("operator"):
            self.analysis.operator_overloads += 1

        is_virtual = cursor.is_virtual_method()
        is_pure_virtual = cursor.is_pure_virtual_method()

        if is_virtual or is_pure_virtual:
            self.analysis.virtual_methods += 1

        # Override detection (heuristic)
        if is_virtual and not is_pure_virtual:
            for base in self.classes.get(class_name, CppClassInfo(class_name)).inherits:
                if base in self.classes:
                    for m in self.classes[base].methods:
                        if m["name"] == method_name:
                            self.analysis.override_methods += 1
                            break

        if access == AccessSpecifier.PRIVATE:
            self.analysis.private_methods += 1
        elif access == AccessSpecifier.PROTECTED:
            self.analysis.protected_methods += 1
        elif access == AccessSpecifier.PUBLIC:
            self.analysis.public_methods += 1

        # Store method info
        method_info = {
            "name": method_name,
            "access": self._access_to_string(access),
            "is_virtual": is_virtual,
            "is_pure_virtual": is_pure_virtual,
        }

        if class_name in self.classes:
            self.classes[class_name].methods.append(method_info)

    def _analyze_field(self, cursor, class_name):
        """Analyze a field declaration."""

        field_name = cursor.spelling
        if not field_name:
            return

        access = cursor.access_specifier

        if access == AccessSpecifier.PRIVATE:
            self.analysis.private_fields += 1
        elif access == AccessSpecifier.PROTECTED:
            self.analysis.protected_fields += 1
        elif access == AccessSpecifier.PUBLIC:
            self.analysis.public_fields += 1

        field_info = {"name": field_name, "access": self._access_to_string(access), "type": cursor.type.spelling}

        if class_name in self.classes:
            self.classes[class_name].fields.append(field_info)

    def _access_to_string(self, access):
        """Convert AccessSpecifier to string."""
        if access == AccessSpecifier.PRIVATE:
            return "private"
        elif access == AccessSpecifier.PROTECTED:
            return "protected"
        elif access == AccessSpecifier.PUBLIC:
            return "public"
        return "public"  # default for structs

    def _compute_inheritance_depth(self):
        """Compute the maximum inheritance chain depth."""

        def depth(class_name: str, visited: Set[str]) -> int:
            if class_name not in self.inheritance_tree:
                return 0

            max_d = 0
            for child in self.inheritance_tree[class_name]:
                if child in visited:
                    continue
                visited.add(child)
                max_d = max(max_d, 1 + depth(child, visited))

            return max_d

        max_depth = 0
        for base in self.inheritance_tree:
            max_depth = max(max_depth, depth(base, set()))

        self.analysis.inheritance_depth = max_depth

    def _detect_design_patterns(self):
        """Detect common design patterns in the code."""

        patterns = set()

        for class_name, class_info in self.classes.items():
            # Factory pattern
            if "Factory" in class_name:
                patterns.add("Factory")

            # Singleton pattern (heuristic)
            if "Singleton" in class_name or any(m["name"] in ("getInstance", "instance") for m in class_info.methods):
                patterns.add("Singleton")

            # Strategy pattern
            if class_info.is_abstract:
                children = self.inheritance_tree.get(class_name, [])
                if len(children) >= 2:
                    patterns.add("Strategy")

            if "Observer" in class_name or "Observable" in class_name:
                patterns.add("Observer")

        self.analysis.design_patterns = sorted(list(patterns))


# SCORING FUNCTIONS
def calculate_oop_score(analysis: CppOOPAnalysis) -> int:
    """Calculate OOP score (0-6) based on C++ OOP principles usage."""
    score = 0

    if analysis.total_classes > 0 or analysis.struct_count > 0:
        score += 1

    if len(analysis.abstract_classes) > 0:
        score += 1

    if analysis.inheritance_depth > 0 or analysis.classes_with_inheritance > 0:
        score += 1

    if (
        analysis.private_fields > 0
        or analysis.private_methods > 0
        or analysis.protected_fields > 0
        or analysis.protected_methods > 0
    ):
        score += 1

    if analysis.virtual_methods > 0 or analysis.override_methods > 0 or analysis.operator_overloads > 0:
        score += 1

    if analysis.template_classes > 0 or analysis.namespaces_used > 0 or len(analysis.design_patterns) > 0:
        score += 1

    return score


def calculate_solid_score(analysis: CppOOPAnalysis) -> float:
    """Rough SOLID principles score (0-5) based on code structure."""
    score = 0.0

    total_types = analysis.total_classes + analysis.struct_count
    total_methods = analysis.public_methods + analysis.private_methods + analysis.protected_methods

    # Single Responsibility: reasonable methods per type
    if total_types > 0:
        avg_methods = total_methods / max(total_types, 1)
        if 3 <= avg_methods <= 15:
            score += 1.0
        elif avg_methods > 0:
            score += 0.5

    # Open/Closed: inheritance + virtual methods
    if analysis.classes_with_inheritance > 0 and analysis.virtual_methods > 0:
        score += 1.0
    elif analysis.classes_with_inheritance > 0:
        score += 0.5

    # Liskov Substitution: multiple abstract classes
    if len(analysis.abstract_classes) >= 3:
        score += 1.0
    elif len(analysis.abstract_classes) > 0:
        score += 0.5

    # Interface Segregation: design patterns
    if "Strategy" in analysis.design_patterns or "Factory" in analysis.design_patterns:
        score += 1.0
    elif len(analysis.design_patterns) > 0:
        score += 0.5

    # Dependency Inversion: templates (generic programming)
    if analysis.template_classes > 0:
        score += 1.0

    return min(score, 5.0)


def get_coding_style(oop_score: int) -> str:
    """Determine coding style based on OOP score."""
    if oop_score == 0:
        return "Procedural/Functional"
    elif oop_score <= 2:
        return "Basic OOP"
    elif oop_score <= 4:
        return "Moderate OOP"
    else:
        return "Advanced OOP"


def analyze_cpp_file(content: str) -> CppOOPAnalysis:
    """Analyze a single C++ file and return the OOP analysis results."""
    analyzer = CppOOPAnalyzer()
    return analyzer.analyze_file(content)


def analyze_cpp_project(zip_path: Path, project_path: str = "") -> Dict:
    """Perform deep OOP analysis on a C++ project inside a ZIP file."""
    if MetadataExtractor is None or FileClassifier is None:
        raise ImportError("MetadataExtractor and FileClassifier are required")

    with MetadataExtractor(zip_path) as extractor:
        metadata = extractor.extract_project_metadata(project_path)

    combined = CppOOPAnalysis()

    with zipfile.ZipFile(zip_path, "r") as zf:
        classifier = FileClassifier(zip_path)
        classification = classifier.classify_project(project_path)

        cpp_files = []
        if "cpp" in classification["files"]["code"]:
            cpp_files = classification["files"]["code"]["cpp"]

        for file_info in cpp_files:
            try:
                content = zf.read(file_info["path"]).decode("utf-8", errors="ignore")
                file_analysis = analyze_cpp_file(content)

                combined.total_classes += file_analysis.total_classes
                combined.struct_count += file_analysis.struct_count
                combined.classes_with_inheritance += file_analysis.classes_with_inheritance
                combined.inheritance_depth = max(combined.inheritance_depth, file_analysis.inheritance_depth)

                combined.private_methods += file_analysis.private_methods
                combined.protected_methods += file_analysis.protected_methods
                combined.public_methods += file_analysis.public_methods

                combined.private_fields += file_analysis.private_fields
                combined.protected_fields += file_analysis.protected_fields
                combined.public_fields += file_analysis.public_fields

                combined.virtual_methods += file_analysis.virtual_methods
                combined.override_methods += file_analysis.override_methods
                combined.operator_overloads += file_analysis.operator_overloads

                combined.template_classes += file_analysis.template_classes
                combined.namespaces_used += file_analysis.namespaces_used

                combined.abstract_classes.extend(file_analysis.abstract_classes)

                for p in file_analysis.design_patterns:
                    if p not in combined.design_patterns:
                        combined.design_patterns.append(p)

            except Exception as e:
                print(f"Warning: Failed to analyze {file_info['path']}: {e}")
                continue

        classifier.close()

    return {
        "project_name": metadata.project_name,
        "project_path": metadata.project_path,
        "metadata": metadata.to_dict(),
        "cpp_oop_analysis": combined.to_dict(),
    }


# COMMAND LINE INTERFACE
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])

        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        if not CLANG_AVAILABLE:
            print("Error: libclang not installed.")
            print("Install with: pip install libclang")
            sys.exit(1)

        print("\n" + "=" * 70)
        print(f"ANALYZING C++ FILE: {file_path.name}")
        print("=" * 70)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            result = analyze_cpp_file(content)
            oop_score = calculate_oop_score(result)
            solid_score = calculate_solid_score(result)
            coding_style = get_coding_style(oop_score)

            print("\nC++ OOP ANALYSIS RESULTS:\n")

            print(f"  Total classes: {result.total_classes}")
            print(f"  Structs: {result.struct_count}")
            if result.abstract_classes:
                print(f"  Abstract classes: {', '.join(result.abstract_classes)}")
            print(f"  Classes with inheritance: {result.classes_with_inheritance}")
            print(f"  Inheritance depth: {result.inheritance_depth}")

            print("\n  Encapsulation:")
            print(f"    Private methods: {result.private_methods}")
            print(f"    Protected methods: {result.protected_methods}")
            print(f"    Public methods: {result.public_methods}")
            print(f"    Private fields: {result.private_fields}")
            print(f"    Protected fields: {result.protected_fields}")
            print(f"    Public fields: {result.public_fields}")

            print("\n  Polymorphism:")
            print(f"    Virtual methods: {result.virtual_methods}")
            print(f"    Override methods: {result.override_methods}")
            print(f"    Operator overloads: {result.operator_overloads}")

            print("\n  C++ Features:")
            print(f"    Template classes: {result.template_classes}")
            print(f"    Namespaces used: {result.namespaces_used}")

            if result.design_patterns:
                print("\n  Design Patterns:")
                for p in result.design_patterns:
                    print(f"    ✓ {p}")

            print("\nSCORES:")
            print(f"  OOP Score: {oop_score}/6")
            print(f"  SOLID Score: {solid_score:.1f}/5.0")
            print(f"  Coding Style: {coding_style}")

            print("\n" + "=" * 70 + "\n")

        except Exception as e:
            print(f"Error analyzing file: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    else:
        print("=" * 70)
        print("C++ OOP ANALYZER - Usage")
        print("=" * 70)
        print("\nUsage:")
        print("  python cpp_oop_analyzer_clang.py <file.cpp>")
        print("\nExample:")
        print("  python cpp_oop_analyzer_clang.py sample.cpp")
        print("\nRequirements:")
        print("  pip install libclang")
        print("\n" + "=" * 70)
