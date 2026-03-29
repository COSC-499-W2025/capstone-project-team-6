#!/usr/bin/env python3
"""
Simple validation script for Enhanced REST API components.
Run with: python test_components.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_component_imports():
    """Test that all enhanced components can be imported."""
    print("=== TESTING COMPONENT IMPORTS ===")
    try:
        from backend.api_server import app
        from backend.task_manager import get_task_manager, TaskType, TaskStatus
        from backend.analysis_database import init_db, get_all_analyses_for_user
        print(f"[OK] All enhanced components imported successfully")
        print(f"[OK] API Server: {app.title} v{app.version}")
        return True
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_database_integration():
    """Test database integration functions."""
    print("\n=== TESTING DATABASE INTEGRATION ===")
    try:
        from backend.analysis_database import init_db, get_all_analyses_for_user, get_analysis_by_uuid, delete_analysis
        
        init_db()
        print("[OK] Database initialized")
        
        analyses = get_all_analyses_for_user('testuser')
        print(f"[OK] get_all_analyses_for_user returned: {len(analyses)} analyses")
        
        result = get_analysis_by_uuid('fake-uuid', 'testuser')
        print(f"[OK] get_analysis_by_uuid (non-existent): {result}")
        
        deleted = delete_analysis('fake-uuid', 'testuser')
        print(f"[OK] delete_analysis (non-existent): {deleted}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return False

def test_task_manager():
    """Test task manager components."""
    print("\n=== TESTING TASK MANAGER ===")
    try:
        from backend.task_manager import get_task_manager, TaskType, TaskStatus, FileManager
        import tempfile
        
        tm = get_task_manager()
        print(f"[OK] Task Manager initialized: {type(tm).__name__}")
        
        fm = FileManager()
        print(f"[OK] File Manager initialized: {type(fm).__name__}")
        
        # Test file hashing
        test_file = Path(tempfile.mktemp(suffix='.txt'))
        test_file.write_text('test content')
        file_hash = fm.calculate_file_hash(test_file)
        print(f"[OK] File hash calculated: {file_hash[:16]}...")
        test_file.unlink()
        
        print("[OK] Task Manager components working")
        return True
    except Exception as e:
        print(f"[ERROR] Task Manager error: {e}")
        return False

def main():
    """Run all component tests."""
    print("Enhanced API Component Validation")
    print("=" * 40)
    
    tests = [
        test_component_imports,
        test_database_integration, 
        test_task_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"TEST RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("[SUCCESS] All component tests passed! ✅")
        print("\nReady to start API server with:")
        print("cd src")
        print("python -m uvicorn backend.api_server:app --reload --host 127.0.0.1 --port 8000")
        return True
    else:
        print(f"[FAILED] {total - passed} tests failed ❌")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)