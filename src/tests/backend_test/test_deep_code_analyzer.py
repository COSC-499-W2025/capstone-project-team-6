import os
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

# Add paths for imports
current_dir = Path(__file__).parent
backend_test_dir = current_dir
tests_dir = backend_test_dir.parent
src_dir = tests_dir.parent
backend_dir = src_dir / "backend"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

from src.backend.analysis.deep_code_analyzer import (OOPAnalysis,
                                                     analyze_python_file)


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


def test_abstract_class_detection():
    code = """
from abc import ABC, abstractmethod
class Aircraft(ABC):
    @abstractmethod
    def fly(self):
        pass
class A380(Aircraft):
    def fly(self):
        return "A380"
"""
    result = analyze_python_file(code)
    assert result.total_classes == 2
    assert len(result.abstract_classes) == 1
    assert result.inheritance_depth == 2
    assert result.oop_score >= 1


def test_operator_overloads():
    code = """
class Plane:
    def __add__(self, other): return self
    def __str__(self): return "plane"
"""
    result = analyze_python_file(code)
    assert result.operator_overloads == 2
    assert result.oop_score >= 1


def test_properties_count():
    code = """
class Aircraft:
    @property
    def model(self): return "A320"
"""
    result = analyze_python_file(code)
    assert result.properties_count == 1
    assert result.oop_score >= 1


def test_design_pattern_detection():
    code = """
class PlaneFactory: pass
class SingletonPlane: pass
class ObserverPlane: pass
class StrategyPlane: pass
"""
    result = analyze_python_file(code)
    patterns = set(result.design_patterns)
    assert "Factory" in patterns
    assert "Singleton" in patterns
    assert "Observer" in patterns
    assert "Strategy" in patterns


def test_project_size_labels():
    from src.backend.analysis.deep_code_analyzer import \
        calculate_python_oop_score

    analysis = OOPAnalysis(total_classes=2)
    analysis.oop_score = calculate_python_oop_score(analysis)
    assert analysis.total_classes < 3
    analysis = OOPAnalysis(total_classes=5)
    analysis.oop_score = calculate_python_oop_score(analysis)
    assert 3 <= analysis.total_classes < 10
    analysis = OOPAnalysis(total_classes=15)
    analysis.oop_score = calculate_python_oop_score(analysis)
    assert analysis.total_classes >= 10


def test_solid_score_ranges():
    from src.backend.analysis.deep_code_analyzer import \
        calculate_python_solid_score

    analysis = OOPAnalysis(total_classes=5, private_methods=2, public_methods=3, abstract_classes=["A"], properties_count=1)
    score = calculate_python_solid_score(analysis)
    assert 0 <= score <= 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
