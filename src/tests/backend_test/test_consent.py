# tests/test_consent.py
import builtins
from unittest.mock import patch

import pytest
from backend.consent import ask_for_consent


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
