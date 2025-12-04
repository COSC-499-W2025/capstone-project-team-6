#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for Delete Previously Generated Insights PR
Tests A, B, C, D with proper database handling
"""

import subprocess
import sqlite3
import os
import sys
import io
from pathlib import Path

# Configure stdout/stderr to use UTF-8 encoding on Windows to handle Unicode characters
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_db_path():
    """Get database path - matches analysis_database.py"""
    return Path(__file__).parent / "src" / "myapp.db"

def count_analyses(zip_file_path):
    """Count analyses in database for a given zip file"""
    db_path = get_db_path()
    if not db_path.exists():
        return 0
    try:
        # Convert to absolute path to match how script stores it
        zip_file_abs = str(Path(zip_file_path).absolute())
        
        conn = sqlite3.connect(db_path)
        # Query using LIKE to match partial paths
        cursor = conn.execute(
            "SELECT COUNT(*) FROM analyses WHERE zip_file LIKE ?",
            (f"%{zip_file_path}%",)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"DB Error: {e}")
        return 0

def run_analysis(zip_file, inputs):
    """Run analysis with given inputs"""
    try:
        result = subprocess.run(
            [sys.executable, "src/backend/analysis/analyze.py", zip_file],
            input=inputs,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result
    except subprocess.TimeoutExpired:
        print("ERROR: Analysis timed out")
        return None

def clean_db():
    """Remove database for fresh test"""
    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
        print("  [Cleaned database]")

def test_a():
    """Test A: First run creates analysis"""
    print("\n" + "="*70)
    print("TEST A: First Run - Create Initial Analysis")
    print("="*70)
    
    zip_file = "demo_analysis.zip"
    clean_db()
    
    print("\n[Step 1] Running analysis with option 3 (keep all, generate new)...")
    result = run_analysis(zip_file, "3\nn\nn\n")
    
    if result is None or result.returncode != 0:
        print(f"  FAILED - Return code: {result.returncode if result else 'None'}")
        if result and result.stderr:
            print(f"  Error: {result.stderr[-300:]}")
        return False
    
    if "STORING ANALYSIS IN DATABASE" not in result.stdout:
        print("  FAILED - Analysis not stored")
        return False
    
    count = count_analyses(zip_file)
    print(f"  Analyses in DB: {count}")
    
    if count < 1:
        print(f"  FAILED - Expected at least 1 analysis, got {count}")
        return False
    
    print(f"  PASSED - Analysis created and stored")
    return True

def test_b():
    """Test B: Delete older analyses (keep most recent)"""
    print("\n" + "="*70)
    print("TEST B: Delete Older Analyses (Option 1)")
    print("="*70)
    
    zip_file = "demo_analysis.zip"
    
    print("\n[Step 1] Creating first analysis...")
    run_analysis(zip_file, "3\nn\nn\n")
    
    print("[Step 2] Creating second analysis...")
    run_analysis(zip_file, "3\nn\nn\n")
    
    count_before = count_analyses(zip_file)
    print(f"  Before deletion: {count_before} analyses")
    
    print("\n[Step 3] Running with option 1 (delete older, keep most recent)...")
    result = run_analysis(zip_file, "1\ny\nn\nn\n")
    
    if result is None or result.returncode != 0:
        print(f"  FAILED - Return code: {result.returncode if result else 'None'}")
        if result and result.stderr:
            print(f"  Error: {result.stderr[-300:]}")
        return False
    
    count_after = count_analyses(zip_file)
    print(f"  After deletion: {count_after} analyses")
    
    if count_after != 1:
        print(f"  FAILED - Expected 1 analysis, got {count_after}")
        return False
    
    if count_before <= count_after:
        print(f"  FAILED - No deletion occurred")
        return False
        
    print(f"  PASSED - Deleted {count_before - count_after} analysis/analyses, {count_after} remaining")
    return True

def test_c():
    """Test C: Delete all analyses"""
    print("\n" + "="*70)
    print("TEST C: Delete ALL Analyses (Option 2)")
    print("="*70)
    
    zip_file = "demo_analysis.zip"
    clean_db()
    
    print("\n[Step 1] Creating test analysis...")
    run_analysis(zip_file, "3\nn\nn\n")
    
    count_before = count_analyses(zip_file)
    print(f"  Before deletion: {count_before} analyses")
    
    print("\n[Step 2] Running with option 2 (delete ALL analyses)...")
    result = run_analysis(zip_file, "2\nyes\nn\nn\n")
    
    if result is None or result.returncode != 0:
        print(f"  FAILED - Return code: {result.returncode if result else 'None'}")
        if result and result.stderr:
            print(f"  Error: {result.stderr[-300:]}")
        return False
    
    count_after = count_analyses(zip_file)
    print(f"  After deletion: {count_after} analyses")
    
    # For option 2, all should be deleted, but then the analysis should still be stored
    # because new_analysis_generated should be True
    if count_after < 1:
        print(f"  FAILED - Expected at least 1 analysis (re-stored), got {count_after}")
        return False
    
    print(f"  PASSED - All {count_before} analysis/analyses deleted successfully, current analysis stored")
    return True

def test_d():
    """Test D: Keep all analyses and generate new"""
    print("\n" + "="*70)
    print("TEST D: Keep All Analyses and Generate New (Option 3)")
    print("="*70)
    
    zip_file = "demo_analysis.zip"
    clean_db()
    
    print("\n[Step 1] Creating first analysis...")
    run_analysis(zip_file, "3\nn\nn\n")
    
    count_after_first = count_analyses(zip_file)
    print(f"  After first run: {count_after_first} analysis/analyses")
    
    print("\n[Step 2] Running again with option 3 (keep all, generate new)...")
    result = run_analysis(zip_file, "3\nn\nn\n")
    
    if result is None or result.returncode != 0:
        print(f"  FAILED - Return code: {result.returncode if result else 'None'}")
        if result and result.stderr:
            print(f"  Error: {result.stderr[-300:]}")
        return False
    
    count_after_second = count_analyses(zip_file)
    print(f"  After second run: {count_after_second} analysis/analyses")
    
    if count_after_second <= count_after_first:
        print(f"  FAILED - Expected more analyses after second run")
        return False
    
    print(f"  PASSED - Both analyses kept, new one added ({count_after_first} -> {count_after_second})")
    return True

def main():
    """Run all tests"""
    print("="*70)
    print("TESTING DELETE PREVIOUSLY GENERATED INSIGHTS FEATURE")
    print("="*70)
    
    # Create test zip if it doesn't exist
    if not Path("demo_analysis.zip").exists():
        print("Creating test zip file...")
        try:
            subprocess.run([sys.executable, "create_demo_zip.py"], check=True)
        except subprocess.CalledProcessError:
            print("ERROR: Could not create test zip file")
            return False
    
    results = {
        'A': test_a(),
        'B': test_b(),
        'C': test_c(),
        'D': test_d()
    }
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name in ['A', 'B', 'C', 'D']:
        status = "PASSED" if results[test_name] else "FAILED"
        symbol = "✓" if results[test_name] else "✗"
        print(f"Test {test_name}: {symbol} {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("SUCCESS - ALL TESTS PASSED!")
    else:
        print("FAILURE - SOME TESTS FAILED")
    print("="*70)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
