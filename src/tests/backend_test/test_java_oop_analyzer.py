from __future__ import annotations

import sys
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

try:
    from analysis.java_oop_analyzer import (JavaOOPAnalysis, JavaOOPAnalyzer,
                                            analyze_java_file,
                                            calculate_oop_score,
                                            calculate_solid_score,
                                            get_coding_style)

    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="javalang not installed")


@pytest.mark.skipif(not JAVALANG_AVAILABLE, reason="javalang not installed")
class TestJavaOOPAnalysis:
    """Test the JavaOOPAnalysis data class."""

    def test_oop_analysis_creation(self):
        """Test creating a JavaOOPAnalysis object."""
        analysis = JavaOOPAnalysis()
        assert analysis.total_classes == 0
        assert analysis.interface_count == 0
        assert analysis.abstract_classes == []
        assert analysis.private_methods == 0
        assert analysis.public_methods == 0
        assert analysis.inheritance_depth == 0
        assert analysis.annotations == {}
        assert analysis.design_patterns == []

    def test_oop_analysis_to_dict(self):
        """Test converting JavaOOPAnalysis to dictionary."""
        analysis = JavaOOPAnalysis(total_classes=5, interface_count=2, private_methods=10)
        result = analysis.to_dict()
        assert isinstance(result, dict)
        assert result["total_classes"] == 5
        assert result["interface_count"] == 2
        assert result["private_methods"] == 10


@pytest.mark.skipif(not JAVALANG_AVAILABLE, reason="javalang not installed")
class TestAnalyzeJavaFile:
    """Test the analyze_java_file function."""

    def test_empty_file(self):
        """Test analyzing an empty Java file."""
        code = ""
        result = analyze_java_file(code)

        assert result.total_classes == 0
        assert result.interface_count == 0
        assert result.private_methods == 0

    def test_simple_class(self):
        """Test analyzing a simple Java class."""
        code = """
public class MyClass {
    public void method() {
        System.out.println("Hello");
    }
}
"""
        result = analyze_java_file(code)

        assert result.total_classes == 1
        assert result.public_methods == 1
        assert result.private_methods == 0
        assert result.interface_count == 0

    def test_interface(self):
        """Test detecting an interface."""
        code = """
public interface MyInterface {
    void method();
}
"""
        result = analyze_java_file(code)

        assert result.interface_count == 1
        assert result.total_classes == 0

    def test_abstract_class(self):
        """Test detecting an abstract class."""
        code = """
public abstract class Animal {
    public abstract void makeSound();
    
    public void sleep() {
        System.out.println("Zzz");
    }
}
"""
        result = analyze_java_file(code)

        assert result.total_classes == 1
        assert "Animal" in result.abstract_classes
        assert result.public_methods == 2

    def test_inheritance(self):
        """Test detecting inheritance."""
        code = """
class Animal {
    void eat() {}
}

class Dog extends Animal {
    void bark() {}
}

class Cat extends Animal {
    void meow() {}
}
"""
        result = analyze_java_file(code)

        assert result.total_classes == 3
        assert result.classes_with_inheritance == 2
        assert result.inheritance_depth >= 1

    def test_interface_implementation(self):
        """Test detecting interface implementation."""
        code = """
interface Flyable {
    void fly();
}

class Bird implements Flyable {
    public void fly() {
        System.out.println("Flying");
    }
}
"""
        result = analyze_java_file(code)

        assert result.interface_count == 1
        assert result.total_classes == 1
        assert result.classes_with_inheritance == 1

    def test_access_modifiers(self):
        """Test counting methods by access modifier."""
        code = """
public class MyClass {
    private void privateMethod() {}
    protected void protectedMethod() {}
    public void publicMethod() {}
    void packageMethod() {}
}
"""
        result = analyze_java_file(code)

        assert result.private_methods == 1
        assert result.protected_methods == 1
        assert result.public_methods == 1
        assert result.package_methods == 1

    def test_fields(self):
        """Test counting fields by access modifier."""
        code = """
public class MyClass {
    private int x;
    protected String y;
    public double z;
}
"""
        result = analyze_java_file(code)

        assert result.private_fields == 1
        assert result.protected_fields == 1
        assert result.public_fields == 1

    def test_override_annotation(self):
        """Test detecting @Override annotations."""
        code = """
class Parent {
    public void method() {}
}

class Child extends Parent {
    @Override
    public void method() {}
}
"""
        result = analyze_java_file(code)

        assert result.override_count == 1
        assert "Override" in result.annotations


@pytest.mark.skipif(not JAVALANG_AVAILABLE, reason="javalang not installed")
class TestScoringFunctions:
    """Test OOP and SOLID scoring functions."""

    def test_calculate_oop_score_empty(self):
        """Test OOP score for empty analysis."""
        analysis = JavaOOPAnalysis()
        score = calculate_oop_score(analysis)
        assert score == 0

    def test_calculate_oop_score_full(self):
        """Test OOP score for comprehensive analysis."""
        analysis = JavaOOPAnalysis(
            total_classes=10,
            interface_count=5,
            abstract_classes=["Base"],
            inheritance_depth=3,
            private_methods=20,
            override_count=5,
            generic_classes=3,
        )
        score = calculate_oop_score(analysis)
        assert score == 6

    def test_calculate_solid_score(self):
        """Test SOLID score calculation."""
        analysis = JavaOOPAnalysis(
            total_classes=10,
            public_methods=50,
            private_methods=30,
            interface_count=5,
            classes_with_inheritance=8,
            override_count=10,
        )
        score = calculate_solid_score(analysis)
        assert 0.0 <= score <= 5.0

    def test_get_coding_style(self):
        """Test coding style determination."""
        assert get_coding_style(0) == "Procedural/Functional"
        assert get_coding_style(1) == "Basic OOP"
        assert get_coding_style(3) == "Moderate OOP"
        assert get_coding_style(6) == "Advanced OOP"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
