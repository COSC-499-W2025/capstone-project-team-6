# ZIP File Traversal Feature

## Overview

The traversal system now supports analyzing ZIP archives **without extraction**. You can traverse and detect projects inside ZIP files just like regular directories.

## What Changed

### New Components

1. **File System Abstraction Layer**
   - `FileSystemInterface`: Abstract base class for file system operations
   - `RegularFileSystem`: Handles regular directories
   - `ZipFileSystem`: Handles ZIP archives
   - `FileSystemEntry` protocol: Unified interface for files/directories

2. **New Function: `Folder_traversal_fs()`**
   - Automatically detects whether input is a directory or ZIP file
   - Uses appropriate file system interface
   - Returns same structure as original `Folder_traversal()`

3. **Updated `DirectoryNode`**
   - Now supports both `Path` objects and string paths
   - Added `path_str` property for consistent string representation
   - Added `name` property that works for both types

### Libraries Used

- **`zipfile`** (Python standard library)
  - No external dependencies required
  - Built-in support for reading ZIP files
  - Memory efficient for large archives

## Usage

### Basic Usage

```python
from backend.traversal import Folder_traversal_fs

# For ZIP files
results = Folder_traversal_fs("path/to/archive.zip")

# For regular directories (also supported)
results = Folder_traversal_fs("path/to/directory")

# Process results
for path, node in results.items():
    if node.is_project:
        print(f"Project: {path}")
        print(f"  Score: {node.score}")
        print(f"  Indicators: {node.indicators_found}")
```

### How It Works

1. **Detection**: Function checks if path is a `.zip` file
2. **Interface Creation**:
   - ZIP → creates `ZipFileSystem`
   - Directory → creates `RegularFileSystem`
3. **Traversal**: Same BFS algorithm works with both
4. **Scoring**: Project indicators detected in both ZIP and regular files
5. **Results**: Dictionary mapping paths to `DirectoryNode` objects

### Differences from Original Function

| Feature | `Folder_traversal()` | `Folder_traversal_fs()` |
|---------|---------------------|------------------------|
| Regular directories | ✅ | ✅ |
| ZIP files | ❌ | ✅ |
| Return type | `Dict[Path, DirectoryNode]` | `Dict[str, DirectoryNode]` |
| Path in DirectoryNode | `Path` object | `Path` or `str` |

**Note**: For ZIP files, paths are strings (e.g., `"projectA"`, `"src/main.py"`). For regular directories, paths are full path strings.

## Examples

### Example 1: Simple Project ZIP

ZIP contains:
```
project.zip
├── package.json
├── README.md
├── src/
│   └── index.js
└── tests/
    └── test.js
```

Result:
```python
results = Folder_traversal_fs("project.zip")
# {
#     '': DirectoryNode(is_project=True, score=110.0)
# }
```

### Example 2: Monorepo ZIP

ZIP contains:
```
monorepo.zip
├── README.md
├── projectA/
│   ├── package.json
│   └── src/
├── projectB/
│   ├── pyproject.toml
│   └── src/
└── projectC/
    ├── Cargo.toml
    └── src/
```

Result:
```python
results = Folder_traversal_fs("monorepo.zip")
# {
#     '': DirectoryNode(is_project=False, subproject_count=3),
#     'projectA': DirectoryNode(is_project=True, score=80.0),
#     'projectB': DirectoryNode(is_project=True, score=80.0),
#     'projectC': DirectoryNode(is_project=True, score=80.0)
# }
```

## Testing

### Test ZIP Files

Run the test ZIP creator:
```bash
python3 src/tests/backend_test/create_test_zip.py
```

This creates 5 test ZIP files:
- `simple_project.zip` - Single project
- `nested_projects.zip` - Multiple projects (monorepo)
- `python_project.zip` - Python-specific project
- `non_project.zip` - Random files (not a project)
- `mixed_structure.zip` - Mix of projects and non-projects

### Running Tests

```bash
# Run pytest tests (if pytest is installed)
pytest src/tests/backend_test/test_zip_traversal.py -v

# Or run the module directly to see demo
python3 src/backend/traversal.py
```

## Implementation Details

### ZIP File System

The `ZipFileSystem` class:
1. Opens ZIP file using `zipfile.ZipFile`
2. Builds directory map on initialization
3. Provides `iterdir()` to iterate entries
4. Normalizes paths (removes trailing slashes)
5. Automatically closes ZIP file when done

### Path Handling

- **ZIP paths**: Stored as strings without trailing slashes
  - Root: `''` (empty string)
  - Directories: `'src'`, `'projectA'`
  - Nested: `'src/components'`

- **Regular paths**: Stored as full absolute path strings
  - Example: `'/Users/name/project/src'`

### Performance

- ZIP files are **not extracted** to disk
- Directory structure is built once on initialization
- Subsequent operations read from in-memory map
- ZIP file is closed automatically after traversal

## Bug Fixes Applied

1. **Root self-counting**: Fixed root directory counting itself as a subproject
2. **Path normalization**: Ensured trailing slashes are removed from ZIP paths for consistent parent/child matching

## Backward Compatibility

✅ Original `Folder_traversal()` function **unchanged**
✅ All existing code continues to work
✅ `Folder_traversal_fs()` works with both directories and ZIP files
✅ Same project detection logic and scoring

## Future Enhancements

Potential improvements:
- Support for nested ZIP files (ZIP within ZIP)
- Support for other archive formats (.tar, .tar.gz, .7z)
- Streaming for very large ZIP files
- Caching for repeated traversals

## Summary

The ZIP traversal feature provides:
- ✅ Traverse ZIP files without extraction
- ✅ Same project detection as regular directories
- ✅ No external dependencies (uses standard library)
- ✅ Backward compatible with existing code
- ✅ Memory efficient
- ✅ Easy to use API
