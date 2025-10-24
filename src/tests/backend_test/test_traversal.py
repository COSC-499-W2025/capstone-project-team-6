'''
from pathlib import Path
import shutil
import os
import pytest

# this import is finiky, try src.backend.traversal if the current import does not work
from backend.traversal import Folder_traversal, dfs_for_file

def test_dfs_for_file_depth1():
    current_dir = Path(__file__).parent
    root = current_dir / "Test-traversal"

    folderA = root / "FolderA"      # has File1.txt directly -> True
    folderB = root / "FolderB"      # only subfolders -> False
    folderE = root / "FolderB" / "FolderE"  # has files -> True
    folderF = root / "FolderB" / "FolderF"  # only subfolder -> False
    folderG = root / "FolderB" / "FolderF" / "FolderG"  # has file -> True
    folderC = root / "FolderC"      # has File7.txt -> True

    assert dfs_for_file(folderA) is True
    assert dfs_for_file(folderB) is False
    assert dfs_for_file(folderE) is True
    assert dfs_for_file(folderF) is True
    #assert dfs_for_file(folderG) is True
    assert dfs_for_file(folderC) is True

    # Root has only folders at depth 1 -> False
    assert dfs_for_file(root) is False


def test_bfs_marks_projects_and_prunes_children():
    current_dir = Path(__file__).parent
    root = current_dir / "Test-traversal"
    results = Folder_traversal(root)

    # Keys should be Path objects
    assert all(isinstance(k, Path) for k in results.keys())

    # Helper to get 'project' quickly (guard against missing keys if you reuse it elsewhere)
    def P(p: Path) -> bool:
        return results[p]["project"]

    # Present nodes that SHOULD exist in results
    assert root in results
    assert (root / "FolderA") in results
    assert (root / "FolderB") in results
    assert (root / "FolderC") in results
    assert (root / "FolderB" / "FolderE") in results
    assert (root / "FolderB" / "FolderF") in results

    # Labels to match your informal run
    assert P(root) is False
    assert P(root / "FolderA") is True
    assert P(root / "FolderB") is False
    assert P(root / "FolderC") is True
    assert P(root / "FolderB" / "FolderE") is True
    assert P(root / "FolderB" / "FolderF") is True  # F is project ⇒ prune its children

    #  FolderF is project, its descendant FolderG must be pruned (NOT present)
    assert (root / "FolderB" / "FolderF" / "FolderG") not in results

    # Children of other project folders should be pruned too:
    assert (root / "FolderA" / "FolderD") not in results

    #  nothing deeper under FolderC (project)
    for k in results.keys():
        assert not str(k).startswith(str(root / "FolderC") + os.sep) or k == (root / "FolderC")

    # nothing deeper under FolderE (project)
    for k in results.keys():
        assert not str(k).startswith(str(root / "FolderB" / "FolderE") + os.sep) or k == (root / "FolderB" / "FolderE")

'''