import ast
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Set, Optional


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
        if method_name.startswith('__') and not method_name.endswith('__'):
            self.analysis.private_methods += 1
        elif method_name.startswith('_'):
            self.analysis.protected_methods += 1
        else:
            self.analysis.public_methods += 1
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'property':
                self.analysis.properties_count += 1

        if method_name.startswith('__') and method_name.endswith('__'):
            if method_name not in ('__init__', '__new__', '__del__'):
                self.analysis.operator_overloads += 1
    
    




