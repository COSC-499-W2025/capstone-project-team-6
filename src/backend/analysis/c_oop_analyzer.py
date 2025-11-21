


#copied imports from c++ code

import re
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Set,Tuple


try:
    import clang.cindex
    from clang.cindex import CursorKind, TypeKind, StorageClass
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
class COOPAnalysis:
    """
    Data class to store C OOP-style analysis results.
    
    Metric Categories:
    1. Basic Structure (structs, functions)
    2. OOP-Style Patterns (function pointers, naming conventions)
    3. Memory Management (malloc/free, constructors/destructors)
    4. Error Handling (return codes, error enums)
    5. API Design (header vs implementation separation)
    6. Design Patterns (Factory, Singleton, etc.)
    """
    
    # BASIC STRUCTURE METRICS
    total_structs: int = 0
    total_functions: int = 0
    static_functions: int = 0
    """
    Functions with 'static' storage class.
    - identifys encapsulation
    -visible in compilation unit
    - High count = good encapsulation practices.
    """

    typedef_count: int = 0
    """for abstraction"""
    enum_count: int = 0
    
    # OOP-STYLE PATTERN METRICS
    opaque_pointer_structs: int = 0
    """
    Structs that are forward-declared but not defined in header files.
    This is C's information hiding mechanism - users can't see internal structure.
    Example: In header: 'struct MyType;' but definition in .c file
    This is equivalent to 'private' class members in OOP.
    """
    
    function_pointer_fields: int = 0
    vtable_structs: int = 0
    """
    Structs containing 2+ function pointers.
    shows  polymorphism
    """
    oop_style_naming_count: int = 0

    
    # MEMORY MANAGEMENT METRICS - C is all about memory management
    malloc_usage: int = 0
    """functions that call malloc/calloc/realloc (dynamic memory allocation)"""
    
    free_usage: int = 0
    """functions that call free (memory deallocation)"""
    
    constructor_destructor_pairs: int = 0
    """
    Matched pairs of Type_create/Type_new with Type_destroy/Type_free functions.
    Example: Vector_create() paired with Vector_destroy()
    High count = RAII(Resource Acquisition Is Initialization) -style discipline in C.
    """
    
    # ERROR HANDLING METRICS 
    functions_returning_status: int = 0
    error_enum_count: int = 0
    
    # API DESIGN METRICS
    header_functions: int = 0
    """Functions declared in .h files (public API)"""
    
    implementation_functions: int = 0
    """Functions only in .c files (internal implementation)"""
    
    # DESIGN PATTERNS
    design_patterns: List[str] = field(default_factory=list)
    """
    Detected design patterns adapted for C:
    - Factory: Type_create() functions
    - Singleton: Static variable + getInstance() pattern
    - Strategy: Structs with function pointers for swappable behavior
    - Observer: Callback function pointers
    """
    
    def to_dict(self) -> Dict:
        """Convert analysis to dictionary for JSON serialization"""
        return asdict(self)


analysis = COOPAnalysis(total_structs=5, design_patterns=["Factory", "Singleton"])
print(analysis.to_dict())





