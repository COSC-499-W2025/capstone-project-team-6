from pathlib import Path
from collections import deque
from typing import Iterable, Union

#Note traverse symlink is for folders that go into other folders that are not heirachally there in the topology so we will be ignoring these
def bfs_fs(
        root: Union[str, Path],
        *,
        traverse_symlink_dirs: bool = False,
    ) -> Iterable[Path]:


    root = Path(root)
    q = deque([root])

    #Track visited directories
    visited = set()

    #generate unique key for each directory
    def dir_key(p: Path):
        try:
            st = p.stat(follow_symlinks=False)
            return (st.st_dev, st.st_ino) # st.st_dev - device id, st.ino inode number (can remove later if not needed)
        except Exception:
            # Fallback: resolved path string 
            try:
                return ("path", str(p.resolve(strict=False)))
            except Exception:
                return ("path", str(p))

    #add root as visited 
    if root.is_dir():
        visited.add(dir_key(root))

    # while q not empty
    while q:
        current = q.popleft()
        yield current

        #Only descend into directories
        try:
            if not current.is_dir():
                continue

            #loop through child nodes
            for child in sorted(current.iterdir(), key=lambda p: p.name.lower()):
                # Always yield the child (files, dirs, and symlinks alike)
                yield child

                # Decide whether to traverse further
                try:
                    if child.is_dir():
                        #Will be skipping symlinks at this stage
                        if child.is_symlink() and not traverse_symlink_dirs:
                            continue
                        
                        # if the child is as folder check if it is already visited
                        k = dir_key(child)
                        if k in visited:
                            continue
                        #if not visited add it to visited
                        visited.add(k)
                        # add all child nodes to queue
                        q.append(child)
                except PermissionError:
                    # Can't stat or descend this child; just skip
                    continue
                except FileNotFoundError:
                    # It vanished between listing and stat; skip
                    continue

        except PermissionError:
            # Can't read this directory; skip
            continue
        except FileNotFoundError:
            # Directory vanished; skip
            continue



from pathlib import Path

def has_file_in_subitems(path: str | Path) -> bool:
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
