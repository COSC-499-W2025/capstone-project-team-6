// samplecpp.cpp - Simple C++ file for OOP analysis testing

#include <iostream>
#include <string>

// Abstract base "interface-like" shape
class Shape {
public:
    virtual double area() const = 0;  // pure virtual
    virtual void draw() const = 0;
    virtual ~Shape() {}
};

// Concrete class: Circle
class Circle : public Shape {
private:
    double radius;

public:
    Circle(double r) : radius(r) {}

    double area() const override {
        return 3.14159 * radius * radius;
    }

    void draw() const override {
        std::cout << "Circle\n";
    }
};

// Operator overload
Circle operator+(const Circle& a, const Circle& b) {
    return Circle(a.area() + b.area());
}

// Template class
template <typename T>
class Box {
public:
    T value;
    Box(T v) : value(v) {}
    T get() const { return value; }
};

// Singleton logger 
class Logger {
private:
    Logger() {}                          // private constructor
    static Logger* instance;             // static instance pointer

public:
    static Logger* getInstance() {
        if (!instance) {
            instance = new Logger();
        }
        return instance;
    }

    void log(const std::string& msg) {
        std::cout << "[LOG] " << msg << std::endl;
    }
};

Logger* Logger::instance = nullptr;

// Namespace example
namespace Geometry {
    struct Point {
    public:
        double x;
        double y;
    };
}
