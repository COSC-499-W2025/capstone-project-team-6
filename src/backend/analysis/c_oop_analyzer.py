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
    - identifies encapsulation
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
        self.header_only_structs: Set[str] = set()  # Structs declared in .h but not defined in .c
        self.create_functions: Set[str] = set()
        self.destroy_functions: Set[str] = set()
        self.function_pointer_typedefs: Set[str] = set()


    def analyze_file(self, content: str, filename: str = "temp.c", include_dirs: Optional[List[str]] = None) -> COOPAnalysis:
        """
        analyze a single C file.

        Args:
            content: The C source code as a string
            filename: Name of the file (used for .h vs .c detection)
            include_dirs: Optional list of directories to search for includes

        Returns:
            COOPAnalysis object with all metrics

        Process:
        1. Check if libclang is available
        2. Write content to temporary file (libclang needs actual files)
        3. Parse file into AST with include directories
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

            # Build compile args with include directories
            compile_args = ['-std=c11', '-x', 'c']
            if include_dirs:
                for inc_dir in include_dirs:
                    compile_args.extend(['-I', inc_dir])

            translation_unit = index.parse(
                temp_path,
                args=compile_args
            )
            
            # Check for parse errors (ignore system header errors)
            if translation_unit.diagnostics:
                for diag in translation_unit.diagnostics:
                    if diag.severity >= clang.cindex.Diagnostic.Error:
                        # Ignore errors about system headers not being found
                        if "file not found" in diag.spelling.lower():
                            # Check if it's a system header (angle brackets)
                            if any(h in diag.spelling for h in ["<", "stdlib", "stdio", "string", "stddef", "stdint"]):
                                continue
                        print(f"Parse error: {diag.spelling}")
            
            # Traverse the Abstract Syntax Tree
            self._traverse_ast(translation_unit.cursor, filename)

            # Clean up temporary file
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"Warning: Failed to parse C file: {e}")
            import traceback
            traceback.print_exc()
        
        return self.analysis

    def finalize_analysis(self):
        """
        Run post-processing after all files have been analyzed.
        This should be called once after analyzing all files in a project.
        """
        self._detect_opaque_pointers()
        self._match_constructor_destructor_pairs()
        self._detect_design_patterns()


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
        #elif cursor.kind == CursorKind.TYPEDEF_DECL:
        #    self.analysis.typedef_count += 1
        #    # Check if it's a struct typedef
        #    underlying = cursor.underlying_typedef_type
        #    if underlying.kind == TypeKind.RECORD:  # RECORD = struct/union
        #        struct_name = underlying.spelling.replace('struct ', '')
        #        if struct_name in self.structs:
        #            self.structs[struct_name].has_typedef = True
        
        elif cursor.kind == CursorKind.TYPEDEF_DECL:
            self.analysis.typedef_count += 1
            typedef_name = cursor.spelling or ""
            underlying = cursor.underlying_typedef_type

            # Check if it's a struct typedef (existing code)
            if underlying.kind == TypeKind.RECORD:
                struct_name = underlying.spelling.replace('struct ', '')
                if struct_name in self.structs:
                    self.structs[struct_name].has_typedef = True

            # NEW: detect function-pointer typedefs
            is_fp = False
            try:
                canonical = underlying.get_canonical()
            except Exception:
                canonical = underlying

            # Pointer-to-function via TypeKind (if clang can see it)
            try:
                if canonical.kind == TypeKind.POINTER:
                    pointee = canonical.get_pointee()
                    if pointee.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO):
                        is_fp = True
            except Exception:
                pass

            # Fallback: spelling like "void (*)(int, void *)"
            spelling = getattr(canonical, "spelling", "") or getattr(underlying, "spelling", "")
            if "(*" in spelling:
                is_fp = True

            if is_fp and typedef_name:
                self.function_pointer_typedefs.add(typedef_name)



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
            # Forward declaration only
            self.declared_structs.add(struct_name)
            # If this is in a header file, track it specially
            if filename.endswith('.h'):
                self.header_only_structs.add(struct_name)
    
    
        def _is_function_pointer_type(self, type_obj) -> bool:
            """
            Check if a type is a function pointer.

            Handles:
            - Direct function pointers: void (*fn)(int);
            - Typedef-based function pointers: typedef void (*CB)(int); CB cb;
            """
            if not CLANG_AVAILABLE or type_obj is None:
                return False

            # 1) If the type spelling is a known function-pointer typedef, we're done
            spelling = getattr(type_obj, "spelling", "") or ""
            if spelling in self.function_pointer_typedefs:
                return True

            # 2) Canonical pointer-to-function detection
            try:
                canonical = type_obj.get_canonical()
            except Exception:
                canonical = type_obj

            try:
                if canonical.kind == TypeKind.POINTER:
                    pointee = canonical.get_pointee()
                    return pointee.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO)
            except Exception:
                pass

            # 3) Fallback heuristic: "void (*)(...)" etc.
            canon_spelling = getattr(canonical, "spelling", "") or spelling
            if "(*" in canon_spelling:
                return True

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

        # Track function only once for counting, but still process definitions
        is_definition = cursor.is_definition()
        already_counted = func_name in self.functions

        if not already_counted:
            self.analysis.total_functions += 1
        
        #STATIC FUNCTION DETECTION
        #Static functions are only visible in their file
        storage_class = cursor.storage_class
        is_static = (storage_class == StorageClass.STATIC)

        if not already_counted:
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
        # Always process definitions to catch malloc/free
        if is_definition:
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
        
        if not already_counted:
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
            return_type = cursor.result_type.spelling
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
        # Opaque pointers are structs that were declared in headers
        # but their full definition is hidden in .c files
        # Use header_only_structs which tracks structs forward-declared in .h files
        opaque = self.header_only_structs
        self.analysis.opaque_pointer_structs = len(opaque)

        # Mark structs as opaque
        for struct_name in opaque:
            if struct_name not in self.structs:
                self.structs[struct_name] = CStructInfo(name=struct_name)
            self.structs[struct_name].is_opaque = True

    def _is_function_pointer_type(self, type_obj) -> bool:
        """
        Check if a type is a function pointer.
        Handles:
        - Direct function pointers: int (*fn)(int, int);
        - Typedef-based function pointers: typedef void (*CB)(int); CB cb;
        """
        if not CLANG_AVAILABLE or type_obj is None:
            return False
        # 1) If the type spelling is a known function-pointer typedef, we're done
        spelling = getattr(type_obj, "spelling", "") or ""
        if hasattr(self, "function_pointer_typedefs") and spelling in self.function_pointer_typedefs:
            return True
        # 2) Canonical pointer-to-function detection via libclang
        try:
            canonical = type_obj.get_canonical()
        except Exception:
            canonical = type_obj
        try:
            if canonical.kind == TypeKind.POINTER:
                pointee = canonical.get_pointee()
                if pointee.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO):
                    return True
        except Exception:
            # If anything goes wrong with TypeKind inspection, fall through to heuristics
            pass
        # 3) Fallback heuristic: function pointer spellings usually contain "(*"
        canon_spelling = getattr(canonical, "spelling", "") or spelling
        if "(*" in canon_spelling:
            return True
        return False


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

#helper function to make objects for classes
def analyze_c_file(content: str, filename: str = "temp.c") -> COOPAnalysis:
    analyzer = COOPAnalyzer()
    analyzer.analyze_file(content, filename)
    analyzer.finalize_analysis()
    return analyzer.analysis


def analyze_c_project(zip_path: Path, project_path: str = "") -> Dict:
    """
    Perform deep OOP-style analysis on a C project inside a ZIP file.
    
    This function integrates with the existing project analysis pipeline:
    1. Uses MetadataExtractor to get project info
    2. Uses FileClassifier to find all C files
    3. Analyzes each C file individually
    4. Aggregates results into combined analysis
    
    Args:
        zip_path: path to ZIP file containing the project
        project_path: relative path within ZIP to the project root (should be )
    
    Returns:
        Dictionary containing:
        - project_name: Name of the project
        - project_path: Path analyzed
        - metadata: Project metadata (languages, files, etc.)
        - c_oop_analysis: Combined COOPAnalysis for all C files
    """
    project_name = Path(zip_path).stem

    # extract meta data
    metadata_obj = None
    metadata_dict: Dict = {
        "project_name": project_name,
        "project_path": project_path,
    }

    if MetadataExtractor is not None:
        try:
            with MetadataExtractor(zip_path) as extractor:
                metadata_obj = extractor.extract_project_metadata(project_path)
                project_name = getattr(metadata_obj, "project_name", project_name)
                project_path = getattr(metadata_obj, "project_path", project_path)
                metadata_dict = metadata_obj.to_dict()
        except Exception as e:
            print(f"Warning: MetadataExtractor failed: {e}")

    analyzer = COOPAnalyzer()

    # Create temp directory for extracting all C files
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp(prefix="c_analyzer_")

    try:
        #list c files
        with zipfile.ZipFile(zip_path, "r") as zf:
            code_paths: List[str] = []

            classifier = None
            if FileClassifier is not None:
                try:
                    classifier = FileClassifier(zip_path)
                    classification = classifier.classify_project(project_path)

                    files_section = classification.get("files", {})
                    code_section = files_section.get("code", {})

                    if isinstance(code_section, dict):
                        for value in code_section.values():
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, str):
                                        if item.endswith((".c", ".h")):
                                            code_paths.append(item)
                                    elif isinstance(item, dict):
                                        path = (
                                            item.get("path")
                                            or item.get("relative_path")
                                            or item.get("file_path")
                                        )
                                        if isinstance(path, str) and path.endswith((".c", ".h")):
                                            code_paths.append(path)
                except Exception as e:
                    print(f"Warning: FileClassifier failed: {e}")
                finally:
                    if classifier is not None and hasattr(classifier, "close"):
                        try:
                            classifier.close()
                        except Exception:
                            pass

            if not code_paths:
                for name in zf.namelist():
                    if name.endswith(".c") or name.endswith(".h"):
                        code_paths.append(name)

            #deduplicate & sort
            code_paths = sorted(set(code_paths))

            # Extract all C/H files to temp directory first
            for rel_path in code_paths:
                try:
                    # Extract file preserving structure
                    target_path = Path(temp_dir) / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    content = zf.read(rel_path).decode("utf-8", errors="ignore")
                    target_path.write_text(content)
                except Exception as e:
                    print(f"Warning: Failed to extract {rel_path}: {e}")
                    continue

        # Now analyze each file with include paths
        for rel_path in code_paths:
            try:
                target_path = Path(temp_dir) / rel_path
                if not target_path.exists():
                    continue

                content = target_path.read_text()
                filename = Path(rel_path).name

                # Get all directories that might contain headers
                include_dirs = [
                    temp_dir,  # Root directory
                    str(target_path.parent),  # File's own directory
                ]

                analyzer.analyze_file(content, filename, include_dirs)

            except Exception as e:
                print(f"Warning: Failed to analyze {rel_path}: {e}")
                continue

        # Run post-processing after all files are analyzed
        analyzer.finalize_analysis()
        combined = analyzer.analysis
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    return {
        "project_name": project_name,
        "project_path": project_path,
        "metadata": metadata_dict,
        "c_oop_analysis": combined.to_dict(),
    }


#scoring

def calculate_oop_score(analysis: COOPAnalysis) -> int:
    """
    Calculate OOP-style score (0-6) based on C pattern usage.
    
    Scoring criteria:
    +1: Uses structs (basic data organization)
    +1: Uses opaque pointers (information hiding / encapsulation)
    +1: Uses static functions (file-scope encapsulation)
    +1: Uses function pointers (polymorphism simulation)
    +1: Has VTable structs (advanced polymorphism)
    +1: Uses design patterns or consistent OOP naming

    
    """
    score = 0
    
    # +1: Has structs (basic organization)
    if analysis.total_structs > 0:
        score += 1
    
    # +1: Uses opaque pointers (encapsulation / information hiding)
    if analysis.opaque_pointer_structs > 0:
        score += 1
    
    # +1: Uses static functions (file-scope encapsulation)
    if analysis.static_functions > 0:
        score += 1
    
    # +1: Uses function pointers (polymorphism-like behavior)
    if analysis.function_pointer_fields > 0:
        score += 1
    
    # +1: Has VTable structs (advanced polymorphism)
    if analysis.vtable_structs > 0:
        score += 1
    
    # +1: Uses design patterns or OOP naming conventions
    if analysis.design_patterns or analysis.oop_style_naming_count > 5:
        score += 1

    if (
        score >= 3
        and analysis.constructor_destructor_pairs > 0
        and analysis.opaque_pointer_structs > 0
    ):
        score += 1
    return min(score, 6)


def calculate_solid_score(analysis: COOPAnalysis) -> float:
    """
    Calculate SOLID-style score (0-3) for C code architecture.
    
    
    metrics used:
    S - Single Responsibility: Reasonable function count per struct
    O - Open/Closed: Use of function pointers for extensibility
    L - Liskov Substitution- dont care
    I - Interface Segregation: Clean API with header/implementation separation
    D - Dependency Inversion: dont care
    
    Since only 3 principles apply well to C, we use 0-3 scale.
    
    Scoring:
    +1.0: Good function-to-struct ratio 
    +1.0: Uses function pointers for extensibility
    +1.0: Clean API separation
    
    Args:
        analysis: COOPAnalysis object
    
    Returns:
        Float score from 0.0 to 3.0
    """

    score = 0.0
    
    #S
    if analysis.total_structs > 0:
        avg_funcs = analysis.total_functions / max(analysis.total_structs, 1)
        if 3 <= avg_funcs <= 15:
            score += 1.0
        elif avg_funcs > 0:
            score += 0.5
    
    #Open/Closed
    if analysis.vtable_structs > 0:
        score += 1.0
    elif analysis.function_pointer_fields > 0:
        score += 0.5
    
    # Interface Segregation
    if analysis.implementation_functions > analysis.header_functions > 0:
        score += 1.0
    elif analysis.header_functions > 0:
        score += 0.5
    
    return min(score, 3.0)


def get_coding_style(oop_score: int) -> str:
    """
    Determine coding style based on OOP score.
    
    Args:
        oop_score: Score from calculate_oop_score (0-6)
    
    Returns:
        String description of coding style
    """

    if oop_score == 0:
        return "Pure Procedural"
    elif oop_score <= 2:
        return "Structured C"
    elif oop_score <= 4:
        return "OOP-Influenced C"
    else:
        return "Advanced OOP-Style C"


def calculate_encapsulation_ratio(analysis: COOPAnalysis) -> float:
    """
    Calculate what percentage of functions use encapsulation.
    
    In C, encapsulation is achieved through:
    - Static functions
    - Opaque pointers 
    
    Returns:
        Percentage (0-100) of functions that are encapsulated
    """
    if analysis.total_functions == 0:
        return 0.0
    
    encapsulated = analysis.static_functions
    total = analysis.total_functions
    
    return (encapsulated / total) * 100


def calculate_memory_safety_score(analysis: COOPAnalysis) -> float:
    """
    Evaluates:
    - Constructor/destructor pair discipline
    - malloc/free balance
    
    Returns:
        Score from 0 to 10
    """
    score = 0.0
    
    # +5: constructor/destructor pairs (RAII-style)
    if analysis.constructor_destructor_pairs > 0:
        score += 5.0
    
    # +5: balanced malloc/free usage
    if analysis.malloc_usage > 0:
        if analysis.free_usage > 0:
            ratio = min(analysis.free_usage, analysis.malloc_usage) / analysis.malloc_usage
            score += 5.0 * ratio
    
    return score
