#!/usr/bin/env python3
"""
Test suite for the enhanced REST API with task management and file handling.
"""

import asyncio
import json
import tempfile
import uuid
import zipfile
from pathlib import Path
import pytest
import requests
from fastapi.testclient import TestClient

# Import our API server
import sys
sys.path.insert(0, 'src')
from backend.api_server import app
from backend.task_manager import get_task_manager, TaskStatus
from backend.analysis_database import init_db, get_all_analyses

# Test client
client = TestClient(app)

class TestEnhancedAPI:
    """Test suite for enhanced API functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        # Initialize databases
        init_db()
        
        # Create test user
        self.test_user = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": "password123"
        }
        
        # Signup and get token
        response = client.post("/api/auth/signup", json=self.test_user)
        assert response.status_code == 201
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def create_test_zip(self) -> Path:
        """Create a test ZIP file."""
        temp_dir = Path(tempfile.mkdtemp())
        zip_path = temp_dir / "test_project.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add test Python file
            zf.writestr("main.py", """
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")
            
            # Add README
            zf.writestr("README.md", "# Test Project\nThis is a test project.")
            
            # Add requirements
            zf.writestr("requirements.txt", "requests==2.28.0\npytest==7.0.0")
        
        return zip_path
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Blume API"
        assert "version" in data
    
    def test_auth_flow(self):
        """Test complete authentication flow."""
        # Test login with created user
        response = client.post("/api/auth/login", json=self.test_user)
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # Test logout
        response = client.post("/api/auth/logout", headers=self.headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_invalid_auth(self):
        """Test authentication with invalid credentials."""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass"
        })
        assert response.status_code == 401
    
    def test_portfolio_upload_new(self):
        """Test uploading a new portfolio."""
        zip_path = self.create_test_zip()
        
        with open(zip_path, "rb") as f:
            files = {"file": ("test_project.zip", f, "application/zip")}
            data = {"analysis_type": "non_llm"}
            response = client.post(
                "/api/portfolios/upload",
                files=files,
                data=data,
                headers=self.headers
            )
        
        assert response.status_code == 202
        result = response.json()
        assert "details" in result
        assert "task_id" in result["details"]
        assert result["details"]["analysis_type"] == "non_llm"
        assert result["details"]["status"] == "processing"
        
        return result["details"]["task_id"]
    
    def test_task_status_tracking(self):
        """Test task status endpoint."""
        # Upload a file to get a task
        task_id = self.test_portfolio_upload_new()
        
        # Check task status
        response = client.get(f"/api/tasks/{task_id}", headers=self.headers)
        assert response.status_code == 200
        
        task_data = response.json()
        assert task_data["task_id"] == task_id
        assert task_data["status"] in ["pending", "running", "completed", "failed"]
        assert "progress" in task_data
        assert "created_at" in task_data
        assert "filename" in task_data
        
        # Wait a moment for processing
        import time
        time.sleep(3)
        
        # Check status again
        response = client.get(f"/api/tasks/{task_id}", headers=self.headers)
        updated_task = response.json()
        assert updated_task["task_id"] == task_id
        # Should have progressed or completed
        assert updated_task["progress"] >= task_data["progress"]
    
    def test_get_user_tasks(self):
        """Test getting all user tasks."""
        # Upload a file to create a task
        self.test_portfolio_upload_new()
        
        # Get user tasks
        response = client.get("/api/tasks", headers=self.headers)
        assert response.status_code == 200
        
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        
        # Check task structure
        task = tasks[0]
        assert "task_id" in task
        assert "status" in task
        assert "progress" in task
        assert "task_type" in task
        assert "filename" in task
    
    def test_list_portfolios(self):
        """Test listing user portfolios."""
        response = client.get("/api/portfolios", headers=self.headers)
        assert response.status_code == 200
        
        portfolios = response.json()
        assert isinstance(portfolios, list)
        # Might be empty if no analyses exist yet
    
    def test_invalid_file_upload(self):
        """Test uploading invalid file types."""
        # Test non-ZIP file
        files = {"file": ("test.txt", "not a zip file", "text/plain")}
        data = {"analysis_type": "non_llm"}
        response = client.post(
            "/api/portfolios/upload",
            files=files,
            data=data,
            headers=self.headers
        )
        assert response.status_code == 400
        assert "ZIP file" in response.json()["detail"]
    
    def test_invalid_analysis_type(self):
        """Test uploading with invalid analysis type."""
        zip_path = self.create_test_zip()
        
        with open(zip_path, "rb") as f:
            files = {"file": ("test_project.zip", f, "application/zip")}
            data = {"analysis_type": "invalid_type"}
            response = client.post(
                "/api/portfolios/upload",
                files=files,
                data=data,
                headers=self.headers
            )
        
        assert response.status_code == 400
        assert "analysis_type must be" in response.json()["detail"]
    
    def test_unauthorized_access(self):
        """Test accessing endpoints without authentication."""
        # Test without token
        response = client.get("/api/portfolios")
        assert response.status_code == 403
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/portfolios", headers=headers)
        assert response.status_code == 401
    
    def test_nonexistent_task(self):
        """Test getting status of non-existent task."""
        fake_task_id = str(uuid.uuid4())
        response = client.get(f"/api/tasks/{fake_task_id}", headers=self.headers)
        assert response.status_code == 404
    
    def test_task_access_control(self):
        """Test that users can only access their own tasks."""
        # Create another user
        other_user = {
            "username": f"otheruser_{uuid.uuid4().hex[:8]}",
            "password": "password123"
        }
        response = client.post("/api/auth/signup", json=other_user)
        other_token = response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        # Upload file with first user
        task_id = self.test_portfolio_upload_new()
        
        # Try to access task with second user
        response = client.get(f"/api/tasks/{task_id}", headers=other_headers)
        assert response.status_code == 403


class TestTaskManager:
    """Test suite for task manager functionality."""
    
    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Test creating tasks."""
        task_manager = get_task_manager()
        
        # Create temporary file
        temp_file = Path(tempfile.mktemp(suffix=".zip"))
        temp_file.write_bytes(b"fake zip content")
        
        try:
            # Run in event loop
            loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
            if not loop.is_running():
                asyncio.set_event_loop(loop)
            
            task_id = task_manager.create_task(
                task_type="new_portfolio",
                username="testuser",
                filename="test.zip",
                file_path=temp_file,
                analysis_type="non_llm"
            )
            
            assert isinstance(task_id, str)
            assert len(task_id) > 0
            
            # Check task exists
            task = task_manager.get_task_status(task_id)
            assert task is not None
            assert task.username == "testuser"
            assert task.filename == "test.zip"
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_user_task_filtering(self):
        """Test getting tasks for specific users."""
        task_manager = get_task_manager()
        
        # Create temporary files
        temp_file1 = Path(tempfile.mktemp(suffix=".zip"))
        temp_file2 = Path(tempfile.mktemp(suffix=".zip"))
        temp_file1.write_bytes(b"fake zip content 1")
        temp_file2.write_bytes(b"fake zip content 2")
        
        try:
            # Ensure event loop is set
            loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
            if not loop.is_running():
                asyncio.set_event_loop(loop)
                
            # Create tasks for different users
            task1 = task_manager.create_task(
                task_type="new_portfolio",
                username="user1",
                filename="test1.zip",
                file_path=temp_file1
            )
            
            task2 = task_manager.create_task(
                task_type="new_portfolio",
                username="user2",
                filename="test2.zip",
                file_path=temp_file2
            )
            
            # Get tasks for user1
            user1_tasks = task_manager.get_user_tasks("user1")
            assert len(user1_tasks) == 1
            assert user1_tasks[0].task_id == task1
            
            # Get tasks for user2
            user2_tasks = task_manager.get_user_tasks("user2")
            assert len(user2_tasks) == 1
            assert user2_tasks[0].task_id == task2
            
        finally:
            for file in [temp_file1, temp_file2]:
                if file.exists():
                    file.unlink()


def run_api_tests():
    """Run all API tests."""
    print("Running Enhanced API Tests...")
    
    # API Tests
    api_tests = TestEnhancedAPI()
    
    test_methods = [
        api_tests.test_health_endpoint,
        api_tests.test_root_endpoint,
        api_tests.test_invalid_auth,
        api_tests.test_invalid_file_upload,
        api_tests.test_unauthorized_access,
    ]
    
    passed = 0
    total = len(test_methods)
    
    for test_method in test_methods:
        try:
            test_method()
            print(f"✅ {test_method.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method.__name__}: {e}")
    
    # Tests that require setup
    setup_tests = [
        ("test_auth_flow", api_tests.test_auth_flow),
        ("test_portfolio_upload_new", api_tests.test_portfolio_upload_new),
        ("test_list_portfolios", api_tests.test_list_portfolios),
        ("test_invalid_analysis_type", api_tests.test_invalid_analysis_type),
        ("test_nonexistent_task", api_tests.test_nonexistent_task),
        ("test_task_status_tracking", api_tests.test_task_status_tracking),
        ("test_get_user_tasks", api_tests.test_get_user_tasks),
        ("test_task_access_control", api_tests.test_task_access_control),
    ]
    
    for test_name, test_method in setup_tests:
        try:
            api_tests.setup_method()
            test_method()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
        total += 1
    
    # Task Manager Tests
    print("\nRunning Task Manager Tests...")
    task_tests = TestTaskManager()
    
    task_test_methods = [
        task_tests.test_task_creation,
        task_tests.test_user_task_filtering,
    ]
    
    for test_method in task_test_methods:
        try:
            test_method()
            print(f"✅ {test_method.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method.__name__}: {e}")
        total += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    import sys
    success = run_api_tests()
    sys.exit(0 if success else 1)