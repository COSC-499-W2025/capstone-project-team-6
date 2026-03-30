"""Tests for applypilot.llm."""

import os
from unittest.mock import MagicMock, patch

import pytest

import applypilot.llm as llm_module
from applypilot.llm import LLMClient, _detect_provider


# ---------------------------------------------------------------------------
# _detect_provider
# ---------------------------------------------------------------------------

class TestDetectProvider:
    def _clean_env(self, monkeypatch):
        for key in ("GEMINI_API_KEY", "OPENAI_API_KEY", "LLM_URL", "LLM_MODEL", "LLM_API_KEY"):
            monkeypatch.delenv(key, raising=False)

    def test_gemini_key_selects_gemini(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-fake-key")
        base_url, model, api_key = _detect_provider()
        assert "generativelanguage.googleapis.com" in base_url
        assert "gemini" in model
        assert api_key == "gemini-fake-key"

    def test_openai_key_selects_openai(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        base_url, model, api_key = _detect_provider()
        assert "openai.com" in base_url
        assert "gpt" in model
        assert api_key == "sk-fake"

    def test_local_url_selects_local(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("LLM_URL", "http://localhost:11434/v1")
        base_url, model, api_key = _detect_provider()
        assert base_url == "http://localhost:11434/v1"
        assert model == "local-model"

    def test_local_url_strips_trailing_slash(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("LLM_URL", "http://localhost:11434/v1/")
        base_url, model, _ = _detect_provider()
        assert not base_url.endswith("/")

    def test_model_override_respected(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("GEMINI_API_KEY", "key")
        monkeypatch.setenv("LLM_MODEL", "gemini-1.5-pro")
        _, model, _ = _detect_provider()
        assert model == "gemini-1.5-pro"

    def test_no_provider_raises_runtime_error(self, monkeypatch):
        self._clean_env(monkeypatch)
        with pytest.raises(RuntimeError, match="No LLM provider"):
            _detect_provider()

    def test_local_url_takes_priority_over_gemini(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
        monkeypatch.setenv("LLM_URL", "http://localhost:11434/v1")
        base_url, _, _ = _detect_provider()
        assert "localhost" in base_url

    def test_local_url_takes_priority_over_openai(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        monkeypatch.setenv("LLM_URL", "http://localhost:11434/v1")
        base_url, _, _ = _detect_provider()
        assert "localhost" in base_url

    def test_returns_tuple_of_three_strings(self, monkeypatch):
        self._clean_env(monkeypatch)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        result = _detect_provider()
        assert len(result) == 3
        assert all(isinstance(x, str) for x in result)


# ---------------------------------------------------------------------------
# LLMClient initialization
# ---------------------------------------------------------------------------

class TestLLMClientInit:
    def test_is_gemini_true_for_gemini_url(self):
        client = LLMClient(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model="gemini-2.0-flash",
            api_key="key",
        )
        assert client._is_gemini is True

    def test_is_gemini_false_for_openai_url(self):
        client = LLMClient(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            api_key="sk-key",
        )
        assert client._is_gemini is False

    def test_is_gemini_false_for_local_url(self):
        client = LLMClient(
            base_url="http://localhost:11434/v1",
            model="local-model",
            api_key="",
        )
        assert client._is_gemini is False

    def test_use_native_gemini_starts_false(self):
        client = LLMClient(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model="gemini-2.0-flash",
            api_key="key",
        )
        assert client._use_native_gemini is False

    def test_attributes_stored(self):
        client = LLMClient(base_url="http://x.com", model="my-model", api_key="abc")
        assert client.base_url == "http://x.com"
        assert client.model == "my-model"
        assert client.api_key == "abc"

    def test_close_does_not_raise(self):
        client = LLMClient(base_url="http://x.com", model="m", api_key="k")
        client.close()  # should not raise


# ---------------------------------------------------------------------------
# LLMClient.ask / chat (mocked HTTP)
# ---------------------------------------------------------------------------

class TestLLMClientChat:
    def _make_client(self):
        return LLMClient(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            api_key="sk-fake",
        )

    def _mock_response(self, content="Hello world"):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "choices": [{"message": {"content": content}}]
        }
        resp.raise_for_status.return_value = None
        return resp

    def test_ask_returns_string(self):
        client = self._make_client()
        mock_resp = self._mock_response("Test response")
        with patch.object(client._client, "post", return_value=mock_resp):
            result = client.ask("Say hello")
        assert result == "Test response"

    def test_chat_uses_provided_messages(self):
        client = self._make_client()
        mock_resp = self._mock_response("Response text")
        with patch.object(client._client, "post", return_value=mock_resp) as mock_post:
            client.chat([{"role": "user", "content": "Hello"}])
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs["json"]
            assert payload["messages"][0]["content"] == "Hello"

    def test_qwen_model_prepends_no_think(self):
        client = LLMClient(
            base_url="https://api.openai.com/v1",
            model="qwen3-8b",
            api_key="key",
        )
        mock_resp = self._mock_response("ok")
        with patch.object(client._client, "post", return_value=mock_resp) as mock_post:
            client.chat([{"role": "user", "content": "Extract this"}])
            payload = mock_post.call_args[1]["json"]
            assert payload["messages"][0]["content"].startswith("/no_think")

    def test_non_qwen_model_no_prefix(self):
        client = self._make_client()
        mock_resp = self._mock_response("ok")
        with patch.object(client._client, "post", return_value=mock_resp) as mock_post:
            client.chat([{"role": "user", "content": "Hello"}])
            payload = mock_post.call_args[1]["json"]
            assert not payload["messages"][0]["content"].startswith("/no_think")


# ---------------------------------------------------------------------------
# get_client singleton
# ---------------------------------------------------------------------------

class TestGetClient:
    def test_returns_same_instance_twice(self, monkeypatch):
        monkeypatch.setattr(llm_module, "_instance", None)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_URL", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        c1 = llm_module.get_client()
        c2 = llm_module.get_client()
        assert c1 is c2

    def test_singleton_is_llm_client_instance(self, monkeypatch):
        monkeypatch.setattr(llm_module, "_instance", None)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_URL", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        client = llm_module.get_client()
        assert isinstance(client, LLMClient)
