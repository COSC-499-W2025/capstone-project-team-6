# Time Complexity Analysis Feature

## Overview

The complexity analyzer examines Python code for patterns that indicate awareness (or lack thereof) of algorithmic optimization and time complexity considerations.

## What It Detects

### Good Practices (Increases Score) 
- **Efficient Data Structures**: Using sets/dicts for O(1) lookups instead of lists
- **Memoization**: Using `@lru_cache`, `@cache`, or custom memoization decorators
- **Binary Search**: Using `bisect` module for O(log n) searches
- **List Comprehensions**: Pythonic and efficient iteration patterns
- **Generator Expressions**: Memory-efficient lazy evaluation
- **Sorting with Key Functions**: Using `key=` parameter for optimized sorting

### Optimization Opportunities (Decreases Score) 
- **Nested Loops**: O(n²) or worse complexity patterns
- **Inefficient Membership Tests**: Using `in` operator on lists inside loops
- **List Lookups in Loops**: Repeated O(n) operations that could be O(1) with sets/dicts

## Scoring System

- **Base Score**: 50/100
- **Good Practices**: +5 points each (capped at +40)
- **Nested Loops**: -10 points each (capped at -30)
- **Inefficient Lookups**: -8 points each (capped at -25)
- **Inefficient Membership Tests**: -5 points each (capped at -15)

**Score Interpretation:**
- **75-100**: Strong optimization awareness
- **50-74**: Moderate awareness with some opportunities
- **0-49**: Limited awareness, review suggestions

## Usage

### Basic Analysis
```powershell
mda analyze project.zip --complexity
```

Shows summary with optimization score and counts.

### Detailed Analysis
```powershell
mda analyze project.zip --complexity --verbose
```

Shows file-by-file breakdown with line numbers and code snippets.

### Example Output

```
======================================================================
TIME COMPLEXITY ANALYSIS REPORT
======================================================================

Files Analyzed: 2
Optimization Awareness Score: 55.0/100
Assessment: Moderate awareness, some optimization opportunities exist

----------------------------------------------------------------------
SUMMARY
----------------------------------------------------------------------

Good Practices Found:
  ✓ Memoization: 1
  ✓ Set Operations: 1
  ✓ Binary Search: 1
  ✓ List Comprehension: 1

Optimization Opportunities:
  • Nested Loops: 1
  • Inefficient Membership Test: 1

----------------------------------------------------------------------
DETAILED FINDINGS (with --verbose)
----------------------------------------------------------------------

📄 demo_project/inefficient.py
  💡 Line 4: Nested loop detected (O(n²) complexity). Consider if this can
     be optimized with better data structures or algorithms.
     Code: for j in range(i + 1, len(arr)):
  💡 Line 13: Membership test inside loop on 'data_list'. Consider using a
     set or dict for O(1) lookups instead of O(n).
     Code: if item in data_list:

📄 demo_project/optimized.py
  ✓ Line 5: Memoization decorator (@lru_cache) used - reduces time
     complexity through caching.
     Code: def fibonacci(n):
  ✓ Line 13: Set created for efficient O(1) operations.
     Code: return list(set(items))
```

## Integration Points

### CLI Command
- `src/backend/cli.py`: Added `--complexity` and `--verbose` flags to `analyze` command
- Requires ZIP file (for now)
- Gated by login + consent flow

### Core Module
- `src/backend/analysis/complexity_analyzer.py`: AST-based pattern detection
- Modular design: `ComplexityAnalyzer` (visitor), `ComplexityReport` (aggregation), `format_report()` (display)

### File Classification Integration
- `src/backend/analysis/project_analyzer.py`: Added `analyze_python_complexity()` method to `FileClassifier`
- Automatically extracts Python files from ZIP and analyzes them

## Testing

Comprehensive test suite with 29 tests covering:
- Pattern detection (nested loops, data structures, decorators)
- Score calculation and clamping
- Report formatting
- Integration with FileClassifier
- Edge cases (syntax errors, Unicode, large files)

Run tests:
```powershell
python -m pytest src/tests/backend_test/test_complexity_analyzer.py -v
```

## Future Enhancements

This implementation focuses on Python projects. Future work can:
1. Add support for other languages (JavaScript, Java, C++, etc.)
2. Detect additional patterns (dynamic programming, graph algorithms)
3. Provide automated refactoring suggestions
4. Integrate with the vector database for semantic similarity analysis
5. Add machine learning-based complexity estimation
