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

## Known Limitations

1. **Git Analysis**: Full git history parsing requires extracting `.git` directory and running git commands. Current implementation detects git presence but doesn't fully parse history.

2. **Binary Files**: Binary dependencies and compiled artifacts are not analyzed.

3. **Dynamic Imports**: Runtime/dynamic imports in code are not detected.

4. **Large Files**: Files larger than 20MB are skipped to prevent memory issues.

## Future Enhancements

- [ ] Full git commit history parsing with `gitpython`
- [ ] Code complexity metrics (Analyzing O(n) complexity, etc.)
- [ ] Security vulnerability scanning for dependencies
- [ ] License detection and compliance checking
- [ ] Code duplication detection
- [ ] API endpoint extraction
- [ ] Database schema detection
- [ ] Test execution and actual coverage measurement

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
