"""Create a demo ZIP file for testing complexity analysis."""
import os
import zipfile
from pathlib import Path

# Create demo directory
demo_dir = Path("demo_project")
demo_dir.mkdir(exist_ok=True)

# Create Python file with inefficient code (nested loops)
(demo_dir / "inefficient.py").write_text("""def find_duplicates(arr):
    # O(n²) - nested loops without optimization
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j]:
                return True
    return False

def search_in_list(data_list, target):
    # Inefficient: O(n) lookup in loop
    found_items = []
    for item in target:
        if item in data_list:  # Should use set
            found_items.append(item)
    return found_items
""")

# Create Python file with optimized code
(demo_dir / "optimized.py").write_text("""from functools import lru_cache
import bisect

@lru_cache(maxsize=128)
def fibonacci(n):
    # Memoization reduces complexity
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def deduplicate(items):
    # Using set for O(1) operations
    return list(set(items))

def find_in_sorted(sorted_list, target):
    # Binary search - O(log n)
    idx = bisect.bisect_left(sorted_list, target)
    if idx < len(sorted_list) and sorted_list[idx] == target:
        return idx
    return -1

def process_efficiently(data):
    # List comprehension - Pythonic and efficient
    return [x * 2 for x in data if x > 0]
""")

# Create package.json to mark as project
(demo_dir / "package.json").write_text('{"name": "demo-project", "version": "1.0.0"}')

# Create README
(demo_dir / "README.md").write_text("# Demo Project\\n\\nFor complexity analysis testing.")

# Create ZIP file
zip_path = Path("demo_analysis.zip")
with zipfile.ZipFile(zip_path, "w") as zf:
    for file in demo_dir.glob("*"):
        if file.is_file():
            zf.write(file, f"demo_project/{file.name}")

print(f"✓ Created {zip_path} with demo Python code")
print(f"  - inefficient.py: nested loops, inefficient lookups")
print(f"  - optimized.py: memoization, sets, binary search, comprehensions")
