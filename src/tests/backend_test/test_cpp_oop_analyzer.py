"""
Tests for C++ OOP Analyzer Module
"""

import pytest

from backend.analysis.cpp_oop_analyzer import (CLANG_AVAILABLE, CppOOPAnalysis,
                                               CppOOPAnalyzer,
                                               analyze_cpp_file,
                                               calculate_oop_score,
                                               calculate_solid_score,
                                               get_coding_style)

# Skip all tests if clang is not available
pytestmark = pytest.mark.skipif(not CLANG_AVAILABLE, reason="libclang not installed")


# Sample C++ code for testing
SIMPLE_CLASS = """
class SimpleClass {
public:
    int getValue() { return value; }
    void setValue(int v) { value = v; }
private:
    int value;
};
"""

INHERITANCE_CODE = """
class Animal {
public:
    virtual void speak() = 0;  // pure virtual
    virtual ~Animal() {}
};

class Dog : public Animal {
public:
    void speak() override { }
};

class Cat : public Animal {
public:
    void speak() override { }
};
"""

TEMPLATE_CODE = """
template<typename T>
class Container {
private:
    T data;
public:
    void set(T value) { data = value; }
    T get() { return data; }
};
"""

NAMESPACE_CODE = """
namespace MyNamespace {
    class MyClass {
    public:
        void doSomething() {}
    };
}
"""

DESIGN_PATTERN_CODE = """
class Singleton {
private:
    static Singleton* instance;
    Singleton() {}
public:
    static Singleton* getInstance() {
        if (!instance) {
            instance = new Singleton();
        }
        return instance;
    }
};

class ShapeFactory {
public:
    virtual Shape* createShape() = 0;
};
"""

STRUCT_CODE = """
struct Point {
    int x;
    int y;
};

struct Vector3D {
    float x, y, z;
    float length() { return 0.0f; }
};
"""

OPERATOR_OVERLOAD_CODE = """
class Complex {
private:
    double real, imag;
public:
    Complex operator+(const Complex& other) {
        Complex result;
        result.real = real + other.real;
        result.imag = imag + other.imag;
        return result;
    }
    
    Complex operator*(const Complex& other) {
        Complex result;
        return result;
    }
};
"""

ENCAPSULATION_CODE = """
class EncapsulatedClass {
private:
    int privateField1;
    int privateField2;
    void privateMethod() {}
    
protected:
    int protectedField;
    void protectedMethod() {}
    
public:
    int publicField;
    void publicMethod1() {}
    void publicMethod2() {}
};
"""


class TestCppOOPAnalyzer:
    """Test the CppOOPAnalyzer class."""

    def test_simple_class_detection(self):
        """Test detection of a simple class."""
        analysis = analyze_cpp_file(SIMPLE_CLASS)

        assert analysis.total_classes == 1
        assert analysis.struct_count == 0
        assert analysis.public_methods >= 2
        assert analysis.private_fields >= 1

    def test_inheritance_detection(self):
        """Test detection of inheritance and abstract classes."""
        analysis = analyze_cpp_file(INHERITANCE_CODE)

        assert analysis.total_classes >= 3
        assert analysis.classes_with_inheritance >= 2
        assert len(analysis.abstract_classes) >= 1
        assert analysis.virtual_methods >= 2
        assert analysis.inheritance_depth >= 1

    def test_namespace_detection(self):
        """Test detection of namespaces."""
        analysis = analyze_cpp_file(NAMESPACE_CODE)

        assert analysis.namespaces_used >= 1

    def test_design_pattern_detection(self):
        """Test detection of design patterns."""
        analysis = analyze_cpp_file(DESIGN_PATTERN_CODE)

        assert "Singleton" in analysis.design_patterns
        assert "Factory" in analysis.design_patterns

    def test_struct_detection(self):
        """Test detection of structs."""
        analysis = analyze_cpp_file(STRUCT_CODE)

        assert analysis.struct_count >= 2

    def test_operator_overload_detection(self):
        """Test detection of operator overloads."""
        analysis = analyze_cpp_file(OPERATOR_OVERLOAD_CODE)

        assert analysis.operator_overloads >= 2

    def test_encapsulation_metrics(self):
        """Test counting of access modifiers."""
        analysis = analyze_cpp_file(ENCAPSULATION_CODE)

        assert analysis.private_fields >= 2
        assert analysis.private_methods >= 1
        assert analysis.protected_fields >= 1
        assert analysis.protected_methods >= 1
        assert analysis.public_fields >= 1
        assert analysis.public_methods >= 2

    def test_empty_code(self):
        """Test analyzer with empty code."""
        analysis = analyze_cpp_file("")

        assert analysis.total_classes == 0
        assert analysis.struct_count == 0

    def test_procedural_code(self):
        """Test analyzer with procedural (non-OOP) code."""
        procedural_code = """
        int add(int a, int b) {
            return a + b;
        }
        
        void printHello() {
            // Just a function
        }
        """
        analysis = analyze_cpp_file(procedural_code)

        assert analysis.total_classes == 0
        assert analysis.struct_count == 0


class TestScoringFunctions:
    """Test the scoring functions."""

    def test_oop_score_no_oop(self):
        """Test OOP score for procedural code."""
        analysis = CppOOPAnalysis()
        score = calculate_oop_score(analysis)

        assert score == 0

    def test_oop_score_basic(self):
        """Test OOP score for basic OOP code."""
        analysis = CppOOPAnalysis()
        analysis.total_classes = 1
        analysis.private_fields = 1

        score = calculate_oop_score(analysis)
        assert score >= 2

    def test_oop_score_advanced(self):
        """Test OOP score for advanced OOP code."""
        analysis = CppOOPAnalysis()
        analysis.total_classes = 5
        analysis.abstract_classes = ["Base1", "Base2"]
        analysis.classes_with_inheritance = 3
        analysis.inheritance_depth = 2
        analysis.private_methods = 10
        analysis.virtual_methods = 5
        analysis.template_classes = 2
        analysis.design_patterns = ["Factory", "Singleton"]

        score = calculate_oop_score(analysis)
        assert score == 6

    def test_solid_score_range(self):
        """Test that SOLID score stays within valid range."""
        analysis = CppOOPAnalysis()
        analysis.total_classes = 10
        analysis.public_methods = 50
        analysis.classes_with_inheritance = 5
        analysis.virtual_methods = 10
        analysis.abstract_classes = ["A", "B", "C", "D"]
        analysis.design_patterns = ["Strategy", "Factory"]
        analysis.template_classes = 3

        score = calculate_solid_score(analysis)
        assert 0.0 <= score <= 5.0

    def test_solid_score_zero(self):
        """Test SOLID score for non-OOP code."""
        analysis = CppOOPAnalysis()
        score = calculate_solid_score(analysis)

        assert score == 0.0


class TestCodingStyle:
    """Test coding style classification."""

    def test_procedural_style(self):
        """Test procedural/functional style classification."""
        style = get_coding_style(0)
        assert style == "Procedural/Functional"

    def test_basic_oop_style(self):
        """Test basic OOP style classification."""
        style = get_coding_style(1)
        assert style == "Basic OOP"

        style = get_coding_style(2)
        assert style == "Basic OOP"

    def test_moderate_oop_style(self):
        """Test moderate OOP style classification."""
        style = get_coding_style(3)
        assert style == "Moderate OOP"

        style = get_coding_style(4)
        assert style == "Moderate OOP"

    def test_advanced_oop_style(self):
        """Test advanced OOP style classification."""
        style = get_coding_style(5)
        assert style == "Advanced OOP"

        style = get_coding_style(6)
        assert style == "Advanced OOP"


class TestDataClasses:
    """Test the data classes."""

    def test_cpp_oop_analysis_defaults(self):
        """Test CppOOPAnalysis default values."""
        analysis = CppOOPAnalysis()

        assert analysis.total_classes == 0
        assert analysis.struct_count == 0
        assert analysis.abstract_classes == []
        assert analysis.design_patterns == []
        assert analysis.inheritance_depth == 0

    def test_cpp_oop_analysis_to_dict(self):
        """Test CppOOPAnalysis to_dict conversion."""
        analysis = CppOOPAnalysis()
        analysis.total_classes = 5
        analysis.abstract_classes = ["Base"]

        result = analysis.to_dict()

        assert isinstance(result, dict)
        assert result["total_classes"] == 5
        assert result["abstract_classes"] == ["Base"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
