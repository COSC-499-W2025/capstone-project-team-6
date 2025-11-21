


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
    


    def _traverse_ast(self, cursor, filename: str, parent_struct: Optional[str] = None):
        """
        Recursively traverse the Abstract Syntax Tree.
        
        Args:
            cursor: Current AST node (from libclang)
            filename: Source filename (for header vs implementation tracking)
            parent_struct: If we're inside a struct, this is its name
        
        This is the core traversal function that visits every node in the AST.
        For each node type, we call specialized analysis functions to add to stats.
        
        Key AST node types we care about:
        - STRUCT_DECL: Struct declarations
        - FUNCTION_DECL: Function declarations
        - TYPEDEF_DECL: Typedef statements
        - ENUM_DECL: Enum definitions
        - FIELD_DECL: Struct fields (when inside a struct)

        Note the base of this was taken from C++ with changes made for C compatability
        """
        
        #look for user code
        if cursor.location.file and cursor.location.file.name.startswith('/usr'):
            return
        
        #STRUCT DECLARATIONS 
        if cursor.kind == CursorKind.STRUCT_DECL:
            self._analyze_struct(cursor, filename)
        
        #FUNCTION DECLARATIONS
        elif cursor.kind == CursorKind.FUNCTION_DECL:
            self._analyze_function(cursor, filename)
        
        #TYPEDEF DECLARATIONS
        elif cursor.kind == CursorKind.TYPEDEF_DECL:
            self.analysis.typedef_count += 1
            # Check if it's a struct typedef
            underlying = cursor.underlying_typedef_type
            if underlying.kind == TypeKind.RECORD:  # RECORD = struct/union
                struct_name = underlying.spelling.replace('struct ', '')
                if struct_name in self.structs:
                    self.structs[struct_name].has_typedef = True
        
        #ENUM DECLARATIONS
        elif cursor.kind == CursorKind.ENUM_DECL:
            self.analysis.enum_count += 1
            # Check if it's an error enum
            enum_name = cursor.spelling.lower() if cursor.spelling else ""
            if 'error' in enum_name or 'status' in enum_name:
                self.analysis.error_enum_count += 1
        
        
        # RECURSE TO CHILDREN
        for child in cursor.get_children():
            # If we're entering a struct, pass its name down
            new_parent = parent_struct
            if cursor.kind == CursorKind.STRUCT_DECL and cursor.spelling:
                new_parent = cursor.spelling
            
            #recursive function
            self._traverse_ast(child, filename, new_parent)
    
    def _analyze_struct(self, cursor, filename: str):
        """
        Analyze a struct declaration.
        
        Args:
            cursor: AST node for the struct
            filename: Source file name
        
        Detects:
        1. Whether it's just a forward declaration or full definition
        2. Number of fields
        3. Function pointer fields
        4. Creates CStructInfo for tracking
        
        Forward declaration example:
            struct Vector;  // Just declaration (opaque pointer candidate)
        
        Full definition example:
            struct Vector {
                int size;
                void (*push)(struct Vector*, int);  // Function pointer field!
            };
        """
        
        struct_name = cursor.spelling
        
        if not struct_name:
            return
        
        is_definition = cursor.is_definition()
        
        if is_definition:
            # Full struct definition
            self.defined_structs.add(struct_name)
            self.analysis.total_structs += 1
            
            # Create or update struct info
            if struct_name not in self.structs:
                self.structs[struct_name] = CStructInfo(name=struct_name)
            
            struct_info = self.structs[struct_name]
            
            # Analyze fields
            field_count = 0
            function_pointer_count = 0
            
            for child in cursor.get_children():
                if child.kind == CursorKind.FIELD_DECL:
                    field_count += 1
                    
                    # Check if this field is a function pointer
                    if self._is_function_pointer_type(child.type):
                        function_pointer_count += 1
                        self.analysis.function_pointer_fields += 1
            
            struct_info.field_count = field_count
            struct_info.function_pointer_count = function_pointer_count
            
            #check for VTable pattern: struct with 2+ function pointers (polymorphism)
            if function_pointer_count >= 2:
                self.analysis.vtable_structs += 1
        
        else:
            self.declared_structs.add(struct_name)
    
    
    def _is_function_pointer_type(self, type_obj) -> bool:
        """
        Check if a type is a function pointer.
        
        Args:
            type_obj: clang Type object
        
        Returns:
            True if the type is a function pointer
        
        
        Type hierarchy:
            POINTER -> FUNCTIONPROTO = function pointer
            POINTER -> INT = regular pointer
        """
        if type_obj.kind == TypeKind.POINTER:
            pointee = type_obj.get_pointee()
            return pointee.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO)
        return False

    def _analyze_function(self, cursor, filename: str):
        """
        Analyze a function declaration.
        
        Args:
            cursor: AST node for the function
            filename: Source file name
        
        Detects:
        1. Static vs non-static (encapsulation indicator)
        2. OOP-style naming (ClassName_method pattern)
        3. Memory management functions (malloc/free usage)
        4. Constructor/destructor patterns (_create/_destroy)
        5. Error handling (functions returning status codes)
        6. Header vs implementation (public vs internal API)
        """
        
        func_name = cursor.spelling
        if not func_name:
            return
        
        #avoid dupli
        if func_name in self.functions:
            return
        
        self.analysis.total_functions += 1
        
        #STATIC FUNCTION DETECTION
        #Static functions are only visible in their file
        storage_class = cursor.storage_class
        is_static = (storage_class == StorageClass.STATIC)
        
        if is_static:
            self.analysis.static_functions += 1
        
        #OOP-STYLE NAMING CONVENTION
        if self._matches_oop_naming(func_name):
            self.analysis.oop_style_naming_count += 1
            
            # link to struct
            struct_name = func_name.split('_')[0]
            if struct_name in self.structs:
                self.structs[struct_name].associated_functions.append(func_name)
        
        #CONSTRUCTOR/DESTRUCTOR PATTERN
        #constructor
        if func_name.endswith('_create') or func_name.endswith('_new'):
            self.create_functions.add(func_name)
        
        #destructors
        if (func_name.endswith('_destroy') or 
            func_name.endswith('_free') or 
            func_name.endswith('_delete')):
            self.destroy_functions.add(func_name)
        
        #MEMORY MANAGEMENT DETECTION
        # Check if function uses malloc/free (dynamic memory)
        if cursor.is_definition():
            # Get function body tokens
            for token in cursor.get_tokens():
                token_text = token.spelling
                
                #Memory allocation
                if token_text in ['malloc', 'calloc', 'realloc']:
                    self.analysis.malloc_usage += 1
                    break
            
            for token in cursor.get_tokens():
                token_text = token.spelling
                
                # Memory deallocation
                if token_text == 'free':
                    self.analysis.free_usage += 1
                    break
        
        #ERROR HANDLING DETECTION
        #Functions returning int/long might be returning error codes
        return_type = cursor.result_type.spelling
        if return_type in ['int', 'long', 'ssize_t', 'ptrdiff_t']:
            self.analysis.functions_returning_status += 1
        
        #API DESIGN: Header vs Implementation
        if filename.endswith('.h'):
            self.analysis.header_functions += 1
        else:
            self.analysis.implementation_functions += 1
        
        # Store function metadata
        self.functions[func_name] = {
            'name': func_name,
            'is_static': is_static,
            'return_type': return_type,
            'filename': filename
        }
    
    def _matches_oop_naming(self, func_name: str) -> bool:
        '''basic name check'''
        pattern = r'^[A-Z][a-zA-Z0-9]*_[a-z][a-zA-Z0-9]*$'
        return bool(re.match(pattern, func_name))

    def _detect_opaque_pointers(self):
        """
        Detect opaque pointer pattern
        
        Pattern:
            In header (.h):
                struct MyType;  // Forward declaration only
                struct MyType* MyType_create();  // Return pointer
            
            In implementation (.c):
                struct MyType {  // Full definition hidden
                    int private_data;
                };
        
        Users can only access via pointer, can't see internals.
        This forces use of provided API functions (encapsulation).
        """
        # Opaque pointers are structs that are declared but never defined
        opaque = self.declared_structs - self.defined_structs 
        self.analysis.opaque_pointer_structs = len(opaque)
        
        # Mark structs as opaque
        for struct_name in opaque:
            if struct_name not in self.structs:
                self.structs[struct_name] = CStructInfo(name=struct_name)
            self.structs[struct_name].is_opaque = True
    

    def _match_constructor_destructor_pairs(self):
        """
        Match constructor/destructor function pairs.
        High pair count = disciplined resource management
        """
        
        create_bases = set()
        for func in self.create_functions:
            if func.endswith('_create'):
                base = func[:-7]
            elif func.endswith('_new'):
                base = func[:-4]
            else:
                continue
            create_bases.add(base)
        

        destroy_bases = set()
        for func in self.destroy_functions:
            if func.endswith('_destroy'):
                base = func[:-8]
            elif func.endswith('_free'):
                base = func[:-5]
            elif func.endswith('_delete'):
                base = func[:-7]
            else:
                continue
            destroy_bases.add(base)
        
        # Count matches
        matched = create_bases & destroy_bases
        self.analysis.constructor_destructor_pairs = len(matched)
    
    
    # done by AI completely do not know the patterns well enough to edit 
    def _detect_design_patterns(self):
        """
        Detect common design patterns adapted for C.
        
        1. FACTORY PATTERN
           - Functions named Type_create() or Type_new()
           - Encapsulates object creation
           - Example: Vector* Vector_create(int capacity);
        
        2. SINGLETON PATTERN
           - Static variable + getInstance() function
           - Ensures single instance
           - Example: static Connection* instance = NULL;
                      Connection* Connection_getInstance();
        
        3. STRATEGY PATTERN
           - Struct with function pointers (swappable algorithms)
           - Example: struct Sorter { int (*compare)(void*, void*); };
        
        4. OBSERVER PATTERN
           - Callback function pointers
           - Fields named 'callback', 'handler', 'notify'
           - Example: struct Button { void (*on_click)(void*); };
        
        All detection is heuristic-based (name matching, structure analysis).
        """
        patterns = set()
        
        # === FACTORY PATTERN ===
        # Detected by presence of _create() or _new() functions
        if self.create_functions:
            patterns.add("Factory")
        
        # === SINGLETON PATTERN ===
        # Heuristic: function named "getInstance" or "instance"
        for func_name in self.functions:
            if 'getInstance' in func_name or func_name.endswith('_instance'):
                patterns.add("Singleton")
                break
        
        # === STRATEGY PATTERN ===
        # Detected by VTable structs
        # These allow swapping implementations at runtime
        if self.analysis.vtable_structs > 0:
            patterns.add("Strategy")
        
        # === OBSERVER PATTERN ===
        # Detected by callback/handler/notify patterns in struct fields
        for struct_name, struct_info in self.structs.items():
            if struct_info.function_pointer_count > 0:
                # Check if any function pointer fields suggest callbacks
                # This is a simplified check - in practice, you'd examine field names
                # For now, we'll use the presence of function pointers + certain struct names
                if any(keyword in struct_name.lower() 
                       for keyword in ['event', 'listener', 'observer', 'callback']):
                    patterns.add("Observer")
                    break
        
        self.analysis.design_patterns = sorted(list(patterns))



#analysis = COOPAnalysis(total_structs=5, design_patterns=["Factory", "Singleton"])
#print(analysis.to_dict())





