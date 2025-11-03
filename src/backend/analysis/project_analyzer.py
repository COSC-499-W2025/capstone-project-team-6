"""
Phase 1: File Classification Module

This module classifies files within a project (inside a ZIP archive) into categories:
- Code files (by language)
- Documentation files
- Test files
- Configuration files
- Other files
"""

from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import zipfile


class FileClassifier:
    """Classifies files in a project for analysis."""
    
    # File extensions by category
    CODE_EXTENSIONS = {
        'python': {'.py', '.pyw'},
        'javascript': {'.js', '.mjs', '.cjs'},
        'typescript': {'.ts', '.tsx'},
        'java': {'.java'},
        'cpp': {'.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'},
        'go': {'.go'},
        'rust': {'.rs'},
        'ruby': {'.rb'},
        'php': {'.php'},
        'swift': {'.swift'},
        'kotlin': {'.kt', '.kts'},
        'scala': {'.scala'},
        'csharp': {'.cs'},
        'r': {'.r', '.R'},
        'shell': {'.sh', '.bash', '.zsh'},
        'html': {'.html', '.htm'},
        'css': {'.css', '.scss', '.sass', '.less'},
        'sql': {'.sql'},
    }
    
    DOC_EXTENSIONS = {'.md', '.rst', '.txt', '.adoc', '.tex', '.markdown'}
    
    CONFIG_EXTENSIONS = {
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.xml', '.env', '.properties', '.lock', '.config'
    }
    
    # Patterns to identify test files
    TEST_FILENAME_PATTERNS = [
        'test_', '_test.', 'test.', '.test.',
        'spec.', '.spec.', '_spec.',
        'tests.', '.tests.'
    ]
    
    TEST_DIR_PATTERNS = [
        '/test/', '/tests/', '/__tests__/',
        '/spec/', '/specs/',
        'test\\', 'tests\\', '__tests__\\',  # Windows paths
    ]
    
    # Directories to ignore- misc and not important files
    #THESE FILE WILL BE NEEDED FOR META DATA AND GIT ANALYSIS LATER BUT IGNORED FOR NOW
    IGNORE_DIRS = {
        'node_modules', '__pycache__', '.pytest_cache',
        'venv', '.venv', 'env', 'virtualenv',
        'target', 'build', 'dist', '.next',
        '.cache', 'coverage', '.git', '.svn',
        '.idea', '.vscode', 'bin', 'obj'
    }
    
    # File size limit (20MB)
    MAX_FILE_SIZE = 20 * 1024 * 1024

    #the below 4 functions are basic and self explanatory. 
    
    def __init__(self, zip_path: Path):
        """
        Initialize the classifier with a ZIP file.
        
        Args:
            zip_path: Path to the ZIP file containing projects
        """
        self.zip_path = zip_path
        self.zip_file = zipfile.ZipFile(zip_path, 'r')
    
    def should_ignore_path(self, file_path: str) -> bool:
        """
        Check if a file path should be ignored based on directory patterns.
        
        Args:
            file_path: Path to check (can use / or \\ separators)
            
        Returns:
            True if the path should be ignored, False otherwise
        """
        # Normalize path separators
        normalized_path = file_path.replace('\\', '/')
        path_parts = normalized_path.split('/')
        
        # Check if any part of the path matches ignore patterns
        for part in path_parts:
            if part in self.IGNORE_DIRS:
                return True
        
        return False
    
    def is_test_file(self, file_path: str, filename: str) -> bool:
        """
        Determine if a file is a test file based on filename and path patterns.
        
        Args:
            file_path: Full path of the file
            filename: Name of the file
            
        Returns:
            True if the file is identified as a test file
        """
        # Normalize path
        normalized_path = file_path.replace('\\', '/').lower()
        normalized_name = filename.lower()
        
        # Check filename patterns
        for pattern in self.TEST_FILENAME_PATTERNS:
            if pattern in normalized_name:
                return True
        
        # Check directory patterns
        for pattern in self.TEST_DIR_PATTERNS:
            if pattern in normalized_path:
                return True
        
        return False
    
    def get_language_from_extension(self, extension: str) -> str:
        """
        Get programming language from file extension.
        
        Args:
            extension: File extension (e.g., '.py')
            
        Returns:
            Language name or 'unknown'
        """
        extension = extension.lower()
        
        for language, extensions in self.CODE_EXTENSIONS.items():
            if extension in extensions:
                return language
        
        return 'unknown'
    
    def classify_file(self, file_path: str) -> Dict[str, any]:
        """
        Classify a single file.
        
        Args:
            file_path: Path to the file within the ZIP
            
        Returns:
            Dictionary with file metadata and classification
        """
        filename = file_path.split('/')[-1] if '/' in file_path else file_path
        extension = Path(filename).suffix.lower()
        
        # Get file info from ZIP
        try:
            file_info = self.zip_file.getinfo(file_path)
            file_size = file_info.file_size
        except KeyError:
            # File doesn't exist in ZIP
            return None
        
        # Skip if too large
        if file_size > self.MAX_FILE_SIZE:
            return {
                'path': file_path,
                'filename': filename,
                'type': 'skipped',
                'reason': 'file_too_large',
                'size': file_size
            }
        
        # Determine if it's a test file
        is_test = self.is_test_file(file_path, filename)
        
        # Classify by extension
        classification = {
            'path': file_path,
            'filename': filename,
            'extension': extension,
            'size': file_size,
            'is_test': is_test
        }
        
        # Check if it's code
        language = self.get_language_from_extension(extension)
        if language != 'unknown':
            classification['type'] = 'code'
            classification['language'] = language
            return classification
        
        # Check if it's documentation
        if extension in self.DOC_EXTENSIONS:
            classification['type'] = 'doc'
            # Special flag for README files
            if 'readme' in filename.lower():
                classification['is_readme'] = True
            return classification
        
        # Check if it's configuration
        if extension in self.CONFIG_EXTENSIONS:
            classification['type'] = 'config'
            return classification
        
        # Everything else
        classification['type'] = 'other'
        return classification
    
    def classify_project(self, project_root_path: str) -> Dict[str, any]:
        """
        Classify all files in a project within the ZIP file.
        
        Args:
            project_root_path: Root path of the project within the ZIP
                            (e.g., 'my-project/' or 'folder/my-project/')
        
        Returns:
            Dictionary with classified files organized by type
        """
        # Normalize the project root path
        project_root = project_root_path.rstrip('/')
        
        # Result structure
        result = {
            'project_path': project_root,
            'files': {
                'code': defaultdict(list),
                'docs': [],
                'tests': [],
                'configs': [],
                'other': [],
                'skipped': []
            },
            'stats': {
                'total_files': 0,
                'total_size': 0,
            }
        }
        
        # Get all files in the ZIP
        all_files = self.zip_file.namelist()
        
        # Classify each file that belongs to this project
        for file_path in all_files:
            normalized_path = file_path.replace('\\', '/')
            
            # Check if file is under project root
            if project_root:
                if not normalized_path.startswith(project_root + '/'):
                    continue
            
            # Skip directories (they end with /)
            if normalized_path.endswith('/'):
                continue
            
            # Skip ignored paths
            if self.should_ignore_path(normalized_path):
                continue
            
            #classify the file
            classification = self.classify_file(normalized_path)
            
            if classification is None:
                continue
            
            result['stats']['total_files'] += 1
            result['stats']['total_size'] += classification['size']
            
            file_type = classification['type']
            
            if file_type == 'code':
                language = classification['language']

                if classification['is_test']:
                    result['files']['tests'].append(classification)

                else:
                    result['files']['code'][language].append(classification)

            elif file_type == 'doc':
                result['files']['docs'].append(classification)

            elif file_type == 'config':
                result['files']['configs'].append(classification)

            elif file_type == 'skipped':
                result['files']['skipped'].append(classification)
            else:
                result['files']['other'].append(classification)
        
        # Convert defaultdict to regular dict
        result['files']['code'] = dict(result['files']['code'])
        
        return result
    
    #basic methods when dealing with zip files

    def close(self):
        """Close the ZIP file."""
        if hasattr(self, 'zip_file'):
            self.zip_file.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Ensure ZIP file is closed."""
        self.close()

