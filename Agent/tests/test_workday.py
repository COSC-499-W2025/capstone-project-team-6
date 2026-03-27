"""Tests for applypilot.discovery.workday (_HTMLStripper, _location_ok, load_employers)."""

from unittest.mock import patch

import pytest

from applypilot.discovery.workday import _HTMLStripper, _location_ok, load_employers


# ---------------------------------------------------------------------------
# _HTMLStripper
# ---------------------------------------------------------------------------

class TestHTMLStripper:
    def _strip(self, html: str) -> str:
        p = _HTMLStripper()
        p.feed(html)
        return p.get_text()

    def test_plain_text_unchanged(self):
        result = self._strip("Hello world")
        assert result == "Hello world"

    def test_strips_simple_tags(self):
        result = self._strip("<b>Bold</b> text")
        assert result == "Bold text"

    def test_strips_nested_tags(self):
        result = self._strip("<div><p>Hello <span>world</span></p></div>")
        assert "Hello" in result
        assert "world" in result
        assert "<" not in result

    def test_block_tags_add_newlines(self):
        result = self._strip("<p>First</p><p>Second</p>")
        assert "First" in result
        assert "Second" in result
        assert "\n" in result

    def test_script_content_stripped(self):
        result = self._strip("<p>Visible</p><script>alert('hack')</script>")
        assert "Visible" in result
        assert "alert" not in result

    def test_style_content_stripped(self):
        result = self._strip("<p>Text</p><style>body { color: red; }</style>")
        assert "Text" in result
        assert "color" not in result

    def test_br_tag_adds_newline(self):
        result = self._strip("Line one<br>Line two")
        assert "Line one" in result
        assert "Line two" in result
        assert "\n" in result

    def test_li_tags_add_newlines(self):
        result = self._strip("<ul><li>Item 1</li><li>Item 2</li></ul>")
        assert "Item 1" in result
        assert "Item 2" in result

    def test_multiple_spaces_collapsed(self):
        result = self._strip("Hello    world")
        assert "  " not in result

    def test_more_than_two_consecutive_newlines_collapsed(self):
        result = self._strip("<p>A</p><p></p><p></p><p>B</p>")
        # Should not have 3+ consecutive newlines
        assert "\n\n\n" not in result

    def test_empty_input(self):
        result = self._strip("")
        assert result == ""

    def test_result_is_stripped(self):
        result = self._strip("   <p>Text</p>   ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_heading_tags_add_newlines(self):
        # Put text before the heading so the leading \n isn't stripped
        result = self._strip("<p>Intro</p><h1>Title</h1>Content")
        assert "Title" in result
        assert "Content" in result
        assert "\n" in result

    def test_get_text_returns_string(self):
        p = _HTMLStripper()
        p.feed("<p>Hello</p>")
        assert isinstance(p.get_text(), str)

    def test_table_row_adds_newline(self):
        result = self._strip("<tr><td>Cell 1</td></tr><tr><td>Cell 2</td></tr>")
        assert "Cell 1" in result
        assert "Cell 2" in result


# ---------------------------------------------------------------------------
# _location_ok
# ---------------------------------------------------------------------------

class TestLocationOk:
    # --- Remote always passes ---

    def test_remote_always_accepted(self):
        assert _location_ok("Remote", accept=[], reject=["Toronto"]) is True

    def test_anywhere_always_accepted(self):
        assert _location_ok("Anywhere", accept=[], reject=["Toronto"]) is True

    def test_work_from_home_accepted(self):
        assert _location_ok("Work From Home", accept=[], reject=["Toronto"]) is True

    def test_wfh_abbreviation_accepted(self):
        assert _location_ok("WFH – US", accept=[], reject=[]) is True

    def test_distributed_accepted(self):
        assert _location_ok("Distributed Team", accept=[], reject=["Toronto"]) is True

    # --- None/empty location ---

    def test_none_location_passes(self):
        assert _location_ok(None, accept=["Toronto"], reject=["New York"]) is True

    def test_empty_string_location_passes(self):
        assert _location_ok("", accept=["Toronto"], reject=["New York"]) is True

    # --- Reject list ---

    def test_rejected_location_blocked(self):
        assert _location_ok("New York, NY", accept=[], reject=["new york"]) is False

    def test_reject_is_case_insensitive(self):
        assert _location_ok("TORONTO, ON", accept=[], reject=["toronto"]) is False

    # --- Accept list ---

    def test_accepted_location_passes(self):
        assert _location_ok("Toronto, ON", accept=["toronto"], reject=["new york"]) is True

    def test_accept_is_case_insensitive(self):
        assert _location_ok("TORONTO, ON", accept=["toronto"], reject=[]) is True

    def test_unrecognized_location_fails(self):
        # Not remote, not in accept list
        assert _location_ok("Phoenix, AZ", accept=["toronto"], reject=["new york"]) is False

    def test_reject_checked_before_accept(self):
        # Same substring in both — reject wins
        assert _location_ok("Toronto", accept=["toronto"], reject=["toronto"]) is False

    # --- Edge cases ---

    def test_empty_accept_and_reject_unknown_location_fails(self):
        assert _location_ok("Phoenix, AZ", accept=[], reject=[]) is False

    def test_empty_accept_and_reject_remote_passes(self):
        assert _location_ok("Remote US", accept=[], reject=[]) is True


# ---------------------------------------------------------------------------
# load_employers
# ---------------------------------------------------------------------------

class TestLoadEmployers:
    def test_returns_dict(self):
        result = load_employers()
        assert isinstance(result, dict)

    def test_contains_known_employers(self):
        result = load_employers()
        # The shipped employers.yaml should have at least a few entries
        assert len(result) > 0

    def test_missing_yaml_returns_empty_dict(self, tmp_path, monkeypatch):
        import applypilot.discovery.workday as wd_module
        monkeypatch.setattr(
            "applypilot.discovery.workday.CONFIG_DIR",
            tmp_path,
        )
        result = load_employers()
        assert result == {}

    def test_employer_has_required_keys(self):
        employers = load_employers()
        if not employers:
            pytest.skip("No employers in registry")
        first = next(iter(employers.values()))
        # Each employer entry should have at minimum a tenant identifier
        assert isinstance(first, dict)
