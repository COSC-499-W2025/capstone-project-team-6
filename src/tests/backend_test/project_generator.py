"""
Test Project Generator for C Analyzer Tests

This module creates test C projects on-demand for testing the C analyzer.
No need to download or manually create test files - they're generated automatically!

Usage:
    from test_project_generator import generate_all_test_projects
    
    test_dir = generate_all_test_projects()
    # Returns Path to directory containing all test projects and ZIPs
"""

import tempfile
import zipfile
from pathlib import Path
from typing import Dict


class CTestProjectGenerator:
    """Generates test C projects for analyzer testing."""

    @staticmethod
    def create_project_1_minimal(base_dir: Path) -> Path:
        """
        Create Project 1: Minimal - Pure Procedural C

        Purpose: Test low OOP score, basic detection
        Expected OOP Score: 0-1/6
        """
        project_dir = base_dir / "1_minimal"
        project_dir.mkdir(parents=True, exist_ok=True)

        # main.c
        (project_dir / "main.c").write_text(
            """/*
 * Minimal Procedural C Code
 * 
 * Purpose: Test pure procedural C with no OOP patterns
 * Expected OOP Score: 0-1/6
 */

#include <stdio.h>

// Simple helper function - no OOP pattern
int add(int a, int b) {
    return a + b;
}

// Another simple function
int multiply(int a, int b) {
    return a * b;
}

// Main function
int main() {
    int x = 5;
    int y = 10;
    
    printf("Sum: %d\\n", add(x, y));
    printf("Product: %d\\n", multiply(x, y));
    
    return 0;
}
"""
        )

        return project_dir

    @staticmethod
    def create_project_2_basic_struct(base_dir: Path) -> Path:
        """
        Create Project 2: Basic Struct - Simple OOP Elements

        Purpose: Test basic struct detection and simple OOP elements
        Expected OOP Score: 2-3/6
        """
        project_dir = base_dir / "2_basic_struct"
        project_dir.mkdir(parents=True, exist_ok=True)

        # point.h
        (project_dir / "point.h").write_text(
            """/*
 * Basic Struct Project - Header
 */

#ifndef POINT_H
#define POINT_H

// Simple struct - visible structure (not opaque)
struct Point {
    int x;
    int y;
};

// Function declarations
struct Point Point_create(int x, int y);
void Point_print(struct Point p);
int Point_distance_squared(struct Point p1, struct Point p2);

#endif
"""
        )

        # point.c
        (project_dir / "point.c").write_text(
            """/*
 * Basic Struct Project - Implementation
 */

#include "point.h"
#include <stdio.h>

// Constructor-style function (OOP naming: Type_create)
struct Point Point_create(int x, int y) {
    struct Point p;
    p.x = x;
    p.y = y;
    return p;
}

// Method-style function (OOP naming: Type_action)
void Point_print(struct Point p) {
    printf("Point(%d, %d)\\n", p.x, p.y);
}

// Another method-style function
int Point_distance_squared(struct Point p1, struct Point p2) {
    int dx = p2.x - p1.x;
    int dy = p2.y - p1.y;
    return dx * dx + dy * dy;
}

// Static helper (encapsulation - internal only)
static int square(int x) {
    return x * x;
}
"""
        )

        return project_dir

    @staticmethod
    def create_project_3_vector(base_dir: Path) -> Path:
        """
        Create Project 3: Vector - OOP-Style Library

        Purpose: Test comprehensive OOP-style patterns
        Expected OOP Score: 4-5/6
        """
        project_dir = base_dir / "3_vector"
        project_dir.mkdir(parents=True, exist_ok=True)

        # vector.h
        (project_dir / "vector.h").write_text(
            """/*
 * Vector Library - Header (Opaque Pointer Pattern)
 */

#ifndef VECTOR_H
#define VECTOR_H

// Opaque pointer - implementation hidden
struct Vector;

// Error codes for error handling testing
enum VectorError {
    VECTOR_SUCCESS = 0,
    VECTOR_ERROR_NULL = -1,
    VECTOR_ERROR_OUT_OF_MEMORY = -2,
    VECTOR_ERROR_INDEX_OUT_OF_BOUNDS = -3
};

// Constructor (Factory pattern)
struct Vector* Vector_create(int initial_capacity);

// Destructor (RAII-style)
void Vector_destroy(struct Vector* vec);

// Methods
int Vector_push(struct Vector* vec, int value);
int Vector_get(struct Vector* vec, int index, int* out_value);
int Vector_size(struct Vector* vec);

#endif
"""
        )

        # vector.c
        (project_dir / "vector.c").write_text(
            """/*
 * Vector Library - Implementation
 */

#include "vector.h"
#include <stdlib.h>

// Actual struct definition (hidden from header - opaque pointer)
struct Vector {
    int* data;
    int size;
    int capacity;
};

// Constructor (malloc usage, Factory pattern)
struct Vector* Vector_create(int initial_capacity) {
    if (initial_capacity <= 0) {
        return NULL;
    }
    
    struct Vector* vec = malloc(sizeof(struct Vector));
    if (!vec) {
        return NULL;
    }
    
    vec->data = malloc(sizeof(int) * initial_capacity);
    if (!vec->data) {
        free(vec);
        return NULL;
    }
    
    vec->size = 0;
    vec->capacity = initial_capacity;
    
    return vec;
}

// Destructor (free usage, RAII-style)
void Vector_destroy(struct Vector* vec) {
    if (vec) {
        free(vec->data);
        free(vec);
    }
}

// Method with error handling
int Vector_push(struct Vector* vec, int value) {
    if (!vec) {
        return VECTOR_ERROR_NULL;
    }
    
    // Check if resize needed
    if (vec->size >= vec->capacity) {
        int new_capacity = vec->capacity * 2;
        int* new_data = realloc(vec->data, sizeof(int) * new_capacity);
        
        if (!new_data) {
            return VECTOR_ERROR_OUT_OF_MEMORY;
        }
        
        vec->data = new_data;
        vec->capacity = new_capacity;
    }
    
    vec->data[vec->size++] = value;
    return VECTOR_SUCCESS;
}

// Method with error handling
int Vector_get(struct Vector* vec, int index, int* out_value) {
    if (!vec || !out_value) {
        return VECTOR_ERROR_NULL;
    }
    
    if (index < 0 || index >= vec->size) {
        return VECTOR_ERROR_INDEX_OUT_OF_BOUNDS;
    }
    
    *out_value = vec->data[index];
    return VECTOR_SUCCESS;
}

// Getter method
int Vector_size(struct Vector* vec) {
    return vec ? vec->size : 0;
}

// Private helper function (static = encapsulation)
static int vector_grow(struct Vector* vec) {
    int new_capacity = vec->capacity * 2;
    int* new_data = realloc(vec->data, sizeof(int) * new_capacity);
    
    if (!new_data) {
        return 0;
    }
    
    vec->data = new_data;
    vec->capacity = new_capacity;
    return 1;
}
"""
        )

        return project_dir

    @staticmethod
    def create_project_4_polymorphism(base_dir: Path) -> Path:
        """
        Create Project 4: Polymorphism - Function Pointers (VTable)

        Purpose: Test VTable detection and Strategy pattern
        Expected OOP Score: 5/6
        """
        project_dir = base_dir / "4_polymorphism"
        project_dir.mkdir(parents=True, exist_ok=True)

        # animal.h
        (project_dir / "animal.h").write_text(
            """/*
 * Polymorphism via Function Pointers
 */

#ifndef ANIMAL_H
#define ANIMAL_H

// Forward declaration
struct Animal;

// VTable-style struct with function pointers (Strategy pattern)
struct AnimalVTable {
    void (*speak)(struct Animal* self);
    void (*move)(struct Animal* self);
    void (*eat)(struct Animal* self);
};

// Base "class" with function pointers
struct Animal {
    char* name;
    struct AnimalVTable* vtable;  // VTable pointer
};

// Constructor
struct Animal* Animal_create(char* name, struct AnimalVTable* vtable);

// Destructor
void Animal_destroy(struct Animal* animal);

// Polymorphic method calls
void Animal_speak(struct Animal* animal);
void Animal_move(struct Animal* animal);
void Animal_eat(struct Animal* animal);

// Concrete implementations
struct AnimalVTable* Dog_get_vtable(void);
struct AnimalVTable* Cat_get_vtable(void);

#endif
"""
        )

        # dog.c
        (project_dir / "dog.c").write_text(
            """/*
 * Dog Implementation - Polymorphism Example
 */

#include "animal.h"
#include <stdio.h>
#include <stdlib.h>

// Dog-specific implementations
static void dog_speak(struct Animal* self) {
    printf("%s says: Woof!\\n", self->name);
}

static void dog_move(struct Animal* self) {
    printf("%s runs on four legs\\n", self->name);
}

static void dog_eat(struct Animal* self) {
    printf("%s eats dog food\\n", self->name);
}

// Dog's VTable (singleton pattern)
static struct AnimalVTable dog_vtable = {
    .speak = dog_speak,
    .move = dog_move,
    .eat = dog_eat
};

// Factory function for dog VTable
struct AnimalVTable* Dog_get_vtable(void) {
    return &dog_vtable;
}

// Base implementation
struct Animal* Animal_create(char* name, struct AnimalVTable* vtable) {
    struct Animal* animal = malloc(sizeof(struct Animal));
    if (animal) {
        animal->name = name;
        animal->vtable = vtable;
    }
    return animal;
}

void Animal_destroy(struct Animal* animal) {
    if (animal) {
        free(animal);
    }
}

// Polymorphic calls
void Animal_speak(struct Animal* animal) {
    if (animal && animal->vtable && animal->vtable->speak) {
        animal->vtable->speak(animal);
    }
}

void Animal_move(struct Animal* animal) {
    if (animal && animal->vtable && animal->vtable->move) {
        animal->vtable->move(animal);
    }
}

void Animal_eat(struct Animal* animal) {
    if (animal && animal->vtable && animal->vtable->eat) {
        animal->vtable->eat(animal);
    }
}
"""
        )

        # cat.c
        (project_dir / "cat.c").write_text(
            """/*
 * Cat Implementation - Polymorphism Example
 */

#include "animal.h"
#include <stdio.h>

// Cat-specific implementations
static void cat_speak(struct Animal* self) {
    printf("%s says: Meow!\\n", self->name);
}

static void cat_move(struct Animal* self) {
    printf("%s walks gracefully\\n", self->name);
}

static void cat_eat(struct Animal* self) {
    printf("%s eats cat food\\n", self->name);
}

// Cat's VTable
static struct AnimalVTable cat_vtable = {
    .speak = cat_speak,
    .move = cat_move,
    .eat = cat_eat
};

// Factory function for cat VTable
struct AnimalVTable* Cat_get_vtable(void) {
    return &cat_vtable;
}
"""
        )

        return project_dir

    @staticmethod
    def create_project_5_complete(base_dir: Path) -> Path:
        """
        Create Project 5: Complete - Full-Featured Library

        Purpose: Test all OOP-style patterns together
        Expected OOP Score: 6/6
        """
        project_dir = base_dir / "5_complete"
        project_dir.mkdir(parents=True, exist_ok=True)

        # list.h
        (project_dir / "list.h").write_text(
            """/*
 * Complete Library - Linked List
 */

#ifndef LIST_H
#define LIST_H

// Opaque pointer
struct List;

// Callback for observer pattern
typedef void (*ListCallback)(int value, void* user_data);

// Error codes
enum ListStatus {
    LIST_SUCCESS = 0,
    LIST_ERROR_NULL = -1,
    LIST_ERROR_EMPTY = -2,
    LIST_ERROR_OUT_OF_MEMORY = -3
};

// Constructor/Destructor
struct List* List_create(void);
void List_destroy(struct List* list);

// Methods
int List_append(struct List* list, int value);
int List_size(struct List* list);

// Observer pattern
void List_on_change(struct List* list, ListCallback callback, void* user_data);

#endif
"""
        )

        # list.c
        (project_dir / "list.c").write_text(
            """/*
 * Complete Library - Implementation
 */

#include "list.h"
#include <stdlib.h>

struct Node {
    int value;
    struct Node* next;
};

struct List {
    struct Node* head;
    int size;
    ListCallback on_change_callback;
    void* callback_user_data;
};

struct List* List_create(void) {
    struct List* list = malloc(sizeof(struct List));
    if (list) {
        list->head = NULL;
        list->size = 0;
        list->on_change_callback = NULL;
        list->callback_user_data = NULL;
    }
    return list;
}

void List_destroy(struct List* list) {
    if (!list) return;
    
    struct Node* current = list->head;
    while (current) {
        struct Node* next = current->next;
        free(current);
        current = next;
    }
    free(list);
}

static void list_notify_change(struct List* list, int value) {
    if (list && list->on_change_callback) {
        list->on_change_callback(value, list->callback_user_data);
    }
}

int List_append(struct List* list, int value) {
    if (!list) return LIST_ERROR_NULL;
    
    struct Node* node = malloc(sizeof(struct Node));
    if (!node) return LIST_ERROR_OUT_OF_MEMORY;
    
    node->value = value;
    node->next = NULL;
    
    if (!list->head) {
        list->head = node;
    } else {
        struct Node* current = list->head;
        while (current->next) {
            current = current->next;
        }
        current->next = node;
    }
    
    list->size++;
    list_notify_change(list, value);
    
    return LIST_SUCCESS;
}

int List_size(struct List* list) {
    return list ? list->size : 0;
}

void List_on_change(struct List* list, ListCallback callback, void* user_data) {
    if (list) {
        list->on_change_callback = callback;
        list->callback_user_data = user_data;
    }
}
"""
        )

        # iterator.h
        (project_dir / "iterator.h").write_text(
            """/*
 * Iterator Pattern
 */

#ifndef ITERATOR_H
#define ITERATOR_H

struct Iterator;

struct Iterator* Iterator_create(struct List* list);
void Iterator_destroy(struct Iterator* iter);
int Iterator_has_next(struct Iterator* iter);

#endif
"""
        )

        # iterator.c
        (project_dir / "iterator.c").write_text(
            """/*
 * Iterator Implementation
 */

#include "iterator.h"
#include <stdlib.h>

struct Iterator {
    void* current;
};

struct Iterator* Iterator_create(struct List* list) {
    struct Iterator* iter = malloc(sizeof(struct Iterator));
    if (iter) {
        iter->current = NULL;
    }
    return iter;
}

void Iterator_destroy(struct Iterator* iter) {
    free(iter);
}

int Iterator_has_next(struct Iterator* iter) {
    return iter && iter->current != NULL;
}
"""
        )

        # util.c
        (project_dir / "util.c").write_text(
            """/*
 * Utility Functions
 */

#include <stdlib.h>

int util_max(int a, int b) {
    return (a > b) ? a : b;
}

static int util_min(int a, int b) {
    return (a < b) ? a : b;
}

static void util_swap(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
"""
        )

        return project_dir

    @staticmethod
    def create_zip_file(project_dir: Path, output_dir: Path) -> Path:
        """Create a ZIP file from a project directory."""
        zip_path = output_dir / f"{project_dir.name}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_dir.parent)
                    zipf.write(file_path, arcname)

        return zip_path


def generate_all_test_projects(base_dir: Path = None) -> Dict[str, Path]:
    """
    Generate all test projects and return paths.

    Args:
        base_dir: Base directory for test projects. If None, uses temp directory.

    Returns:
        Dictionary with keys:
        - 'base_dir': Base directory containing all projects
        - 'projects': Dict mapping project name to project directory
        - 'zips': Dict mapping project name to ZIP file path
    """
    if base_dir is None:
        base_dir = Path(tempfile.mkdtemp(prefix="c_analyzer_tests_"))
    else:
        base_dir = Path(base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)

    generator = CTestProjectGenerator()

    # Generate all projects
    projects = {
        "1_minimal": generator.create_project_1_minimal(base_dir),
        "2_basic_struct": generator.create_project_2_basic_struct(base_dir),
        "3_vector": generator.create_project_3_vector(base_dir),
        "4_polymorphism": generator.create_project_4_polymorphism(base_dir),
        "5_complete": generator.create_project_5_complete(base_dir),
    }

    # Create ZIP files
    zips = {}
    for name, project_dir in projects.items():
        zips[name] = generator.create_zip_file(project_dir, base_dir)

    return {"base_dir": base_dir, "projects": projects, "zips": zips}


if __name__ == "__main__":
    """Demo: Generate all test projects"""
    print("Generating test projects...")
    result = generate_all_test_projects()

    print(f"\n✓ Generated in: {result['base_dir']}")
    print("\nProjects:")
    for name, path in result["projects"].items():
        print(f"  - {name}: {path}")

    print("\nZIP files:")
    for name, path in result["zips"].items():
        print(f"  - {name}.zip: {path}")

    print("\n✓ All test projects generated successfully!")
