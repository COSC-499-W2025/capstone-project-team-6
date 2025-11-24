from functools import lru_cache
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
