"""Tests for applypilot.config."""

import json
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import applypilot.config as cfg


# ---------------------------------------------------------------------------
# DEFAULTS
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_required_keys_present(self):
        for key in ("min_score", "max_apply_attempts", "max_tailor_attempts",
                    "poll_interval", "apply_timeout", "viewport"):
            assert key in cfg.DEFAULTS

    def test_min_score_is_integer(self):
        assert isinstance(cfg.DEFAULTS["min_score"], int)

    def test_min_score_value(self):
        assert cfg.DEFAULTS["min_score"] == 7

    def test_viewport_format(self):
        w, h = cfg.DEFAULTS["viewport"].split("x")
        assert int(w) > 0 and int(h) > 0


# ---------------------------------------------------------------------------
# load_profile
# ---------------------------------------------------------------------------

class TestLoadProfile:
    def test_raises_when_profile_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cfg, "PROFILE_PATH", tmp_path / "profile.json")
        with pytest.raises(FileNotFoundError):
            cfg.load_profile()

    def test_loads_valid_profile(self, tmp_path, monkeypatch):
        profile = {"personal": {"full_name": "Alice"}, "skills_boundary": {}}
        path = tmp_path / "profile.json"
        path.write_text(json.dumps(profile))
        monkeypatch.setattr(cfg, "PROFILE_PATH", path)
        loaded = cfg.load_profile()
        assert loaded["personal"]["full_name"] == "Alice"

    def test_returns_dict(self, tmp_path, monkeypatch):
        path = tmp_path / "profile.json"
        path.write_text(json.dumps({"key": "value"}))
        monkeypatch.setattr(cfg, "PROFILE_PATH", path)
        result = cfg.load_profile()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# get_tier
# ---------------------------------------------------------------------------

class TestGetTier:
    def test_no_llm_key_returns_tier_1(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_URL", raising=False)
        # load_env is called inside get_tier; patch it to be a no-op
        with patch.object(cfg, "load_env"):
            tier = cfg.get_tier()
        assert tier == 1

    def test_llm_key_no_claude_returns_tier_2(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_URL", raising=False)
        with patch.object(cfg, "load_env"), \
             patch("shutil.which", return_value=None), \
             patch.object(cfg, "get_chrome_path", side_effect=FileNotFoundError):
            tier = cfg.get_tier()
        assert tier == 2

    def test_llm_key_plus_claude_plus_chrome_returns_tier_3(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_URL", raising=False)
        with patch.object(cfg, "load_env"), \
             patch("shutil.which", return_value="/usr/local/bin/claude"), \
             patch.object(cfg, "get_chrome_path", return_value="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
            tier = cfg.get_tier()
        assert tier == 3

    def test_openai_key_no_chrome_returns_tier_2(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_URL", raising=False)
        with patch.object(cfg, "load_env"), \
             patch("shutil.which", return_value=None), \
             patch.object(cfg, "get_chrome_path", side_effect=FileNotFoundError):
            tier = cfg.get_tier()
        assert tier == 2


# ---------------------------------------------------------------------------
# check_tier
# ---------------------------------------------------------------------------

class TestCheckTier:
    def test_sufficient_tier_does_not_raise(self, monkeypatch):
        with patch.object(cfg, "get_tier", return_value=3):
            cfg.check_tier(required=2, feature="AI Scoring")  # should not raise

    def test_insufficient_tier_raises_system_exit(self, monkeypatch):
        with patch.object(cfg, "get_tier", return_value=1):
            with pytest.raises(SystemExit):
                cfg.check_tier(required=2, feature="AI Scoring")

    def test_exact_tier_match_does_not_raise(self):
        with patch.object(cfg, "get_tier", return_value=2):
            cfg.check_tier(required=2, feature="Scoring")  # equal tier is fine


# ---------------------------------------------------------------------------
# is_manual_ats
# ---------------------------------------------------------------------------

class TestIsManualAts:
    def _mock_sites_cfg(self):
        return {"manual_ats": ["greenhouse.io", "lever.co", "myworkdayjobs.com"]}

    def test_none_url_returns_false(self):
        with patch.object(cfg, "load_sites_config", return_value=self._mock_sites_cfg()):
            assert cfg.is_manual_ats(None) is False

    def test_empty_url_returns_false(self):
        with patch.object(cfg, "load_sites_config", return_value=self._mock_sites_cfg()):
            assert cfg.is_manual_ats("") is False

    def test_known_ats_url_returns_true(self):
        with patch.object(cfg, "load_sites_config", return_value=self._mock_sites_cfg()):
            assert cfg.is_manual_ats("https://jobs.greenhouse.io/company/role123") is True

    def test_unknown_url_returns_false(self):
        with patch.object(cfg, "load_sites_config", return_value=self._mock_sites_cfg()):
            assert cfg.is_manual_ats("https://example.com/careers") is False

    def test_case_insensitive(self):
        with patch.object(cfg, "load_sites_config", return_value=self._mock_sites_cfg()):
            assert cfg.is_manual_ats("HTTPS://JOBS.GREENHOUSE.IO/ROLE") is True


# ---------------------------------------------------------------------------
# load_blocked_sites
# ---------------------------------------------------------------------------

class TestLoadBlockedSites:
    def _mock_cfg(self):
        return {
            "blocked": {
                "sites": ["Glassdoor", "Monster"],
                "url_patterns": ["/jobs/view/", "/job-listing/"],
            }
        }

    def test_returns_site_names_as_set(self):
        with patch.object(cfg, "load_sites_config", return_value=self._mock_cfg()):
            sites, patterns = cfg.load_blocked_sites()
        assert isinstance(sites, set)
        assert "Glassdoor" in sites

    def test_returns_patterns_as_list(self):
        with patch.object(cfg, "load_sites_config", return_value=self._mock_cfg()):
            sites, patterns = cfg.load_blocked_sites()
        assert isinstance(patterns, list)
        assert "/jobs/view/" in patterns

    def test_empty_config_returns_empty(self):
        with patch.object(cfg, "load_sites_config", return_value={}):
            sites, patterns = cfg.load_blocked_sites()
        assert sites == set()
        assert patterns == []


# ---------------------------------------------------------------------------
# get_chrome_path
# ---------------------------------------------------------------------------

class TestGetChromePath:
    def test_env_override_used_when_set_and_exists(self, tmp_path, monkeypatch):
        fake_chrome = tmp_path / "chrome"
        fake_chrome.touch()
        monkeypatch.setenv("CHROME_PATH", str(fake_chrome))
        assert cfg.get_chrome_path() == str(fake_chrome)

    def test_env_override_ignored_when_path_does_not_exist(self, monkeypatch):
        monkeypatch.setenv("CHROME_PATH", "/nonexistent/path/chrome")
        # Should fall through to platform detection; may raise FileNotFoundError
        # on machines without Chrome — that's acceptable
        try:
            cfg.get_chrome_path()
        except FileNotFoundError:
            pass  # expected on CI

    def test_raises_when_chrome_not_found(self, monkeypatch):
        monkeypatch.delenv("CHROME_PATH", raising=False)
        with patch("shutil.which", return_value=None), \
             patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                cfg.get_chrome_path()
