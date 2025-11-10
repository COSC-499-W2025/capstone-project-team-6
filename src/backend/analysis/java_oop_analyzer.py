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
    
    # Abstraction
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
    
    # Polymorphism
    override_count: int = 0
    method_overloads: int = 0
    
    # Inheritance
    classes_with_inheritance: int = 0
    inheritance_depth: int = 0
    
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
        """Convert to dictionary."""
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
            print(f"Warning: Failed to parse Java file: {e}")
            return self.analysis
    
    def _visit_tree(self, tree):
        """Visit the Java AST and extract information."""
        # Classes , interfaces and enums
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            self._analyze_class(node, path)
        
        for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
            self._analyze_interface(node, path)
        
        for path, node in tree.filter(javalang.tree.EnumDeclaration):
            self._analyze_enum(node, path)
        # Methods
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            self._analyze_method(node, path)
        
        # Fields
        for path, node in tree.filter(javalang.tree.FieldDeclaration):
            self._analyze_field(node, path)
        
        # Lambdas
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
        if len(path) > 1:
            class_info.is_nested = True
            self.analysis.nested_classes += 1
        
        # Abstract class
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
