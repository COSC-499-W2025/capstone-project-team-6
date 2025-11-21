


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


@dataclass
class CStructInfo:
    """
    Information about a single C struct.
    """
    
    name: str    
    field_count: int = 0    
    function_pointer_count: int = 0    
    is_opaque: bool = False    
    has_typedef: bool = False    
    associated_functions: List[str] = field(default_factory=list)
    """
    Functions that follow StructName_function naming pattern.
    """


class COOPAnalyzer:
    """
    Analysis Process:
    1. Parse C file into AST (Abstract Syntax Tree) using libclang
    2. Traverse AST to find structs, functions, typedefs, enums
    3. Detect OOP-style patterns (function pointers, naming conventions)
    4. Analyze memory management and error handling
    5. Identify design patterns
    6. Return comprehensive analysis
    
    """

    def __init__(self):
        """        
        State maintained during analysis:
        - analysis: Accumulates all metrics
        - structs: Dictionary of struct name -> CStructInfo
        - functions: Dictionary of function name -> metadata
        - declared_structs: Forward declarations
        - defined_structs: Full struct definitions
        """
        self.analysis = COOPAnalysis()
        self.structs: Dict[str, CStructInfo] = {}
        self.functions: Dict[str, Dict] = {}
        self.declared_structs: Set[str] = set()
        self.defined_structs: Set[str] = set()
        self.create_functions: Set[str] = set() 
        self.destroy_functions: Set[str] = set()

    def analyze_file(self, content: str, filename: str = "temp.c") -> COOPAnalysis:
        """
        analyze a single C file.
        
        Args:
            content: The C source code as a string
            filename: Name of the file (used for .h vs .c detection)
        
        Returns:
            COOPAnalysis object with all metrics
        
        Process:
        1. Check if libclang is available
        2. Write content to temporary file (libclang needs actual files)
        3. Parse file into AST
        4. Traverse AST to extract information
        5. Run post-processing (pattern detection, pair matching)
        6. Clean up temporary file
        7. Return analysis
        """
        
        if not CLANG_AVAILABLE:
            print("Error: libclang not available")
            return self.analysis
        
        try:
            import tempfile
            import os
            
            # file extension based on filename
            suffix = '.h' if filename.endswith('.h') else '.c'
            
            # Write to temp file and get path
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
                f.write(content)
                temp_path = f.name        
                
            # Parse with libclang
            index = clang.cindex.Index.create()
            translation_unit = index.parse(
                temp_path,
                args=['-std=c11', '-x', 'c']  # Use C11 standard
            )
            
            # Check for parse errors
            if translation_unit.diagnostics:
                for diag in translation_unit.diagnostics:
                    if diag.severity >= clang.cindex.Diagnostic.Error:
                        print(f"Parse error: {diag.spelling}")
            
            # Traverse the Abstract Syntax Tree
            self._traverse_ast(translation_unit.cursor, filename)
            
            # Post-processing
            self._detect_opaque_pointers()
            self._match_constructor_destructor_pairs()
            self._detect_design_patterns()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"Warning: Failed to parse C file: {e}")
            import traceback
            traceback.print_exc()
        
        return self.analysis
    


    def _traverse_ast(self):
        return

    def _detect_opaque_pointers(self):
        return

    def _match_constructor_destructor_pairs(self):
        return
    
    def _detect_design_patterns(self):
        return


#analysis = COOPAnalysis(total_structs=5, design_patterns=["Factory", "Singleton"])
#print(analysis.to_dict())





