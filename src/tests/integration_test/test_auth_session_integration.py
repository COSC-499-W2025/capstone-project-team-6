"""Integration tests for Authentication & Session Management.

These tests verify the complete authentication flow across multiple components:
- User signup/creation in database
- Session file creation and management
- Login authentication
- Session persistence
- Error handling for invalid operations
"""

import json
# Import backend modules
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend import database, session


class TestSignupIntegration:
    """Integration tests for user signup functionality."""

    def test_successful_signup_creates_user_and_session(self, isolated_test_env, temp_session_file):
        """
        Test 1: Successful signup creates user in database and session file.

        Workflow:
        1. Create new user with valid credentials
        2. Verify user created in database
        3. Verify password is hashed (not stored in plain text)
        4. Authenticate the user (which creates session)
        5. Verify session file exists
        6. Verify session contains correct data
        """
        username = "newuser"
        password = "password123"

        # Step 1: Create user (signup)
        user_id = database.create_user(username, password)
        assert user_id > 0, "User ID should be positive"

        # Step 2: Verify user in database
        user_record = database.get_user(username)
        assert user_record is not None, "User should exist in database"
        assert user_record["username"] == username
        assert user_record["password_hash"] != password, "Password should be hashed"
        assert len(user_record["password_hash"]) > 20, "Hash should be substantial length"

        # Step 3: Authenticate user (creates session)
        auth_success = database.authenticate_user(username, password)
        assert auth_success is True, "Authentication should succeed"

        # Step 4: Verify session file exists
        assert temp_session_file.exists(), "Session file should be created"

        # Step 5: Verify session contents
        session_data = json.loads(temp_session_file.read_text())
        assert session_data["logged_in"] is True, "User should be logged in"
        assert session_data["username"] == username, "Session should contain correct username"

        # Step 6: Verify get_session() returns correct data
        retrieved_session = session.get_session()
        assert retrieved_session["logged_in"] is True
        assert retrieved_session["username"] == username

    def test_duplicate_signup_prevents_creation(self, isolated_test_env, temp_session_file):
        """
        Test 2: Attempting to signup with existing username fails.

        Workflow:
        1. Create user "alice"
        2. Verify user exists in database
        3. Attempt to create same user again
        4. Verify UserAlreadyExistsError is raised
        5. Verify only one user entry exists in database
        6. Verify no session file created
        """
        username = "alice"
        password = "password123"

        # Step 1: Create first user
        user_id = database.create_user(username, password)
        assert user_id > 0

        # Step 2: Verify user exists
        user_record = database.get_user(username)
        assert user_record is not None

        # Step 3: Attempt duplicate creation
        with pytest.raises(database.UserAlreadyExistsError) as exc_info:
            database.create_user(username, "differentpassword")

        # Step 4: Verify error message
        assert "already exists" in str(exc_info.value).lower()

        # Step 5: Verify only one entry in database
        with database.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) as count FROM users WHERE username = ?", (username,)).fetchone()["count"]
            assert count == 1, "Should only have one user entry"

        # Step 6: Verify no session created (since we didn't authenticate)
        assert not temp_session_file.exists(), "Session file should not exist yet"

    def test_signup_with_weak_password_validation(self, isolated_test_env):
        """
        Test 3: Signup with empty or weak passwords is handled appropriately.

        Workflow:
        1. Attempt to create user with empty password
        2. Verify ValueError is raised
        3. Attempt to create user with empty username
        4. Verify ValueError is raised
        5. Verify no users created in database
        """
        # Step 1: Test empty password
        with pytest.raises(ValueError) as exc_info:
            database.create_user("testuser", "")
        assert "password" in str(exc_info.value).lower()

        # Step 2: Test empty username
        with pytest.raises(ValueError) as exc_info:
            database.create_user("", "password123")
        assert "username" in str(exc_info.value).lower()

        # Step 3: Verify no users created
        with database.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
            assert count == 0, "No users should be created"

    def test_signup_with_special_characters_in_username(self, isolated_test_env):
        """
        Test 4: Signup with special characters in username.

        Workflow:
        1. Create user with spaces in username
        2. Verify user created successfully or fails gracefully
        3. Create user with special characters
        4. Verify database handles special characters correctly
        5. Verify authentication works with special usernames
        """
        # Test with spaces (should work - no explicit validation against it)
        username_with_spaces = "user name"
        password = "password123"

        user_id = database.create_user(username_with_spaces, password)
        assert user_id > 0

        # Verify retrieval works
        user_record = database.get_user(username_with_spaces)
        assert user_record is not None
        assert user_record["username"] == username_with_spaces

        # Verify authentication works
        auth_success = database.authenticate_user(username_with_spaces, password)
        assert auth_success is True

        # Test with special characters
        username_special = "user@test.com"
        user_id2 = database.create_user(username_special, password)
        assert user_id2 > 0

        user_record2 = database.get_user(username_special)
        assert user_record2 is not None
        assert user_record2["username"] == username_special


class TestLoginIntegration:
    """Integration tests for user login functionality."""

    def test_successful_login_creates_session(self, isolated_test_env, temp_session_file):
        """
        Test 5: Successful login creates session file with correct data.

        Workflow:
        1. Pre-create user "bob"
        2. Verify session file does not exist
        3. Authenticate with correct credentials
        4. Verify authentication returns True
        5. Verify session file created
        6. Verify session contains correct username and logged_in=True
        """
        username = "bob"
        password = "securepass456"

        # Step 1: Create user
        database.create_user(username, password)

        # Step 2: Clear any existing session
        session.clear_session()
        assert not temp_session_file.exists(), "Session file should not exist initially"

        # Step 3: Authenticate (login)
        auth_success = database.authenticate_user(username, password)

        # Step 4: Verify authentication succeeded
        assert auth_success is True, "Authentication should succeed with correct credentials"

        # Step 5: Verify session file created
        assert temp_session_file.exists(), "Session file should be created after login"

        # Step 6: Verify session contents
        session_data = json.loads(temp_session_file.read_text())
        assert session_data["logged_in"] is True
        assert session_data["username"] == username

    def test_login_with_wrong_password(self, isolated_test_env, temp_session_file):
        """
        Test 6: Login with incorrect password fails and no session is created.

        Workflow:
        1. Pre-create user "carol" with password "correct789"
        2. Attempt login with wrong password
        3. Verify authentication returns False
        4. Verify session file NOT created
        5. Verify get_session() shows logged_in=False
        """
        username = "carol"
        correct_password = "correct789"
        wrong_password = "wrong000"

        # Step 1: Create user
        database.create_user(username, correct_password)

        # Step 2: Clear session
        session.clear_session()

        # Step 3: Attempt authentication with wrong password
        auth_success = database.authenticate_user(username, wrong_password)

        # Step 4: Verify authentication failed
        assert auth_success is False, "Authentication should fail with wrong password"

        # Step 5: Verify no session file created
        assert not temp_session_file.exists(), "Session file should not be created on failed login"

        # Step 6: Verify session state shows not logged in
        session_data = session.get_session()
        assert session_data["logged_in"] is False
        assert session_data["username"] is None

    def test_login_with_nonexistent_user(self, isolated_test_env, temp_session_file):
        """
        Test 7: Login with non-existent user fails.

        Workflow:
        1. Do NOT create any users
        2. Attempt login with non-existent username
        3. Verify authentication returns False
        4. Verify session file NOT created
        """
        username = "ghost"
        password = "anypassword"

        # Step 1: Ensure user doesn't exist
        user_record = database.get_user(username)
        assert user_record is None, "User should not exist"

        # Step 2: Clear session
        session.clear_session()

        # Step 3: Attempt authentication
        auth_success = database.authenticate_user(username, password)

        # Step 4: Verify authentication failed
        assert auth_success is False, "Authentication should fail for non-existent user"

        # Step 5: Verify no session created
        assert not temp_session_file.exists(), "Session file should not be created"

        # Step 6: Verify session state
        session_data = session.get_session()
        assert session_data["logged_in"] is False

    def test_login_overwrites_previous_session(self, isolated_test_env, temp_session_file, mock_users):
        """
        Test 8: Logging in as a different user overwrites previous session.

        Workflow:
        1. Pre-create users "alice" and "bob"
        2. Login as "alice"
        3. Verify session contains "alice"
        4. Login as "bob" (without explicit logout)
        5. Verify session now contains "bob"
        6. Verify previous session completely replaced
        """
        # mock_users fixture already created alice and bob
        alice_password = mock_users["alice"]
        bob_password = mock_users["bob"]

        # Step 1: Login as alice
        auth_success = database.authenticate_user("alice", alice_password)
        assert auth_success is True

        # Step 2: Verify alice session
        session_data = session.get_session()
        assert session_data["logged_in"] is True
        assert session_data["username"] == "alice"

        # Step 3: Login as bob (overwrites alice's session)
        auth_success = database.authenticate_user("bob", bob_password)
        assert auth_success is True

        # Step 4: Verify bob session replaced alice
        session_data = session.get_session()
        assert session_data["logged_in"] is True
        assert session_data["username"] == "bob", "Session should now contain bob"

        # Step 5: Verify session file content
        file_content = json.loads(temp_session_file.read_text())
        assert file_content["username"] == "bob"
        assert "alice" not in json.dumps(file_content), "Alice should not be in session anymore"


class TestHelpers:
    """Helper tests to verify test infrastructure works correctly."""

    def test_isolated_test_env_provides_clean_state(self, isolated_test_env, temp_db, temp_session_file):
        """Verify that isolated_test_env fixture provides clean state."""
        # Database should be empty
        with database.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
            assert count == 0, "Database should be empty"

        # Session file should not exist
        assert not temp_session_file.exists(), "Session file should not exist"

        # get_session should return logged out state
        session_data = session.get_session()
        assert session_data["logged_in"] is False
        assert session_data["username"] is None

    def test_mock_users_fixture_creates_users(self, temp_db, mock_users):
        """Verify that mock_users fixture creates test users correctly."""
        # Verify all mock users exist
        assert len(mock_users) > 0, "Should have mock users"

        for username, password in mock_users.items():
            # Verify user in database
            user_record = database.get_user(username)
            assert user_record is not None, f"User {username} should exist"
            assert user_record["username"] == username

            # Verify password works
            auth_success = database.authenticate_user(username, password)
            assert auth_success is True, f"Authentication should work for {username}"
