def find_duplicates(arr):
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
