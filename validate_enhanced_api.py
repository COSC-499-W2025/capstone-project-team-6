#!/usr/bin/env python3
"""
Validation tests for enhanced REST API functionality.
Tests database integration, task management, and file handling.
"""

import sys
import tempfile
import uuid
import json
from pathlib import Path
import zipfile

sys.path.insert(0, 'src')

from backend.analysis_database import (
    init_db, get_all_analyses_for_user, get_analysis_by_uuid, 
    delete_analysis, record_analysis
)
from backend.task_manager import (
    get_task_manager, TaskType, TaskStatus, FileManager
)
from backend.api_server import app

def create_test_zip() -> Path:
    """Create a test ZIP file."""
    temp_dir = Path(tempfile.mkdtemp())
    zip_path = temp_dir / "test_project.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("main.py", """
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")
        zf.writestr("README.md", "# Test Project\nThis is a test project.")
    
    return zip_path

def test_database_integration():
    """Test database functions work correctly."""
    print("--- Testing Database Integration ---")
    
    # Initialize database
    init_db()
    print("✅ Database initialized")
    
    # Test get_all_analyses_for_user (should work even if empty)
    analyses = get_all_analyses_for_user("testuser")
    assert isinstance(analyses, list), "Should return a list"
    print(f"✅ get_all_analyses_for_user: {len(analyses)} analyses")
    
    # Test get_analysis_by_uuid with non-existent UUID
    result = get_analysis_by_uuid("non-existent-uuid", "testuser")
    assert result is None, "Should return None for non-existent UUID"
    print("✅ get_analysis_by_uuid handles non-existent UUIDs")
    
    # Test delete_analysis with non-existent UUID
    deleted = delete_analysis("non-existent-uuid", "testuser")
    assert deleted == False, "Should return False for non-existent UUID"
    print("✅ delete_analysis handles non-existent UUIDs")

def test_task_manager():
    """Test task manager functionality."""
    print("\n--- Testing Task Manager ---")
    
    # Get task manager instance
    tm = get_task_manager()
    print("✅ Task manager instance created")
    
    # Create test file
    test_zip = create_test_zip()
    
    try:
        # Create a new task
        task_id = tm.create_task(
            task_type=TaskType.NEW_PORTFOLIO,
            username="testuser",
            filename="test.zip",
            file_path=test_zip,
            analysis_type="non_llm"
        )
        
        assert isinstance(task_id, str), "Task ID should be string"
        assert len(task_id) > 0, "Task ID should not be empty"
        print(f"✅ Task created: {task_id}")
        
        # Get task status
        task = tm.get_task_status(task_id)
        assert task is not None, "Task should exist"
        assert task.task_id == task_id, "Task ID should match"
        assert task.username == "testuser", "Username should match"
        assert task.filename == "test.zip", "Filename should match"
        assert task.status in [TaskStatus.PENDING, TaskStatus.RUNNING], "Status should be valid"
        print(f"✅ Task status retrieved: {task.status}")
        
        # Get user tasks
        user_tasks = tm.get_user_tasks("testuser")
        assert len(user_tasks) >= 1, "Should have at least one task"
        assert any(t.task_id == task_id for t in user_tasks), "Should include our task"
        print(f"✅ User tasks retrieved: {len(user_tasks)} tasks")
        
        # Test task filtering
        other_user_tasks = tm.get_user_tasks("otheruser")
        assert not any(t.task_id == task_id for t in other_user_tasks), "Other user shouldn't see our task"
        print("✅ Task filtering works correctly")
        
    finally:
        # Cleanup
        if test_zip.exists():
            test_zip.unlink()

def test_file_manager():
    """Test file manager functionality."""
    print("\n--- Testing File Manager ---")
    
    # Create file manager
    fm = FileManager()
    print("✅ File manager created")
    
    # Create test file
    test_file = Path(tempfile.mktemp(suffix=".zip"))
    test_content = b"test zip content for hashing"
    test_file.write_bytes(test_content)
    
    try:
        # Test file hash calculation
        file_hash = fm.calculate_file_hash(test_file)
        assert isinstance(file_hash, str), "Hash should be string"
        assert len(file_hash) == 64, "SHA256 hash should be 64 characters"
        print(f"✅ File hash calculated: {file_hash[:16]}...")
        
        # Test hash consistency
        hash2 = fm.calculate_file_hash(test_file)
        assert file_hash == hash2, "Hash should be consistent"
        print("✅ Hash calculation is consistent")
        
        # Test permanent storage
        permanent_path = fm.store_file_permanently(test_file, file_hash)
        assert permanent_path.exists(), "File should be stored permanently"
        assert permanent_path.name == f"{file_hash}.zip", "Should use hash as filename"
        print(f"✅ File stored permanently: {permanent_path.name}")
        
        # Test deduplication
        test_file2 = Path(tempfile.mktemp(suffix=".zip"))
        test_file2.write_bytes(test_content)  # Same content
        
        permanent_path2 = fm.store_file_permanently(test_file2)
        assert permanent_path2 == permanent_path, "Should deduplicate identical files"
        assert not test_file2.exists(), "Duplicate should be removed"
        print("✅ File deduplication works")
        
        # Test file retrieval by hash
        retrieved_path = fm.get_file_by_hash(file_hash)
        assert retrieved_path == permanent_path, "Should retrieve correct file"
        print("✅ File retrieval by hash works")
        
    finally:
        # Cleanup
        for file in [test_file, permanent_path]:
            if file.exists():
                file.unlink()

def test_api_server():
    """Test API server configuration."""
    print("\n--- Testing API Server ---")
    
    # Test app configuration
    assert app.title == "FastAPI", "App should have correct title"
    assert app.version == "2.0.0", "App should have correct version"
    print("✅ API server configured correctly")
    
    # Test routes exist
    routes = [route.path for route in app.routes]
    expected_routes = [
        "/api/auth/signup",
        "/api/auth/login",
        "/api/auth/logout",
        "/api/portfolios",
        "/api/portfolios/{portfolio_id}",
        "/api/portfolios/upload",
        "/api/portfolios/{portfolio_id}/add",
        "/api/tasks/{task_id}",
        "/api/tasks",
        "/api/health",
        "/"
    ]
    
    for route in expected_routes:
        assert route in routes, f"Route {route} should exist"
    
    print(f"✅ All {len(expected_routes)} required routes exist")

def test_integration():
    """Test integration between components."""
    print("\n--- Testing Component Integration ---")
    
    # Initialize all components
    init_db()
    tm = get_task_manager()
    fm = FileManager()
    
    print("✅ All components initialized")
    
    # Test that components can work together
    test_zip = create_test_zip()
    
    try:
        # Calculate file hash
        file_hash = fm.calculate_file_hash(test_zip)
        
        # Create task
        task_id = tm.create_task(
            task_type=TaskType.NEW_PORTFOLIO,
            username="integration_test",
            filename="integration_test.zip",
            file_path=test_zip
        )
        
        # Get task
        task = tm.get_task_status(task_id)
        assert task.file_hash == file_hash, "Task should have correct file hash"
        
        print("✅ Components integrate correctly")
        
    finally:
        if test_zip.exists():
            test_zip.unlink()

def run_validation_tests():
    """Run all validation tests."""
    print("🚀 Running Enhanced API Validation Tests")
    print("=" * 50)
    
    tests = [
        test_database_integration,
        test_task_manager,
        test_file_manager,
        test_api_server,
        test_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("\n✅ Enhanced REST API Features Ready:")
        print("  • Database Integration Functions")
        print("  • Background Task Management System")
        print("  • File Management with Deduplication")
        print("  • Task Status Tracking Endpoints")
        print("  • Complete API Infrastructure")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = run_validation_tests()
    sys.exit(0 if success else 1)