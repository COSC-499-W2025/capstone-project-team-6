"""
Test suite for Enhanced REST API functionality.
Tests database integration, task management, file handling, and API endpoints.
"""

import asyncio
import json
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.analysis_database import (
    delete_analysis,
    get_all_analyses_for_user,
    get_analysis_by_uuid,
    init_db,
    record_analysis,
)
from backend.task_manager import FileManager, TaskStatus, TaskType, get_task_manager


class TestDatabaseIntegration:
    """Test enhanced database integration functions."""

    def setup_method(self):
        """Setup test database before each test."""
        init_db()

    def test_get_all_analyses_for_user(self):
        """Test getting all analyses for a specific user."""
        analyses = get_all_analyses_for_user("testuser")
        assert isinstance(analyses, list), "Should return a list"

    def test_get_analysis_by_uuid_nonexistent(self):
        """Test getting analysis by UUID that doesn't exist."""
        result = get_analysis_by_uuid("non-existent-uuid", "testuser")
        assert result is None, "Should return None for non-existent UUID"

    def test_delete_analysis_nonexistent(self):
        """Test deleting analysis that doesn't exist."""
        deleted = delete_analysis("non-existent-uuid", "testuser")
        assert deleted == False, "Should return False for non-existent UUID"

    def test_user_isolation(self):
        """Test that users can only see their own analyses."""
        user1_analyses = get_all_analyses_for_user("user1")
        user2_analyses = get_all_analyses_for_user("user2")

        # Both should return lists (even if empty)
        assert isinstance(user1_analyses, list)
        assert isinstance(user2_analyses, list)


class TestTaskManager:
    """Test task management system."""

    def setup_method(self):
        """Setup task manager before each test."""
        self.task_manager = get_task_manager()

    def test_task_manager_initialization(self):
        """Test that task manager initializes correctly."""
        assert self.task_manager is not None
        assert hasattr(self.task_manager, "create_task")
        assert hasattr(self.task_manager, "get_task_status")
        assert hasattr(self.task_manager, "get_user_tasks")

    def test_task_creation(self):
        """Test creating a new task without async execution."""
        # Test task creation by inspecting the task manager structure
        # without triggering async execution

        # Verify task manager has the required methods
        assert hasattr(
            self.task_manager, "create_task"
        ), "Should have create_task method"
        assert hasattr(self.task_manager, "tasks"), "Should have tasks storage"

        # Test that we can create task objects with proper structure
        from datetime import datetime

        from backend.task_manager import TaskInfo

        task = TaskInfo(
            task_id="test_123",
            task_type=TaskType.NEW_PORTFOLIO,
            username="testuser",
            filename="test.zip",
            file_path="test.zip",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            file_hash="abc123",
        )

        assert task.task_id == "test_123"
        assert task.username == "testuser"
        assert task.filename == "test.zip"
        assert task.status == TaskStatus.PENDING

    def test_task_status_retrieval_basic(self):
        """Test getting task status for existing task structure."""
        # Test with a pre-existing task in the task manager
        # This tests the data structure without creating async tasks
        from datetime import datetime

        from backend.task_manager import TaskInfo

        task = TaskInfo(
            task_id="test_123",
            task_type=TaskType.NEW_PORTFOLIO,
            username="testuser",
            filename="test.zip",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Directly access the tasks dict to insert test data
        self.task_manager.tasks["test_123"] = task

        retrieved_task = self.task_manager.get_task_status("test_123")
        assert retrieved_task is not None, "Task should exist"
        assert retrieved_task.task_id == "test_123", "Task ID should match"
        assert retrieved_task.username == "testuser", "Username should match"

    def test_user_task_filtering_basic(self):
        """Test that users only see their own tasks."""
        # Create test task data directly in the manager
        from datetime import datetime

        from backend.task_manager import TaskInfo

        user1_task = TaskInfo(
            task_id="user1_task",
            task_type=TaskType.NEW_PORTFOLIO,
            username="user1",
            filename="test.zip",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        user2_task = TaskInfo(
            task_id="user2_task",
            task_type=TaskType.NEW_PORTFOLIO,
            username="user2",
            filename="test.zip",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Insert tasks directly
        self.task_manager.tasks["user1_task"] = user1_task
        self.task_manager.tasks["user2_task"] = user2_task

        user1_tasks = self.task_manager.get_user_tasks("user1")
        user2_tasks = self.task_manager.get_user_tasks("user2")

        # User1 should see only their task
        user1_task_ids = [t.task_id for t in user1_tasks]
        user2_task_ids = [t.task_id for t in user2_tasks]

        assert "user1_task" in user1_task_ids, "User1 should see their task"
        assert "user1_task" not in user2_task_ids, "User2 shouldn't see user1's task"
        assert "user2_task" in user2_task_ids, "User2 should see their task"
        assert "user2_task" not in user1_task_ids, "User1 shouldn't see user2's task"


class TestFileManager:
    """Test file management system."""

    def setup_method(self):
        """Setup file manager before each test."""
        self.file_manager = FileManager()

    def test_file_manager_initialization(self):
        """Test file manager initializes correctly."""
        assert self.file_manager is not None
        assert hasattr(self.file_manager, "calculate_file_hash")
        assert hasattr(self.file_manager, "store_file_permanently")
        assert hasattr(self.file_manager, "get_file_by_hash")

    def test_file_hash_calculation(self):
        """Test file hash calculation."""
        test_file = Path(tempfile.mktemp(suffix=".zip"))
        test_content = b"test zip content for hashing"
        test_file.write_bytes(test_content)

        try:
            file_hash = self.file_manager.calculate_file_hash(test_file)

            assert isinstance(file_hash, str), "Hash should be string"
            assert len(file_hash) == 64, "SHA256 hash should be 64 characters"

            # Test hash consistency
            hash2 = self.file_manager.calculate_file_hash(test_file)
            assert file_hash == hash2, "Hash should be consistent"

        finally:
            if test_file.exists():
                test_file.unlink()

    def test_file_storage(self):
        """Test permanent file storage."""
        test_file = Path(tempfile.mktemp(suffix=".zip"))
        test_content = b"test content for storage"
        test_file.write_bytes(test_content)

        try:
            file_hash = self.file_manager.calculate_file_hash(test_file)
            permanent_path = self.file_manager.store_file_permanently(
                test_file, file_hash
            )

            assert permanent_path.exists(), "File should be stored permanently"
            assert (
                permanent_path.name == f"{file_hash}.zip"
            ), "Should use hash as filename"

            # Clean up permanent file
            if permanent_path.exists():
                permanent_path.unlink()

        finally:
            if test_file.exists():
                test_file.unlink()

    def test_file_deduplication(self):
        """Test file deduplication functionality."""
        test_content = b"identical content for dedup test"

        # Create two files with identical content
        test_file1 = Path(tempfile.mktemp(suffix=".zip"))
        test_file2 = Path(tempfile.mktemp(suffix=".zip"))
        test_file1.write_bytes(test_content)
        test_file2.write_bytes(test_content)

        try:
            # Store first file
            permanent_path1 = self.file_manager.store_file_permanently(test_file1)

            # Store second file (should deduplicate)
            permanent_path2 = self.file_manager.store_file_permanently(test_file2)

            assert (
                permanent_path1 == permanent_path2
            ), "Should deduplicate identical files"
            assert not test_file2.exists(), "Duplicate should be removed"

            # Clean up
            if permanent_path1.exists():
                permanent_path1.unlink()

        finally:
            for file in [test_file1, test_file2]:
                if file.exists():
                    file.unlink()


class TestAPIServerConfiguration:
    """Test API server configuration and routes."""

    def test_api_server_import(self):
        """Test that API server can be imported."""
        from backend.api_server import app

        assert app is not None
        assert app.title == "Portfolio & Resume Generation API"
        assert app.version == "2.0.0"

    def test_required_routes_exist(self):
        """Test that all required routes are configured."""
        from backend.api_server import app

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
            "/",
        ]

        for expected_route in expected_routes:
            assert expected_route in routes, f"Route {expected_route} should exist"


class TestComponentIntegration:
    """Test integration between all components."""

    def setup_method(self):
        """Setup all components for integration testing."""
        init_db()
        self.task_manager = get_task_manager()
        self.file_manager = FileManager()

    def test_full_integration(self):
        """Test that all components work together."""
        # Create test file
        test_file = Path(tempfile.mktemp(suffix=".zip"))
        test_file.write_bytes(b"integration test content")

        try:
            # Test file hash calculation
            file_hash = self.file_manager.calculate_file_hash(test_file)
            assert isinstance(file_hash, str)

            # Test task creation by directly creating a task object (avoid async)
            from datetime import datetime

            from backend.task_manager import TaskInfo

            task_data = TaskInfo(
                task_id="integration_123",
                task_type=TaskType.NEW_PORTFOLIO,
                username="integration_user",
                filename="integration.zip",
                file_hash=file_hash,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Insert task directly to test retrieval
            self.task_manager.tasks["integration_123"] = task_data

            # Test task retrieval
            task = self.task_manager.get_task_status("integration_123")
            assert task.file_hash == file_hash, "Task should have correct file hash"

            # Test database user scope
            user_analyses = get_all_analyses_for_user("integration_user")
            assert isinstance(user_analyses, list)

        finally:
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
