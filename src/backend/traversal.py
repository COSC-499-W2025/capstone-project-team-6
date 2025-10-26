from pathlib import Path
from collections import deque
from typing import Iterable, Union

#Note traverse symlink is for folders that go into other folders that are not heirachally there in the topology so we will be ignoring these
def Folder_traversal(root_path: Union[str, Path]):
    """
    Performs a breadth-first traversal starting at root_path.
    checks if it contains files using dfs_for_file().
    returns a dictionary where each directory path maps to its 'project' boolean.
    """
    from .session import get_session
    session = get_session()
    if not session["logged_in"]:
        raise PermissionError("Please login first")
        
    root = Path(root_path)

    if not root.exists():
        raise FileNotFoundError(f"The path {root} does not exist.")
    if not root.is_dir():
        raise ValueError(f"The path {root} is not a directory.")

    #replace with this with a class instead of a dictionary
    #dictionary to store directory info
    node_info = {root: {"project": False}}

    #Queue for BFS
    queue = deque([root])

    while queue:
        current_dir = queue.popleft()

        parent= current_dir.parent
        # if parent node is a project remove from queue
        if parent in node_info and node_info[parent]["project"]:
            # 2 checks since root wont have a parent and node_info will be false
            continue


        #dfs
        has_file = dfs_for_file(current_dir)
        node_info[current_dir]["project"] = has_file

        if has_file:
            #no need to check for the rest of the sub items
            continue

        try:
            for item in current_dir.iterdir():
                #if dir (extra check) add to queue with project false
                if item.is_dir():
                    #initialize child node with default project=False
                    node_info[item] = {"project": False}
                    queue.append(item)
        except (PermissionError, FileNotFoundError):
            continue  # Skip folders that can't be read

    return node_info




def dfs_for_file(path: Union[str, Path]) -> bool:
    """
    Does a Depth first search of depth =1
    returns true if there is file in the sub items of the directory

    """
    p = Path(path)

    #proceed if it’s a directory
    if not p.is_dir():
        raise ValueError(f"The path {p} is not a directory.")

    #Iterate over immediate children
    try:
        for item in p.iterdir():
            if item.is_file():
                return True  # found at least one file
    except PermissionError:
        # Can't access folder contents; treat as empty
        return False
    except FileNotFoundError:
        # Folder may have been deleted during traversal
        return False

    # If we finish the loop without finding files
    return False


# informal testing 
if __name__ == "__main__":
    current_dir = Path(__file__).parent      # directory where this file is
    path = current_dir / "Test-traversal"  
    results = Folder_traversal(path)
    for directory, info in results.items():
        print(f"{directory} → project: {info['project']}")