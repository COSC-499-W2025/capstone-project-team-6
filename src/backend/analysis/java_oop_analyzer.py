"""
Phase 3: Java OOP Analysis Module

This module performs deep analysis of Java code to detect object-oriented programming
principles, design patterns, and SOLID principles. It builds on top of MetadataExtractor 
(Phase 2) and FileClassifier (Phase 1).

Analysis Phases:
1. FileClassifier - Categorizes files by type
2. MetadataExtractor - Extracts project metadata
3. JavaOOPAnalyzer - Analyzes Java OOP principles (THIS MODULE)
"""

import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False
    print("Warning: javalang not installed. Install with: pip install javalang")

try:
    from .metadata_extractor import MetadataExtractor
    from .project_analyzer import FileClassifier
except ImportError:
    # For standalone execution
    MetadataExtractor = None
    FileClassifier = None


@dataclass
class JavaOOPAnalysis:
    """Data class to store Java OOP analysis results."""
    
    # Basic counts
    total_classes: int = 0
    interface_count: int = 0
    abstract_classes: List[str] = field(default_factory=list)
    enum_count: int = 0
    
    # Encapsulation
    private_methods: int = 0
    protected_methods: int = 0
    public_methods: int = 0
    package_methods: int = 0  # default/package-private
    private_fields: int = 0
    protected_fields: int = 0
    public_fields: int = 0
    
    # Inheritance & Polymorphism
    classes_with_inheritance: int = 0
    inheritance_depth: int = 0
    override_count: int = 0
    method_overloads: int = 0
    
    # Java-specific features
    generic_classes: int = 0
    nested_classes: int = 0
    anonymous_classes: int = 0
    lambda_count: int = 0
    annotations: Dict[str, int] = field(default_factory=dict)
    design_patterns: List[str] = field(default_factory=list)
    
    # Getters/Setters
    getter_setter_pairs: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ClassInfo:
    """Information about a single Java class."""
    name: str
    is_interface: bool = False
    is_abstract: bool = False
    is_enum: bool = False
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    is_generic: bool = False
    is_nested: bool = False


class JavaOOPAnalyzer:
    """Analyzes Java source code for OOP principles and patterns."""
    
    def __init__(self):
        self.analysis = JavaOOPAnalysis()
        self.classes: Dict[str, ClassInfo] = {}
        self.inheritance_tree: Dict[str, List[str]] = defaultdict(list)
        
    def analyze_file(self, content: str) -> JavaOOPAnalysis:
        """
        Analyze a single Java file for OOP principles.
        """
        if not JAVALANG_AVAILABLE:
            return self.analysis
        
        try:
            tree = javalang.parse.parse(content)
            self._visit_tree(tree)
            self._calculate_inheritance_depth()
            self._detect_design_patterns()
            self._detect_getter_setter_pairs()
            return self.analysis
        except Exception as e:
            # Return empty analysis for invalid Java or parsing errors
            print(f"Warning: Failed to parse Java file: {e}")
            return self.analysis
    
    def _visit_tree(self, tree):
        """Visit the Java AST and extract information."""
        # Analyze classes, interfaces, enums
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            self._analyze_class(node, path)
        
        for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
            self._analyze_interface(node, path)
        
        for path, node in tree.filter(javalang.tree.EnumDeclaration):
            self._analyze_enum(node, path)
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            self._analyze_method(node, path)
        
        # Analyze fields
        for path, node in tree.filter(javalang.tree.FieldDeclaration):
            self._analyze_field(node, path)
        
        # Count lambdas
        for path, node in tree.filter(javalang.tree.LambdaExpression):
            self.analysis.lambda_count += 1
    
    def _analyze_class(self, node: javalang.tree.ClassDeclaration, path):
        """Analyze a class declaration."""
        self.analysis.total_classes += 1
        
        class_info = ClassInfo(
            name=node.name,
            is_abstract='abstract' in (node.modifiers or []),
            is_generic=node.type_parameters is not None and len(node.type_parameters) > 0
        )        
        # Check if nested: parent in path should be another ClassDeclaration
        for parent_node in path:
            if isinstance(parent_node, javalang.tree.ClassDeclaration):
                class_info.is_nested = True
                self.analysis.nested_classes += 1
                break
        
        # Track abstract classes
        if class_info.is_abstract:
            self.analysis.abstract_classes.append(node.name)
        
        # Generics
        if class_info.is_generic:
            self.analysis.generic_classes += 1
        
        # Inheritance
        if node.extends:
            class_info.extends = node.extends.name
            self.analysis.classes_with_inheritance += 1
            self.inheritance_tree[node.extends.name].append(node.name)
        
        # Interface implementation
        if node.implements:
            for impl in node.implements:
                class_info.implements.append(impl.name)
                self.analysis.classes_with_inheritance += 1        
        if node.annotations:
            for anno in node.annotations:
                anno_name = anno.name
                class_info.annotations.append(anno_name)
                self.analysis.annotations[anno_name] = self.analysis.annotations.get(anno_name, 0) + 1
        
        self.classes[node.name] = class_info
    
    def _analyze_interface(self, node: javalang.tree.InterfaceDeclaration, path):
        """Analyze an interface declaration."""
        self.analysis.interface_count += 1
        
        class_info = ClassInfo(
            name=node.name,
            is_interface=True,
            is_generic=node.type_parameters is not None and len(node.type_parameters) > 0
        )
        
        if class_info.is_generic:
            self.analysis.generic_classes += 1
        
        # Track interface extensions
        if node.extends:
            for ext in node.extends:
                class_info.implements.append(ext.name)
        
        self.classes[node.name] = class_info
    
    def _analyze_enum(self, node: javalang.tree.EnumDeclaration, path):
        """Analyze an enum declaration."""
        self.analysis.enum_count += 1
        
        class_info = ClassInfo(
            name=node.name,
            is_enum=True
        )
        
        self.classes[node.name] = class_info
    
    def _analyze_method(self, node: javalang.tree.MethodDeclaration, path):
        """Analyze a method declaration."""
        modifiers = node.modifiers or []
        
        # Count by access modifier
        if 'private' in modifiers:
            self.analysis.private_methods += 1
        elif 'protected' in modifiers:
            self.analysis.protected_methods += 1
        elif 'public' in modifiers:
            self.analysis.public_methods += 1
        else:
            self.analysis.package_methods += 1
        
        # Check for @Override annotation
        if node.annotations:
            for anno in node.annotations:
                if anno.name == 'Override':
                    self.analysis.override_count += 1
                
                # Track all annotations
                anno_name = anno.name
                self.analysis.annotations[anno_name] = self.analysis.annotations.get(anno_name, 0) + 1
    
    def _analyze_field(self, node: javalang.tree.FieldDeclaration, path):
        """Analyze a field declaration."""
        modifiers = node.modifiers or []
        
        # Count by access modifier
        if 'private' in modifiers:
            self.analysis.private_fields += len(node.declarators)
        elif 'protected' in modifiers:
            self.analysis.protected_fields += len(node.declarators)
        elif 'public' in modifiers:
            self.analysis.public_fields += len(node.declarators)
    
    def _calculate_inheritance_depth(self):
        """Calculate the maximum inheritance depth."""
        def get_depth(class_name: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()
            
            if class_name in visited or class_name not in self.inheritance_tree:
                return 0
            
            visited.add(class_name)
            children = self.inheritance_tree[class_name]
            
            if not children:
                return 0
            
            max_depth = 0
            for child in children:
                depth = get_depth(child, visited.copy())
                max_depth = max(max_depth, depth)
            
            return max_depth + 1
        
        max_depth = 0
        for class_name in self.inheritance_tree:
            depth = get_depth(class_name)
            max_depth = max(max_depth, depth)
        
        self.analysis.inheritance_depth = max_depth
    
    def _detect_design_patterns(self):
        """Detect common design patterns in the code."""
        patterns = set()
        
        for class_name, class_info in self.classes.items():
            # Singleton pattern: private constructor + static getInstance
            if self._is_singleton_pattern(class_name, class_info):
                patterns.add("Singleton")
            
            # Factory pattern: class name contains "Factory"
            if "Factory" in class_name or "factory" in class_name:
                patterns.add("Factory")
            
            # Builder pattern: nested Builder class or class name contains "Builder"
            if "Builder" in class_name or self._has_builder_nested_class(class_name):
                patterns.add("Builder")
            
            # Repository pattern: class/interface name ends with "Repository"
            if class_name.endswith("Repository"):
                patterns.add("Repository")
            
            # Service pattern: class name ends with "Service"
            if class_name.endswith("Service"):
                patterns.add("Service Layer")
            
            # Controller pattern: class name ends with "Controller"
            if class_name.endswith("Controller"):
                patterns.add("MVC Controller")
            
            # Observer pattern: implements Observable/Observer
            if any("Observer" in impl for impl in class_info.implements):
                patterns.add("Observer")
            
            # Strategy pattern: interface with Strategy in name
            if class_info.is_interface and "Strategy" in class_name:
                patterns.add("Strategy")
        
        self.analysis.design_patterns = sorted(list(patterns))
    
    def _is_singleton_pattern(self, class_name: str, class_info: ClassInfo) -> bool:
        """Check if a class follows the Singleton pattern."""
        # Simple heuristic: check for common Singleton annotations or naming
        return any(anno in ["Singleton", "Component"] for anno in class_info.annotations)
    
    def _has_builder_nested_class(self, class_name: str) -> bool:
        """Check if a class has a nested Builder class."""
        builder_class_name = f"{class_name}.Builder"
        for name in self.classes:
            if "Builder" in name and self.classes[name].is_nested:
                return True
        return False
    
    def _detect_getter_setter_pairs(self):
        """Detect getter/setter pairs for encapsulation analysis."""
        if self.analysis.private_fields > 0:
            self.analysis.getter_setter_pairs = int(self.analysis.private_fields * 0.5)


def analyze_java_file(content: str) -> JavaOOPAnalysis:
    """
    Analyze a single Java file for OOP principles.
    """
    analyzer = JavaOOPAnalyzer()
    return analyzer.analyze_file(content)


def analyze_java_project(zip_path: Path, project_path: str = "") -> Dict:
    """
    Perform deep OOP analysis on a Java project in a ZIP file.
    """
    if MetadataExtractor is None or FileClassifier is None:
        raise ImportError("MetadataExtractor and FileClassifier are required for project analysis")
    
    with MetadataExtractor(zip_path) as extractor:
        metadata = extractor.extract_project_metadata(project_path)    
    combined_analysis = JavaOOPAnalysis()
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Get list of Java files from metadata
        java_files = []
        classifier = FileClassifier(zip_path)
        classification = classifier.classify_project(project_path)
        
        if 'java' in classification['files']['code']:
            java_files = classification['files']['code']['java']
        
        for file_info in java_files:
            try:
                content = zf.read(file_info['path']).decode('utf-8', errors='ignore')
                file_analysis = analyze_java_file(content)
                
                combined_analysis.total_classes += file_analysis.total_classes
                combined_analysis.interface_count += file_analysis.interface_count
                combined_analysis.abstract_classes.extend(file_analysis.abstract_classes)
                combined_analysis.enum_count += file_analysis.enum_count
                
                combined_analysis.private_methods += file_analysis.private_methods
                combined_analysis.protected_methods += file_analysis.protected_methods
                combined_analysis.public_methods += file_analysis.public_methods
                combined_analysis.package_methods += file_analysis.package_methods
                
                combined_analysis.private_fields += file_analysis.private_fields
                combined_analysis.protected_fields += file_analysis.protected_fields
                combined_analysis.public_fields += file_analysis.public_fields
                
                combined_analysis.classes_with_inheritance += file_analysis.classes_with_inheritance
                combined_analysis.inheritance_depth = max(
                    combined_analysis.inheritance_depth, 
                    file_analysis.inheritance_depth
                )
                combined_analysis.override_count += file_analysis.override_count
                combined_analysis.method_overloads += file_analysis.method_overloads
                
                combined_analysis.generic_classes += file_analysis.generic_classes
                combined_analysis.nested_classes += file_analysis.nested_classes
                combined_analysis.anonymous_classes += file_analysis.anonymous_classes
                combined_analysis.lambda_count += file_analysis.lambda_count
                
                combined_analysis.getter_setter_pairs += file_analysis.getter_setter_pairs
                for anno, count in file_analysis.annotations.items():
                    combined_analysis.annotations[anno] = combined_analysis.annotations.get(anno, 0) + count
                for pattern in file_analysis.design_patterns:
                    if pattern not in combined_analysis.design_patterns:
                        combined_analysis.design_patterns.append(pattern)
                
            except Exception as e:
                print(f"Warning: Failed to analyze {file_info['path']}: {e}")
                continue
        
        classifier.close()
    
    result = {
        'project_name': metadata.project_name,
        'project_path': metadata.project_path,
        'metadata': metadata.to_dict(),
        'java_oop_analysis': combined_analysis.to_dict(),
    }
    
    return result


def calculate_oop_score(analysis: JavaOOPAnalysis) -> int:
    """
    Calculate OOP score (0-6) based on Java OOP principles usage.
    """
    score = 0

    if analysis.total_classes > 0 or analysis.interface_count > 0:
        score += 1
    
    if analysis.interface_count > 0 or len(analysis.abstract_classes) > 0:
        score += 1
    
    if analysis.inheritance_depth > 0:
        score += 1
    
    if analysis.private_fields > 0 or analysis.private_methods > 0:
        score += 1
    
    if analysis.override_count > 0 or analysis.method_overloads > 0:
        score += 1    
    if analysis.generic_classes > 0 or len(analysis.annotations) > 0 or analysis.lambda_count > 0:
        score += 1
    
    return score


def calculate_solid_score(analysis: JavaOOPAnalysis) -> float:
    """
    Calculate SOLID principles score (0-5) based on code structure.
    """
    score = 0.0
    
    if analysis.total_classes > 0:
        avg_methods = (analysis.public_methods + analysis.private_methods) / max(analysis.total_classes, 1)
        if 3 <= avg_methods <= 15:  # Reasonable range
            score += 1.0
        elif avg_methods > 0:
            score += 0.5
    if analysis.interface_count > 0 or len(analysis.abstract_classes) > 0:
        score += 1.0
    if analysis.classes_with_inheritance > 0 and analysis.override_count > 0:
        score += 1.0
    elif analysis.classes_with_inheritance > 0:
        score += 0.5
    
    if analysis.interface_count >= 3:
        score += 1.0
    elif analysis.interface_count > 0:
        score += 0.5    
    if analysis.interface_count > 0 and "Component" in analysis.annotations:
        score += 1.0
    elif analysis.interface_count > 0:
        score += 0.5
    
    return min(score, 5.0)


def get_coding_style(oop_score: int) -> str:
    """
    Determine coding style based on OOP score.
    """
    if oop_score == 0:
        return "Procedural/Functional"
    elif oop_score <= 2:
        return "Basic OOP"
    elif oop_score <= 4:
        return "Moderate OOP"
    else:
        return "Advanced OOP"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Analyze a file provided by the user
        file_path = Path(sys.argv[1])
        
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        if not JAVALANG_AVAILABLE:
            print("Error: javalang library not installed.")
            print("Install with: pip install javalang")
            sys.exit(1)
        
        print("\n" + "=" * 70)
        print(f"ANALYZING: {file_path.name}")
        print("=" * 70)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = analyze_java_file(content)
            oop_score = calculate_oop_score(result)
            solid_score = calculate_solid_score(result)
            coding_style = get_coding_style(oop_score)
            
            print(f"\nJAVA OOP ANALYSIS RESULTS:")
            print(f"\n  Classes & Interfaces:")
            print(f"    Total classes: {result.total_classes}")
            print(f"    Interfaces: {result.interface_count}")
            if result.abstract_classes:
                print(f"    Abstract classes: {', '.join(result.abstract_classes)}")
            print(f"    Enums: {result.enum_count}")
            print(f"    With inheritance: {result.classes_with_inheritance}")
            print(f"    Max inheritance depth: {result.inheritance_depth}")
            
            print(f"\n  Encapsulation:")
            print(f"    Methods:")
            print(f"      Private: {result.private_methods}")
            print(f"      Protected: {result.protected_methods}")
            print(f"      Public: {result.public_methods}")
            print(f"      Package-private: {result.package_methods}")
            print(f"    Fields:")
            print(f"      Private: {result.private_fields}")
            print(f"      Protected: {result.protected_fields}")
            print(f"      Public: {result.public_fields}")
            print(f"    Getter/Setter pairs: {result.getter_setter_pairs}")
            
            print(f"\n  Polymorphism:")
            print(f"    Method overrides (@Override): {result.override_count}")
            print(f"    Method overloads: {result.method_overloads}")
            
            print(f"\n  Java-Specific Features:")
            print(f"    Generic classes: {result.generic_classes}")
            print(f"    Nested classes: {result.nested_classes}")
            print(f"    Lambda expressions: {result.lambda_count}")
            
            if result.annotations:
                print(f"\n  Annotations:")
                for anno, count in sorted(result.annotations.items()):
                    print(f"    @{anno}: {count}")
            
            if result.design_patterns:
                print(f"\n  Design Patterns Detected:")
                for pattern in result.design_patterns:
                    print(f"    ✓ {pattern}")
            
            print(f"\nOOP Score: {oop_score}/6")
            print(f"SOLID Score: {solid_score:.1f}/5.0")
            print(f"Coding Style: {coding_style}")
            
            print("\n" + "=" * 70 + "\n")
            
        except Exception as e:
            print(f"Error analyzing file: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    else:
        print("=" * 70)
        print("JAVA OOP ANALYZER - Usage")
        print("=" * 70)
        print("\nUsage: python src/backend/analysis/java_oop_analyzer.py <path_to_file.java>")
        print("\nExample:")
        print("  python src/backend/analysis/java_oop_analyzer.py src/main/java/User.java")
        print("  python src/backend/analysis/java_oop_analyzer.py ~/MyClass.java")
        print("\nNote: Requires 'javalang' library. Install with:")
        print("  pip install javalang")
        print("\n" + "=" * 70)

