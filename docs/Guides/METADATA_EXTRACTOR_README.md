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
| `inheritance_depth` | Maximum inheritance chain depth | `3` 
| `private_methods` | Methods starting with `__` (not dunder) | `_internal_method` |
| `protected_methods` | Methods starting with single `_` | `_helper_method` |
| `public_methods` | Methods with no underscore prefix | `calculate()` |
| `properties_count` | Number of `@property` decorators used | `8` |
| `operator_overloads` | Dunder methods (except `__init__`, etc.) | `__str__`, `__add__` |

### OOP Score Calculation

The OOP score (0-6) is calculated based on presence of:
1. Uses Classes (total_classes > 0)
2.  Abstraction - Abstract classes detected
3. Inheritance - Inheritance depth > 0
4. Encapsulation - Private/protected methods > 0
5. Properties - Uses @property decorator
6. Polymorphism - Operator overloads present

### JSON Output Format 
#### Python Projects
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

## Phase 3: Deep Code Analysis - Java OOP Detection

### Overview

Extending Phase 3 to Java projects, the system now performs comprehensive Object-Oriented Programming analysis on Java source code using the `javalang` parser to detect OOP principles, design patterns, and SOLID principles.

### Installation for Java Analysis

```bash
pip install javalang
```

**Note:** Java analysis is optional. If `javalang` is not installed, the system will gracefully skip Java OOP analysis and continue with other analysis phases.

### Java OOP Features

#### 1. Core OOP Principles Detection

**Abstraction**
- Detects interfaces
- Identifies abstract classes
- Lists all abstract class names
- Tracks interface implementations

**Encapsulation**
- Counts private, protected, public, and package-private methods
- Tracks field access modifiers (private, protected, public)
- Detects getter/setter pairs
- Analyzes encapsulation patterns

**Inheritance**
- Calculates maximum inheritance depth
- Tracks `extends` relationships
- Monitors `implements` relationships
- Counts classes with inheritance

**Polymorphism**
- Detects `@Override` annotations
- Identifies method overloading
- Tracks polymorphic behavior

#### 2. Java-Specific Features

**Generics**
- Detects generic classes (e.g., `List<T>`, `Map<K,V>`)
- Tracks type parameter usage
- Analyzes generic methods

**Modern Java Features**
- Lambda expression counting
- Nested/inner class detection
- Anonymous class identification
- Enum detection and counting

**Annotations**
- Tracks all annotations used (Spring, JPA, Lombok, etc.)
- Counts annotation occurrences
- Common annotations: `@Override`, `@Autowired`, `@Service`, `@Repository`, `@Entity`, etc.

#### 3. Design Pattern Detection

The analyzer automatically detects common design patterns:

| Pattern | Detection Method |
|---------|------------------|
| **Singleton** | Private constructor + `getInstance()` method, or `@Singleton` annotation |
| **Factory** | Class name contains "Factory" |
| **Builder** | Nested `Builder` class or class name contains "Builder" |
| **Repository** | Class/interface name ends with "Repository" |
| **Service Layer** | Class name ends with "Service" |
| **MVC Controller** | Class name ends with "Controller" |
| **Observer** | Implements Observable/Observer interfaces |
| **Strategy** | Interface with "Strategy" in name |

#### 4. SOLID Principles Scoring

Calculates SOLID score (0-5.0) based on:
- **Single Responsibility**: Average methods per class (3-15 is ideal)
- **Open/Closed**: Use of interfaces and abstract classes
- **Liskov Substitution**: Inheritance with proper overrides
- **Interface Segregation**: Multiple interfaces (≥3 indicates good separation)
- **Dependency Inversion**: Interface usage with dependency injection patterns

### Usage

#### Analyze Individual Java Files

```bash
python src/backend/analysis/java_oop_analyzer.py <path_to_file.java>

# Examples
python src/backend/analysis/java_oop_analyzer.py src/main/java/User.java
python src/backend/analysis/java_oop_analyzer.py ~/MyClass.java
```

**Output:**
```
======================================================================
ANALYZING: User.java
======================================================================

JAVA OOP ANALYSIS RESULTS:

  Classes & Interfaces:
    Total classes: 1
    Interfaces: 0
    Enums: 0
    With inheritance: 0
    Max inheritance depth: 0

  Encapsulation:
    Methods:
      Private: 2
      Protected: 0
      Public: 5
      Package-private: 0
    Fields:
      Private: 3
      Protected: 0
      Public: 0
    Getter/Setter pairs: 3

  Polymorphism:
    Method overrides (@Override): 2
    Method overloads: 1

  Java-Specific Features:
    Generic classes: 0
    Nested classes: 0
    Lambda expressions: 0

  Annotations:
    @Override: 2

OOP Score: 4/6
SOLID Score: 3.5/5.0
Coding Style: Moderate OOP
```

#### Unified Analysis (Python + Java)

The comprehensive analysis script automatically analyzes both Python and Java projects:

```bash
python src/backend/analysis/analyze.py project.zip
```

**Output includes both Python and Java analysis:**
```
======================================================================
  PHASE 3: CODE ANALYSIS FOR OOP PRINCIPLES
======================================================================

**************************************************************
  PYTHON OOP ANALYSIS
**************************************************************

Project 1: backend
----------------------------------------------------------------------
OOP Metrics:
  Total Classes: 12
  Abstract Classes: BaseHandler, AbstractRepository
  ...

Coding Style: Advanced OOP

**************************************************************
  JAVA OOP ANALYSIS
**************************************************************

Project 1: microservice
----------------------------------------------------------------------
OOP Metrics:
  Total Classes: 25
  Interfaces: 8
  Abstract Classes: AbstractService, BaseController
  Enums: 3

Encapsulation:
  Total Methods: 140
    - Private: 45
    - Protected: 12
    - Public: 78
    - Package-private: 5
  Private Fields: 60
  Getter/Setter pairs: 30

Polymorphism:
  Method Overrides (@Override): 32
  Method Overloads: 15

Java-Specific Features:
  Generic Classes: 6
  Nested Classes: 4
  Lambda Expressions: 8

Annotations (top 5):
  @Override: 32
  @Autowired: 12
  @Service: 5
  @Entity: 4
  @Repository: 3

Design Patterns Detected:
  ✓ Singleton
  ✓ Factory
  ✓ Builder
  ✓ Repository
  ✓ Service Layer
  ✓ MVC Controller

OOP Score: 6/6
SOLID Score: 4.5/5.0
Principles Used:
  ✓ Uses Classes/Interfaces
  ✓ Abstraction
  ✓ Inheritance
  ✓ Encapsulation
  ✓ Polymorphism
  ✓ Advanced Features

Coding Style: Advanced OOP
```

### Java OOP Metrics Explained

| Metric | Description | Example |
|--------|-------------|---------|
| `total_classes` | Number of classes (excludes interfaces/enums) | `25` |
| `interface_count` | Number of interfaces defined | `8` |
| `abstract_classes` | List of abstract class names | `["BaseService", "AbstractController"]` |
| `enum_count` | Number of enum types | `3` |
| `private_methods` | Methods with `private` modifier | `45` |
| `protected_methods` | Methods with `protected` modifier | `12` |
| `public_methods` | Methods with `public` modifier | `78` |
| `package_methods` | Package-private methods (no modifier) | `5` |
| `private_fields` | Fields with `private` modifier | `60` |
| `classes_with_inheritance` | Classes that extend or implement | `18` |
| `inheritance_depth` | Maximum inheritance chain depth | `4` |
| `override_count` | Number of `@Override` annotations | `32` |
| `method_overloads` | Methods with same name, different params | `15` |
| `generic_classes` | Classes using generics | `6` |
| `nested_classes` | Inner/nested classes | `4` |
| `lambda_count` | Lambda expressions used | `8` |
| `getter_setter_pairs` | Estimated getter/setter pairs | `30` |
| `annotations` | Map of annotation names to counts | `{"Override": 32, "Autowired": 12}` |
| `design_patterns` | Detected design patterns | `["Singleton", "Factory", "Builder"]` |

### Java OOP Score Calculation

The OOP score (0-6) is calculated based on:
1. ✓ **Uses Classes/Interfaces** - Has classes or interfaces
2. ✓ **Abstraction** - Has interfaces or abstract classes
3. ✓ **Inheritance** - Inheritance depth > 0
4. ✓ **Encapsulation** - Uses private fields/methods
5. ✓ **Polymorphism** - Has @Override or method overloads
6. ✓ **Advanced Features** - Uses generics, annotations, or lambdas

### Java SOLID Score Calculation

The SOLID score (0-5.0) evaluates:
- **Single Responsibility** - Classes have focused responsibilities (3-15 methods ideal)
- **Open/Closed** - Uses interfaces and abstract classes for extension
- **Liskov Substitution** - Inheritance with proper method overrides
- **Interface Segregation** - Multiple interfaces indicate good separation
- **Dependency Inversion** - Interface usage with dependency injection

### Coding Style Classification

| OOP Score | Style | Description |
|-----------|-------|-------------|
| 0 | Procedural/Functional | No OOP constructs detected |
| 1-2 | Basic OOP | Simple class usage, limited principles |
| 3-4 | Moderate OOP | Multiple principles, some patterns |
| 5-6 | Advanced OOP | Comprehensive OOP with patterns |

### Supported Languages (Phase 3)

Currently, deep OOP analysis is supported for:

- **Python** - Full OOP analysis using AST
- **Java** - Full OOP analysis using javalang parser (requires `pip install javalang`)

### Technical Implementation

**Python Analysis:**

- Uses Python's built-in `ast` module
- No external dependencies required
- Parses code into Abstract Syntax Tree
- Visitor pattern for traversing nodes
- Handles complex inheritance chains

**Java Analysis:**

- Uses `javalang` library for Java AST parsing
- Optional dependency with graceful fallback
- Parses Java source into syntax tree
- Visitor pattern for node traversal
- Handles complex generic types and annotations

**Key Classes:**

- `OOPAnalysis` - Data class storing all OOP metrics
- `PythonOOPAnalyzer` - AST visitor for Python analysis
- `JavaOOPAnalysis` - Data class for Java OOP metrics
- `JavaOOPAnalyzer` - Java AST analyzer
- `analyze_python_file()` - Analyze single file
- `analyze_java_file()` - Analyze single Java file
- `analyze_project_deep()` - Analyze entire project
- `generate_comprehensive_report()` - Orchestrate all phases

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


### Issue: No projects detected
**Solution**: Ensure ZIP contains project indicator files (README, requirements.txt, package.json, etc.)

### Issue: Missing dependencies
**Solution**: Check that dependency files are in recognized formats and not corrupted

### Issue: Incorrect language detection
**Solution**: Verify file extensions match the `CODE_EXTENSIONS` in `FileClassifier`

### Issue: JSON serialization error
**Solution**: Ensure all custom data types are properly converted in `to_dict()` methods

### Issue: Java analysis not running
**Solution**: Install javalang library: `pip install javalang`. The system will gracefully skip Java analysis if not installed.

### Issue: Java parsing errors
**Solution**: Ensure Java files are valid Java source code. Complex generic types or newer Java syntax may require updated javalang version.

### Issue: Missing design patterns in Java
**Solution**: Pattern detection uses heuristics based on naming conventions and annotations. Ensure classes follow common naming patterns (e.g., `UserFactory`, `PersonBuilder`, `ProductRepository`).

## Contributing

When contributing new features:

1. Add comprehensive tests in `test_metadata_extractor.py`
2. Update this README with usage examples
3. Ensure JSON output remains serializable
4. Add example to `example_usage.py`
5. Document any new dependencies
