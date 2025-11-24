# Metadata Extractor - Phase 2 Analysis (Non-LLM) Documentation

## Overview

The **Metadata Extractor** builds on top of the `FileClassifier` (Phase 1) to extract comprehensive project metadata **without using LLMs**. It analyzes categorized files to produce detailed JSON reports about projects, including technology stacks, dependencies, contributor information, and project health indicators.

## Features

### 1. Multi-Project Detection
- Automatically detects multiple projects within a single ZIP archive
- Identifies projects based on dependency files, READMEs, and source structure
- Handles nested directory structures intelligently

### 2. Technology Stack Analysis
- **Language Detection**: Identifies all programming languages used and their file counts
- **Framework Detection**: Recognizes popular frameworks (Django, Flask, React, Vue, Spring, etc.)
- **Dependency Extraction**: Parses dependency files for various package managers:
  - Python: `requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py`
  - JavaScript/Node: `package.json`, `yarn.lock`
  - Java: `pom.xml`, `build.gradle`
  - Go: `go.mod`
  - Ruby: `Gemfile`
  - PHP: `composer.json`

### 3. Project Structure Insights
- File categorization counts (code, tests, docs, configs)
- Directory depth analysis
- Largest file identification
- Test coverage estimation (none/low/medium/high)

### 4. DevOps & Best Practices Detection
- CI/CD configuration detection (GitHub Actions, GitLab CI, Travis, Jenkins, etc.)
- Docker/containerization detection
- README presence
- Git repository detection

### 5. Git Analysis (IF AVAILABLE)
- Contributor identification
- Commit counting
- File modification tracking
- Contribution timeline analysis

### 6. JSON Report Generation
- Comprehensive, structured output
- Summary statistics across all projects
- Individual project breakdowns
- Fully serializable for storage or API responses

## Installation

Ensure you have the base requirements installed:

```bash
pip install -r src/backend/requirements.txt
```

## Usage

### Basic Usage - Command Line

```bash
# Analyze a ZIP file and generate a report
python -m src.backend.analysis.run_metadata_extractor <path_to_zip> [output_path]

# Example
python -m src.backend.analysis.run_metadata_extractor my_project.zip output.json
```

### Programmatic Usage

```python
from pathlib import Path
from src.backend.analysis.metadata_extractor import MetadataExtractor

# Basic usage
with MetadataExtractor(Path("project.zip")) as extractor:
    report = extractor.generate_report(Path("output.json"))
    print(f"Analyzed {len(report['projects'])} projects")

# Access specific project metadata
with MetadataExtractor(Path("project.zip")) as extractor:
    projects = extractor.detect_projects()
    
    for project_path in projects:
        metadata = extractor.extract_project_metadata(project_path)
        print(f"Project: {metadata.project_name}")
        print(f"Primary Language: {metadata.primary_language}")
        print(f"Test Coverage: {metadata.test_coverage_estimate}")
```

### Advanced Examples

See `src/backend/analysis/example_usage.py` for detailed examples including:
- Detailed analysis of each project
- Comparing multiple projects
- Custom health scoring
- Dependency analysis

Run the examples:
```bash
python src/backend/analysis/example_usage.py
```

## Output Format

The generated JSON report has the following structure:

```json
{
  "analysis_metadata": {
    "zip_file": "path/to/project.zip",
    "analysis_timestamp": "2025-11-03T12:34:56",
    "total_projects": 2
  },
  "projects": [
    {
      "project_name": "my_project",
      "project_path": "",
      "primary_language": "python",
      "languages": {
        "python": 15,
        "javascript": 3
      },
      "total_files": 25,
      "total_size": 524288,
      "code_files": 18,
      "test_files": 5,
      "doc_files": 2,
      "config_files": 3,
      "frameworks": ["Django", "React"],
      "dependencies": {
        "python": ["django", "requests", "pytest"],
        "javascript": ["react", "react-dom"]
      },
      "has_tests": true,
      "has_readme": true,
      "has_ci_cd": true,
      "has_docker": true,
      "test_coverage_estimate": "medium",
      "is_git_repo": true,
      "contributors": [
        {
          "name": "John Doe",
          "email": "john@example.com",
          "commits": 45,
          "files_touched": 12
        }
      ],
      "total_commits": 120,
      "directory_depth": 5,
      "largest_file": {
        "path": "src/main.py",
        "size": 50000,
        "size_mb": 0.05
      }
    }
  ],
  "summary": {
    "total_files": 25,
    "total_size_bytes": 524288,
    "total_size_mb": 0.5,
    "languages_used": ["python", "javascript"],
    "frameworks_used": ["Django", "React"]
  }
}
```

## Integration with Phase 1 (FileClassifier)

The Metadata Extractor seamlessly integrates with the Phase 1 `FileClassifier`:

```python
# Phase 1: File Classification
from src.backend.analysis.project_analyzer import FileClassifier

with FileClassifier(zip_path) as classifier:
    classification = classifier.classify_project("")
    # Returns: categorized files (code, docs, tests, configs)

# Phase 2: Metadata Extraction
from src.backend.analysis.metadata_extractor import MetadataExtractor

with MetadataExtractor(zip_path) as extractor:
    # Uses FileClassifier internally
    metadata = extractor.extract_project_metadata("")
    # Returns: comprehensive metadata about the project
```
### Phase 3: Deep Code Analysis - C++ OOP Detection

#### Overview
The C++ OOP Analyzer extends Phase 3 by providing deep object-oriented analysis for C++ code using **Clang’s Abstract Syntax Tree (AST)**.

It extracts detailed metrics related to:
- Class structure  
- Inheritance  
- Encapsulation  
- Polymorphism  
- Core C++ language features  

### Features

#### 1. OOP Principles Detection

**Abstraction**
- Detects abstract classes by identifying pure virtual methods  
- Lists the names of abstract classes  

**Encapsulation**
- Counts private, protected, and public methods  
- Counts private, protected, and public fields  

**Inheritance**
- Detects classes that inherit from others  
- Extracts base class names  
- Computes the maximum inheritance depth  

**Polymorphism**
- Detects virtual and pure virtual methods  
- Detects overridden methods (heuristic-based)  
- Identifies operator overloads  

#### 2. C++-Specific Features
- Template class detection  
- Namespace usage  
- Free functions inside namespaces  
- Operator overloading  
- Static members (if present)  

#### 3. Design Pattern Heuristics
The analyzer includes basic heuristic detection for common patterns such as:
- Singleton  
- Factory  
- Strategy  
- Observer  

### Installation

#### System Requirement: Clang / LLVM

The analyzer requires LLVM’s `libclang` library to be installed on the system.

**macOS**
    brew install llvm
    export LIBCLANG_PATH="$(brew --prefix llvm)/lib"

**Windows**
1. Install LLVM from:  
   https://github.com/llvm/llvm-project/releases  
2. Add the LLVM `bin` directory to the system `PATH`  
3. Set:

    set LIBCLANG_PATH=C:\Program Files\LLVM\bin

### Usage

#### Analyze a Single C++ File

From the repository root:

    python src/backend/analysis/cpp_oop_analyzer.py <path_to_cpp_file>

**Example:**

    python src/backend/analysis/cpp_oop_analyzer.py src/backend/analysis/samplecpp.cpp

Output includes

C++ OOP ANALYSIS RESULTS:

  Total classes: 3
  Structs: 1
  Abstract classes: Shape
  Classes with inheritance: 1
  Inheritance depth: 1

  Encapsulation:
    Private methods: 0
    Protected methods: 0
    Public methods: 12
    Private fields: 2
    Public fields: 4

  Polymorphism:
    Virtual methods: 8
    Override methods: 2
    Operator overloads: 0

  C++ Features:
    Template classes: 0
    Namespaces used: 1

  Design Patterns:
    ✓ Singleton

SCORES:
  OOP Score: 6/6
  SOLID Score: 3.0/5.0
  Coding Style: Advanced OOP

## Known Limitations

1. Override detection relies on heuristics
2. Template detection is limited to templated type declarations
4. Requires system installation of Clang/LLVM

## Phase 3: Deep Code Analysis - Python OOP Detection

### Overview

Building on Phase 1 (File Classification) and Phase 2 (Metadata Extraction), **Phase 3** introduces deep code analysis using Python's Abstract Syntax Tree (AST) to detect Object-Oriented Programming principles and design patterns.

### Features

#### 1. OOP Principles Detection

**Abstraction**
- Detects abstract base classes using `ABC` (Abstract Base Class)
- Identifies Protocol classes for structural subtyping
- Lists all abstract class names

**Encapsulation**
- Counts private methods (`__method_name`)
- Counts protected methods (`_method_name`)
- Counts public methods (no underscore prefix)
- Identifies property usage (`@property` decorators)

**Inheritance**
- Calculates maximum inheritance depth across all classes
- Counts classes that use inheritance
- Builds inheritance hierarchy relationships

**Polymorphism**
- Detects operator overloading (dunder methods like `__str__`, `__add__`, etc.)
- Identifies method overrides (future enhancement)

#### 2. Automated Coding Style Classification

Based on detected OOP metrics, projects are classified as:
- **Procedural/Functional** - No classes detected
- **Basic OOP** - Uses classes but limited OOP principles (score 1-2/6)
- **Moderate OOP** - Uses multiple OOP principles (score 3-4/6)
- **Advanced OOP** - Comprehensive OOP implementation (score 5-6/6)

### Usage

#### Unified Analysis Script (Recommended)

Analyze an entire project ZIP with all three phases:

```bash
python src/backend/analysis/analyze.py <zip_file_path>

# Example
python src/backend/analysis/analyze.py my_project.zip
```

**Output includes:**
```
======================================================================
  PHASE 1 & 2: FILE CLASSIFICATION + METADATA
======================================================================

Total Files: 45
Total Projects: 1
Languages: python, javascript

----------------------------------------------------------------------
Project 1: app
----------------------------------------------------------------------

Basic Info:
  Primary Language: python
  Path: (root)

File Breakdown:
  Total: 45
  Code: 32
  Tests: 8
  Docs: 3
  Config: 2

OOP Metrics:
  Total Classes: 15
  Abstract Classes: Class1, Class2
  Classes with Inheritance: 12
  Max Inheritance Depth: 3

Encapsulation:
  Total Methods: 87
    - Private (__name): 8
    - Protected (_name): 24
    - Public: 55
  Properties (@property): 12

Polymorphism:
  Operator Overloads: 5

OOP Score: 6/6
Principles Used:
  Uses Classes
  Abstraction (ABC/Protocol)
  Inheritance
  Encapsulation
  Properties
  Polymorphism

Coding Style: Advanced OOP
```

#### Analyze Individual Python Files

For quick analysis of a single Python file:

```bash
python src/backend/analysis/deep_code_analyzer.py <path_to_file.py>

# Examples
python src/backend/analysis/deep_code_analyzer.py src/backend/cli.py
python src/backend/analysis/deep_code_analyzer.py ~/Downloads/mycode.py
```

**Output:**
```
======================================================================
ANALYZING: cli.py
======================================================================

OOP ANALYSIS RESULTS:

  Classes:
    Total classes: 3
    Abstract classes: BaseHandler
    With inheritance: 2
    Max inheritance depth: 1

  Encapsulation:
    Private methods (__name): 2
    Protected methods (_name): 5
    Public methods: 12
    Properties (@property): 3

  Polymorphism:
    Operator overloads: 1

QUICK ASSESSMENT:
    - Uses OOP (found 3 classes)
    - Uses abstraction
    - Practices encapsulation
    - Uses inheritance
```




### OOP Metrics Explained

| Metric | Description | Example |
|--------|-------------|---------|
| `total_classes` | Total number of classes in the project | `15` |
| `abstract_classes` | List of abstract class names | `["Animal", "Vehicle"]` |
| `classes_with_inheritance` | Number of classes that inherit from others | `12` |
| `inheritance_depth` | Maximum inheritance chain depth | `3` (GrandChild → Child → Parent) |
| `private_methods` | Methods starting with `__` (not dunder) | `__internal_method` |
| `protected_methods` | Methods starting with single `_` | `_helper_method` |
| `public_methods` | Methods with no underscore prefix | `calculate()` |
| `properties_count` | Number of `@property` decorators used | `8` |
| `operator_overloads` | Dunder methods (except `__init__`, etc.) | `__str__`, `__add__` |

### OOP Score Calculation

The OOP score (0-6) is calculated based on presence of:
1. ✓ Uses Classes (total_classes > 0)
2. ✓ Abstraction - Abstract classes detected
3. ✓ Inheritance - Inheritance depth > 0
4. ✓ Encapsulation - Private/protected methods > 0
5. ✓ Properties - Uses @property decorator
6. ✓ Polymorphism - Operator overloads present

### JSON Output Format (Phase 3 Addition)

When Phase 3 is included, each project in the report gets an `oop_analysis` field:

```json
{
  "projects": [
    {
      "project_name": "my_project",
      "primary_language": "python",
      "oop_analysis": {
        "total_classes": 15,
        "abstract_classes": ["BaseHandler", "AbstractRepository"],
        "private_methods": 8,
        "protected_methods": 24,
        "public_methods": 55,
        "properties_count": 12,
        "method_overrides": 0,
        "operator_overloads": 5,
        "inheritance_depth": 3,
        "classes_with_inheritance": 12
      }
    }
  ]
}
```

### Supported Languages (Phase 3)

Currently, deep OOP analysis is supported for:
- **Python** - Full OOP analysis using AST
- **Java** - WIP

### Technical Implementation

**AST-Based Analysis:**
- Uses Python's built-in `ast` module
- No external dependencies required
- Parses code into Abstract Syntax Tree
- Visitor pattern for traversing nodes
- Handles complex inheritance chains

**Key Classes:**
- `OOPAnalysis` - Data class storing all OOP metrics
- `PythonOOPAnalyzer` - AST visitor for Python analysis
- `analyze_python_file()` - Analyze single file
- `analyze_project_deep()` - Analyze entire project
- `generate_comprehensive_report()` - Orchestrate all phases

### Example: Detecting Design Patterns

While not yet fully implemented, the OOP analysis lays groundwork for design pattern detection:

```python
# Future capability
from src.backend.analysis.pattern_detector import detect_patterns

patterns = detect_patterns(report)
# Returns: ["Singleton", "Factory", "Observer", "Strategy"]
```

## Known Limitations

1. **Git Analysis**: Full git history parsing requires extracting `.git` directory and running git commands. Current implementation detects git presence but doesn't fully parse history.

2. **Binary Files**: Binary dependencies and compiled artifacts are not analyzed.

3. **Dynamic Imports**: Runtime/dynamic imports in code are not detected.

4. **Large Files**: Files larger than 20MB are skipped to prevent memory issues.

5. **OOP Analysis Language Support**: Currently only Python is supported for deep OOP analysis. Other languages show metadata only.

6. **Method Overrides**: Detection of method overrides across inheritance hierarchy is not yet implemented.

7. **Design Patterns**: Automated design pattern detection is planned but not yet implemented.

## Future Enhancements

### Phase 1 & 2 Enhancements
- [ ] Full git commit history parsing with `gitpython`
- [ ] Security vulnerability scanning for dependencies
- [ ] License detection and compliance checking
- [ ] Code duplication detection
- [ ] API endpoint extraction
- [ ] Database schema detection
- [ ] Test execution and actual coverage measurement

### Phase 3 (OOP Analysis) Enhancements
- [ ] **Multi-Language Support**: Extend OOP analysis to Java, C++, TypeScript, C#
- [ ] **Design Pattern Detection**: Identify common patterns (Singleton, Factory, Observer, Strategy, etc.)
- [ ] **Code Complexity Metrics**: Cyclomatic complexity, cognitive complexity
- [ ] **Method Override Detection**: Track method overrides in inheritance hierarchies
- [ ] **SOLID Principles Analysis**: Evaluate adherence to SOLID principles
- [ ] **Code Smell Detection**: Identify anti-patterns and code smells
- [ ] **Dependency Injection Analysis**: Detect DI patterns and frameworks
- [ ] **Composition vs Inheritance Ratio**: Analyze design approach preferences
- [ ] **Interface Segregation Metrics**: Evaluate interface design quality
- [ ] **Maintainability Index**: Calculate overall code maintainability score

## Troubleshooting

### Issue: No projects detected
**Solution**: Ensure ZIP contains project indicator files (README, requirements.txt, package.json, etc.)

### Issue: Missing dependencies
**Solution**: Check that dependency files are in recognized formats and not corrupted

### Issue: Incorrect language detection
**Solution**: Verify file extensions match the `CODE_EXTENSIONS` in `FileClassifier`

### Issue: JSON serialization error
**Solution**: Ensure all custom data types are properly converted in `to_dict()` methods

## Contributing

When contributing new features:

1. Add comprehensive tests in `test_metadata_extractor.py`
2. Update this README with usage examples
3. Ensure JSON output remains serializable
4. Add example to `example_usage.py`
5. Document any new dependencies
