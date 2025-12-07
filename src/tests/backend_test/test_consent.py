# tests/test_consent.py
import builtins
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.consent import ask_for_consent
from backend.database import (check_user_consent, create_user, get_connection,
                              get_db_path, initialize, reset_db,
                              save_user_consent)
from backend.session import get_session, save_session


def _run_with_inputs(inputs, capsys):
    """Run ask_for_consent with a mock input that still prints the prompt."""
    it = iter(inputs)

    def fake_input(prompt=""):
        # emulate real input: print the prompt to stdout
        print(prompt, end="")
        return next(it)

    with patch.object(builtins, "input", side_effect=fake_input):
        result = ask_for_consent()
    out = capsys.readouterr().out
    return result, out


def test_prints_consent_form_once(capsys):
    # Single 'n' answer; ensure the big heading is printed
    result, out = _run_with_inputs(["n"], capsys)
    assert result is False
    assert "PROJECT CONSENT FORM: MINING DIGITAL WORK ARTIFACTS" in out
    # Prompt must appear
    assert "Do you consent to the terms above? [y/n]:" in out


@pytest.mark.parametrize("answer", ["y", "Y", "yes", "YES", " YeS ", "  y  "])
def test_yes_variants_return_true(answer, capsys):
    result, out = _run_with_inputs([answer], capsys)
    assert result is True
    # Should not print the "Please type 'y' or 'n'" error
    assert "Please type 'y' or 'n'" not in out


@pytest.mark.parametrize("answer", ["n", "N", "no", "NO", " nO ", "  n  "])
def test_no_variants_return_false(answer, capsys):
    result, out = _run_with_inputs([answer], capsys)
    assert result is False
    assert "Please type 'y' or 'n'" not in out


def test_invalid_then_yes(capsys):
    # User types invalid text, then confirms yes
    result, out = _run_with_inputs(["maybe", "", "y"], capsys)
    assert result is True
    # Should have shown the guidance at least twice (for "maybe" and empty)
    assert out.count("Please type 'y' or 'n'") >= 2


def test_invalid_then_no(capsys):
    result, out = _run_with_inputs(["   ", "no"], capsys)
    assert result is False
    assert "Please type 'y' or 'n'" in out


def test_eof_returns_false(capsys):
    # Simulate Ctrl-D / closed stdin; function should default to False
    with patch.object(builtins, "input", side_effect=EOFError):
        result = ask_for_consent()
    assert result is False


# Integration Tests
def test_database_consent_storage(temp_db, test_user):
    """Test storing and retrieving consent status in database."""
    username = test_user["username"]

    # Initially no consent record should exist
    assert not check_user_consent(username)

    # Save consent as True
    save_user_consent(username, True)

    # Check consent was saved
    with get_connection() as conn:
        record = conn.execute("SELECT has_consented, consent_date FROM user_consent WHERE username = ?", (username,)).fetchone()

    assert record is not None
    assert record["has_consented"] == 1
    assert record["consent_date"] is not None

    # Verify using the check function
    assert check_user_consent(username)


def test_consent_with_session(temp_db, test_user):
    """Test consent checking with active session."""
    username = test_user["username"]
    save_session(username)
    session = get_session()

    assert session["logged_in"]
    assert session["username"] == username
    assert not check_user_consent(session["username"])

    # Update consent
    save_user_consent(username, True)
    assert check_user_consent(session["username"])


# def test_analyze_consent_enforcement(temp_db, test_user):
#     """Test that analyze command enforces consent requirement."""
#     import sys
#     from io import StringIO

#     from backend.cli import main

#     username = test_user["username"]

#     # Save session but no consent
#     save_session(username)

#     # Try to analyze without consent
#     with patch("sys.argv", ["mda", "analyze", "."]), patch("sys.stdout", new=StringIO()) as fake_out:

#         result = main()
#         assert result == 1
#         output = fake_out.getvalue()
#         assert "Please provide consent" in output

#     # Now give consent and try again
#     save_user_consent(username, True)
#     with patch("sys.argv", ["mda", "analyze", "."]), patch("sys.stdout", new=StringIO()) as fake_out:

#         result = main()
#         # It might still fail for other reasons (like path not existing)
#         # but it shouldn't fail due to consent
#         assert "Please provide consent" not in fake_out.getvalue()


def test_consent_foreign_key_constraint(temp_db):
    """Test that consent records require valid users."""
    username = "johndoe"

    # Attempt to save consent for non-existent user should fail
    with pytest.raises(Exception) as exc_info:
        with get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("INSERT INTO user_consent (username, has_consented) VALUES (?, ?)", (username, True))
            conn.commit()

    assert "FOREIGN KEY constraint failed" in str(exc_info.value)
