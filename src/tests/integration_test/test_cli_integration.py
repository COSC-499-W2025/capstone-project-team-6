"""Integration tests for CLI workflow: Signup -> Login -> Consent -> Analysis."""

import builtins
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend import database
from backend.cli import main


class TestCLISignupFlow:
    """Tests for CLI signup command and flow."""

    def test_successful_signup_with_consent_acceptance(self, isolated_test_env):
        """Test successful signup when user accepts consent."""
        with patch("sys.argv", ["cli", "signup", "newuser", "password123"]), patch.object(
            builtins, "input", return_value="y"
        ), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Account created successfully" in output
            assert "Thank you for providing consent" in output

            # Verify user was created in database
            user = database.get_user("newuser")
            assert user is not None
            assert user["username"] == "newuser"

            # Verify consent was saved
            assert database.check_user_consent("newuser") is True

    def test_successful_signup_with_consent_denial(self, isolated_test_env):
        """Test signup when user denies consent."""
        with patch("sys.argv", ["cli", "signup", "newuser", "password123"]), patch.object(
            builtins, "input", return_value="n"
        ), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            # Note: CLI returns 1 when consent is denied (signup() returns False)
            # This is the current behavior - signup without consent is treated as incomplete
            assert result == 1
            assert "Account created successfully" in output
            assert "You have not provided consent" in output

            # Verify user was created
            user = database.get_user("newuser")
            assert user is not None

            # Verify consent was denied
            assert database.check_user_consent("newuser") is False

    def test_signup_duplicate_username(self, isolated_test_env):
        """Test signup with username that already exists."""
        # Create initial user
        database.create_user("existinguser", "password123")

        with patch("sys.argv", ["cli", "signup", "existinguser", "newpassword"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Username already exists" in output


class TestCLILoginFlow:
    """Tests for CLI login command and flow."""

    def test_successful_login_with_existing_consent(self, isolated_test_env):
        """Test login when user already has consent."""
        # Setup: Create user with consent
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        with patch("sys.argv", ["cli", "login", "testuser", "password123"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Login successful" in output
            assert "Welcome testuser" in output

    def test_login_first_time_with_consent_acceptance(self, isolated_test_env):
        """Test first-time login when user accepts consent."""
        # Setup: Create user without consent
        database.create_user("newuser", "password123")

        with patch("sys.argv", ["cli", "login", "newuser", "password123"]), patch.object(
            builtins, "input", return_value="y"
        ), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Login successful" in output
            assert "Welcome newuser" in output

            # Verify consent was saved
            assert database.check_user_consent("newuser") is True

    def test_login_first_time_with_consent_denial(self, isolated_test_env):
        """Test first-time login when user denies consent."""
        # Setup: Create user without consent
        database.create_user("newuser", "password123")

        with patch("sys.argv", ["cli", "login", "newuser", "password123"]), patch.object(
            builtins, "input", return_value="n"
        ), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Denied Consent" in output

            # Verify consent was denied
            assert database.check_user_consent("newuser") is False

    def test_login_invalid_credentials(self, isolated_test_env):
        """Test login with invalid username or password."""
        # Setup: Create user
        database.create_user("testuser", "password123")

        with patch("sys.argv", ["cli", "login", "testuser", "wrongpassword"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Invalid username or password" in output

    def test_login_nonexistent_user(self, isolated_test_env):
        """Test login with user that doesn't exist."""
        with patch("sys.argv", ["cli", "login", "nonexistent", "password123"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Invalid username or password" in output


class TestCLIConsentCommands:
    """Tests for CLI consent management commands."""

    def test_consent_status_check_with_consent(self, isolated_test_env, temp_session_file):
        """Test checking consent status when user has consented."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "consent", "--status"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Consent Status for testuser" in output
            assert "Consented" in output

    def test_consent_status_check_without_consent(self, isolated_test_env, temp_session_file):
        """Test checking consent status when user hasn't consented."""
        # Setup: Create user without consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", False)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "consent", "--status"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Consent Status for testuser" in output
            assert "Not consented" in output

    def test_consent_update_for_non_consented_user(self, isolated_test_env, temp_session_file):
        """Test updating consent for user who hasn't consented."""
        # Setup: Create user without consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", False)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "consent", "--update"]), patch.object(builtins, "input", return_value="y"), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Thank you for providing consent" in output

            # Verify consent was updated
            assert database.check_user_consent("testuser") is True

    def test_consent_update_for_already_consented_user(self, isolated_test_env, temp_session_file):
        """Test updating consent for user who already consented."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "consent", "--update"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "You have already provided consent" in output

    def test_consent_commands_require_login(self, isolated_test_env):
        """Test that consent commands require being logged in."""
        with patch("sys.argv", ["cli", "consent", "--status"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Please login first" in output


class TestCLIAnalyzeFlow:
    """Tests for CLI analyze command and flow."""

    def test_analyze_requires_login(self, isolated_test_env):
        """Test that analyze command requires login."""
        with patch("sys.argv", ["cli", "analyze", "/some/path"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Please login first" in output

    def test_analyze_requires_consent(self, isolated_test_env, temp_session_file):
        """Test that analyze command requires consent."""
        # Setup: Create user without consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", False)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", "/some/path"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Please provide consent before analyzing files" in output

    def test_analyze_with_invalid_path(self, isolated_test_env, temp_session_file):
        """Test analyze with non-existent path."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", "/nonexistent/path"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 1
            assert "Path does not exist" in output

    def test_analyze_with_valid_path(self, isolated_test_env, temp_session_file, test_directory):
        """Test analyze with valid path."""
        # Setup: Create user with consent and session
        database.create_user("testuser", "password123")
        database.save_user_consent("testuser", True)

        from backend import session

        session.save_session("testuser")

        with patch("sys.argv", ["cli", "analyze", str(test_directory)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            output = fake_out.getvalue()

            assert result == 0
            assert "Analyzing folder" in output
            assert "Analysis Results" in output


class TestCLIEndToEndWorkflow:
    """End-to-end integration tests for complete CLI workflows."""

    def test_complete_happy_path_workflow(self, isolated_test_env, temp_session_file, test_directory):
        """Test complete workflow: signup -> login -> analyze."""
        # Step 1: Signup with consent
        with patch("sys.argv", ["cli", "signup", "alice", "alicepass"]), patch.object(builtins, "input", return_value="y"), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            assert result == 0
            assert "Account created successfully" in fake_out.getvalue()

        # Step 2: Login (should work immediately since consent was given)
        with patch("sys.argv", ["cli", "login", "alice", "alicepass"]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            assert "Login successful" in fake_out.getvalue()

        # Create session for analyze command
        from backend import session

        session.save_session("alice")

        # Step 3: Analyze (should work since user has consent)
        with patch("sys.argv", ["cli", "analyze", str(test_directory)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            assert "Analysis Results" in fake_out.getvalue()

    def test_workflow_with_consent_denial_then_update(self, isolated_test_env, temp_session_file, test_directory):
        """Test workflow: signup (deny consent) -> login -> consent update -> analyze."""
        # Step 1: Signup with consent denial (returns 1 due to consent denial)
        with patch("sys.argv", ["cli", "signup", "bob", "bobpass"]), patch.object(builtins, "input", return_value="n"), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            assert result == 1  # Signup without consent returns 1
            assert "You have not provided consent" in fake_out.getvalue()

        # Step 2: Login - user with consent=False will be prompted for consent again
        # If they deny again, login fails
        with patch("sys.argv", ["cli", "login", "bob", "bobpass"]), patch.object(builtins, "input", return_value="n"), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            # Login fails because user denied consent again
            assert result == 1
            assert "Denied Consent" in fake_out.getvalue()

        # Create session manually for consent update (simulating logged in state)
        from backend import session

        session.save_session("bob")

        # Step 3: Update consent
        with patch("sys.argv", ["cli", "consent", "--update"]), patch.object(builtins, "input", return_value="y"), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            assert result == 0
            assert "Thank you for providing consent" in fake_out.getvalue()

        # Step 4: Now analyze should work
        with patch("sys.argv", ["cli", "analyze", str(test_directory)]), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            assert "Analysis Results" in fake_out.getvalue()

    def test_workflow_signup_first_time_login_with_consent(self, isolated_test_env, temp_session_file):
        """Test workflow: signup (no consent prompt) -> first-time login (consent prompt)."""
        # Note: This test simulates a user created without going through consent
        # (e.g., created by admin or during signup with interrupted consent flow)

        # Step 1: Create user directly without consent
        database.create_user("charlie", "charliepass")

        # Step 2: First-time login should prompt for consent
        with patch("sys.argv", ["cli", "login", "charlie", "charliepass"]), patch.object(
            builtins, "input", return_value="y"
        ), patch("sys.stdout", new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            assert "Login successful" in fake_out.getvalue()

            # Verify consent was saved
            assert database.check_user_consent("charlie") is True

    def test_workflow_multiple_login_attempts_after_consent_denial(self, isolated_test_env):
        """Test workflow: signup (deny) -> multiple login attempts (all should fail)."""
        # Step 1: Signup with consent denial (returns 1)
        with patch("sys.argv", ["cli", "signup", "dave", "davepass"]), patch.object(builtins, "input", return_value="n"), patch(
            "sys.stdout", new=StringIO()
        ):
            result = main()
            assert result == 1  # Signup without consent returns 1

        # Step 2: First login attempt (should fail - need to mock input again)
        with patch("sys.argv", ["cli", "login", "dave", "davepass"]), patch.object(builtins, "input", return_value="n"), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            assert result == 1
            assert "Denied Consent" in fake_out.getvalue()

        # Step 3: Second login attempt (should also fail - mock input again)
        with patch("sys.argv", ["cli", "login", "dave", "davepass"]), patch.object(builtins, "input", return_value="n"), patch(
            "sys.stdout", new=StringIO()
        ) as fake_out:
            result = main()
            assert result == 1
            assert "Denied Consent" in fake_out.getvalue()
