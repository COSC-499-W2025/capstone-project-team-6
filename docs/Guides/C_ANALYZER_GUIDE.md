# C OOP-Style Analyzer - Implementation Guide

## Overview

This analyzer detects **OOP-style patterns in C code**, It evaluates how professional C developers emulate OOP concepts using C idioms.

## Key Concepts

### 1. **The 17 Metrics We Track**

#### **Basic Structure (5 metrics)**
- `total_structs` - Number of struct definitions
- `total_functions` - All functions
- `static_functions` - File-scope only (encapsulation)
- `typedef_count` - Type abstractions
- `enum_count` - Enumeration types

#### **OOP-Style Patterns (4 metrics)**
- `opaque_pointer_structs` - Forward-declared structs (info hiding)
- `function_pointer_fields` - Function pointers in structs (methods)
- `vtable_structs` - Structs with 2+ function pointers (polymorphism)
- `oop_style_naming_count` - ClassName_method pattern usage

#### **Memory Management (3 metrics)**
- `malloc_usage` - Dynamic allocation
- `free_usage` - Memory deallocation
- `constructor_destructor_pairs` - Type_create/Type_destroy pairs

#### **Error Handling (2 metrics)**
- `functions_returning_status` - Functions returning int (error codes)
- `error_enum_count` - Error/status enums

#### **API Design (2 metrics)**
- `header_functions` - Public API (.h files)
- `implementation_functions` - Internal functions (.c files)

#### **Design Patterns (1 metric)**
- `design_patterns` - List of detected patterns

---

## Implementation Details

### **How We Parse C Code**

```python
# Step 1: Write content to temp file (libclang needs actual files)
with tempfile.NamedTemporaryFile(mode='w', suffix='.c') as f:
    f.write(content)
    
# Step 2: Parse with libclang
index = clang.cindex.Index.create()
translation_unit = index.parse(temp_path, args=['-std=c11', '-x', 'c'])

# Step 3: Traverse AST
self._traverse_ast(translation_unit.cursor, filename)
```

### **Key Detection Algorithms**

#### **1. Opaque Pointer Detection**
```python
# Track declarations vs definitions
if cursor.is_definition():
    defined_structs.add(name)  # Full definition
else:
    declared_structs.add(name)  # Just forward declaration

# Opaque = declared but never defined (hidden implementation)
opaque = declared_structs - defined_structs
```

**Example:**
```c
// header.h
struct Vector;  // Forward declaration (opaque)
struct Vector* Vector_create();

// vector.c  
struct Vector {  // Definition hidden in .c file
    int* data;
    int size;
};
```

#### **2. Function Pointer Detection (Polymorphism)**
```python
def _is_function_pointer_type(self, type_obj) -> bool:
    if type_obj.kind == TypeKind.POINTER:
        pointee = type_obj.get_pointee()
        return pointee.kind == TypeKind.FUNCTIONPROTO
    return False
```

**Example:**
```c
struct Animal {
    void (*speak)(void);  // Function pointer = method
};

// "Virtual" function table pattern
struct FileOps {
    int (*read)(void*, int);   // 2+ function pointers
    int (*write)(void*, int);  // = VTable struct
};
```

#### **3. OOP Naming Convention**
```python
def _matches_oop_naming(self, func_name: str) -> bool:
    # Pattern: StructName_methodName
    pattern = r'^[A-Z][a-zA-Z0-9]*_[a-z][a-zA-Z0-9]*$'
    return bool(re.match(pattern, func_name))
```

**Example:**
```c
Vector_push()    ✓ Matches
String_new()     ✓ Matches  
vector_push()    ✗ Lowercase start
my_helper()      ✗ No capital start
```

#### **4. Constructor/Destructor Pairing**
```python
# Track create/new functions
if func_name.endswith('_create') or func_name.endswith('_new'):
    create_functions.add(func_name)

# Track destroy/free functions
if func_name.endswith('_destroy') or func_name.endswith('_free'):
    destroy_functions.add(func_name)

# Match pairs by base name
# Vector_create ↔ Vector_destroy = 1 pair
```

**Example:**
```c
Vector* Vector_create(int capacity);  // Constructor
void Vector_destroy(Vector* v);       // Destructor
// This is C's RAII pattern
```

#### **5. Memory Management Tracking**
```python
# Scan function tokens for malloc/free
for token in cursor.get_tokens():
    if token.spelling in ['malloc', 'calloc', 'realloc']:
        self.analysis.malloc_usage += 1
    if token.spelling == 'free':
        self.analysis.free_usage += 1
```

#### **6. Static Function Detection (Encapsulation)**
```python
storage_class = cursor.storage_class
is_static = (storage_class == StorageClass.STATIC)

if is_static:
    self.analysis.static_functions += 1
```

**Why this matters:**
```c
static void helper() { }  // Only visible in this file (encapsulated)
void public_api() { }     // Visible everywhere
```

---

## Design Pattern Detection

### **Factory Pattern**
```c
// Detected by _create or _new functions
Vector* Vector_create(int capacity) {
    Vector* v = malloc(sizeof(Vector));
    // Initialize...
    return v;
}
```

### **Singleton Pattern**
```c
// Detected by getInstance or _instance functions
static Database* instance = NULL;
Database* Database_getInstance() {
    if (!instance) {
        instance = malloc(sizeof(Database));
    }
    return instance;
}
```

### **Strategy Pattern**
```c
// Detected by VTable structs (2+ function pointers)
struct Sorter {
    int (*compare)(void*, void*);  // Swappable algorithm
    void (*sort)(void*, int);
};
```

### **Observer Pattern**
```c
// Detected by callback/handler in struct names
struct EventListener {
    void (*on_event)(void*);  // Callback
};
```

---

## Scoring System

### **OOP Score (0-6)**
```
+1: Has structs (basic organization)
+1: Opaque pointers (information hiding)
+1: Static functions (encapsulation)
+1: Function pointers (polymorphism-like)
+1: VTable structs (advanced polymorphism)
+1: Design patterns or OOP naming (5+ matches)
```

### **SOLID Score (0-3)**
```
+1: Good function-to-struct ratio (3-15 functions/struct)
+1: Function pointers for extensibility
+1: Clean API (more internal than public functions)
```

### **Additional Metrics**
- **Encapsulation Ratio**: % of static functions
- **Memory Safety Score**: Constructor/destructor pairs + malloc/free balance

---

## Usage Examples

### **Analyze Single File**
```python
from c_oop_analyzer import analyze_c_file, calculate_oop_score

with open('vector.c', 'r') as f:
    code = f.read()

analysis = analyze_c_file(code, 'vector.c')
score = calculate_oop_score(analysis)

print(f"OOP Score: {score}/6")
print(f"Structs: {analysis.total_structs}")
print(f"VTables: {analysis.vtable_structs}")
```

### **Analyze Project**
```python
from pathlib import Path
from c_oop_analyzer import analyze_c_project

result = analyze_c_project(Path('my_project.zip'))

print(f"Project: {result['project_name']}")
print(f"Design Patterns: {result['c_oop_analysis']['design_patterns']}")
```

### **Command Line**
```bash
python c_oop_analyzer.py vector.c
python c_oop_analyzer.py mylib.h
```

---

## Resume-Worthy Insights

### **What to Highlight**

✅ **High OOP Score (4+/6)**
- "Implemented OOP patterns in C achieving 5/6 architectural score"

✅ **Constructor/Destructor Pairs**
- "Designed 12 struct types with RAII-style resource management"

✅ **Opaque Pointers**
- "Employed opaque pointer pattern for information hiding across 8 data structures"

✅ **VTable Usage**
- "Implemented polymorphic behavior via virtual function tables in 5 core abstractions"

✅ **Design Patterns**
- "Applied Factory, Strategy, and Observer patterns using C idioms"

✅ **Encapsulation**
- "Maintained 73% encapsulation rate through static functions"

✅ **Memory Safety**
- "Achieved 9.5/10 memory safety score with balanced malloc/free and constructor/destructor discipline"

---



## Testing Strategy

### **Test Cases to Create**

1. **Basic Struct Test**
   - Empty struct
   - Struct with simple fields
   - Multiple structs

2. **Function Pointer Test**
   - Struct with 1 function pointer
   - VTable struct (2+ function pointers)
   - No function pointers

3. **Opaque Pointer Test**
   - Forward declaration in header
   - Definition in implementation
   - Both in same file

4. **Naming Convention Test**
   - Correct: `Vector_push`
   - Incorrect: `vector_push`, `myfunc`

5. **Memory Management Test**
   - Matched create/destroy pairs
   - malloc without free
   - Balanced usage

6. **Design Pattern Test**
   - Factory pattern detection
   - Strategy pattern detection
   - Multiple patterns

---
## What needs to be done
- integration with the CLI.
- Test C for non OOP coding. (Although most is done here and is similar there might be a few features which can be checked and may be useful)



