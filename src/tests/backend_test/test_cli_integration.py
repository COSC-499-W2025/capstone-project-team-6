#!/usr/bin/env python3
"""
Test script to verify CLI curation functionality works correctly.
"""

import tempfile
import subprocess
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_cli_help():
    """Test that CLI help shows curation commands."""
    result = subprocess.run([
        sys.executable, "-m", "src.backend.cli", "--help"
    ], capture_output=True, text=True)
    
    print("CLI Help Output:")
    print(result.stdout)
    print("STDERR:", result.stderr)
    
    # Check if curate command is listed
    if "curate" in result.stdout:
        print("✅ 'curate' command found in help")
    else:
        print("❌ 'curate' command not found in help")
    
    return "curate" in result.stdout

def test_curate_help():
    """Test curate command help."""
    result = subprocess.run([
        sys.executable, "-m", "src.backend.cli", "curate", "--help"
    ], capture_output=True, text=True)
    
    print("\nCurate Help Output:")
    print(result.stdout)
    print("STDERR:", result.stderr)
    
    # Check for subcommands
    success = all(cmd in result.stdout for cmd in ["chronology", "comparison", "showcase", "status"])
    if success:
        print("✅ All curation subcommands found")
    else:
        print("❌ Some curation subcommands missing")
    
    return success

def test_curate_status_no_login():
    """Test curate status without login."""
    result = subprocess.run([
        sys.executable, "-m", "src.backend.cli", "curate", "status"
    ], capture_output=True, text=True)
    
    print("\nCurate Status (No Login) Output:")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    # Should require login
    success = "Please login first" in result.stdout
    if success:
        print("✅ Properly requires login")
    else:
        print("❌ Should require login")
    
    return success

def main():
    print("Testing MDA CLI Curation Integration")
    print("=" * 50)
    
    tests = [
        test_cli_help,
        test_curate_help, 
        test_curate_status_no_login
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ {test.__name__} failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("✅ All CLI integration tests passed!")
        return 0
    else:
        print("❌ Some CLI integration tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())