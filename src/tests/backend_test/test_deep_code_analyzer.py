import pytest
from pathlib import Path
import sys
import zipfile
import tempfile
import os

# Add paths for imports
current_dir = Path(__file__).parent
backend_test_dir = current_dir
tests_dir = backend_test_dir.parent
src_dir = tests_dir.parent
backend_dir = src_dir / "backend"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from analysis.deep_code_analyzer import (
    analyze_python_file,
    OOPAnalysis,
    PythonOOPAnalyzer,
)


class TestOOPAnalysis:    
    def test_oop_analysis_creation(self):
        analysis = OOPAnalysis()
        assert analysis.total_classes == 0
        assert analysis.abstract_classes == []
        assert analysis.private_methods == 0
        assert analysis.protected_methods == 0
        assert analysis.public_methods == 0
        assert analysis.properties_count == 0
        assert analysis.operator_overloads == 0
        assert analysis.inheritance_depth == 0
        assert analysis.classes_with_inheritance == 0


class TestAnalyzePythonFile:
    """Test the analyze_python_file function."""
    
    def test_empty_file(self):
        """Test analyzing an empty Python file."""
        code = ""
        result = analyze_python_file(code)
        
        assert result.total_classes == 0
        assert result.private_methods == 0
        assert result.public_methods == 0
    
    def test_simple_class(self):
        """Test analyzing a simple class."""
        code = """
class MyClass:
    def method(self):
        pass
"""
        result = analyze_python_file(code)
        
        assert result.total_classes == 1
        assert result.public_methods == 1
        assert result.private_methods == 0
        assert result.inheritance_depth == 0
    
    
    def test_inheritance(self):
        """Test detecting inheritance."""
        code = """
class Plane:
    pass

class A380(Plane):
    pass

class B777(Plane):
    pass
"""
        result = analyze_python_file(code)
        
        assert result.total_classes == 3
        assert result.classes_with_inheritance == 2
        assert result.inheritance_depth == 1
    
    def test_multiple_inheritance_depth(self):
        """Test calculating inheritance depth."""
        code = """
class Plane:
    pass

class B737(Plane):
    pass

class B737Max(B737):
    pass

class Max8(B737Max):
    pass
"""
        result = analyze_python_file(code)
        
        assert result.total_classes == 4
        assert result.inheritance_depth == 3
   
    


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
