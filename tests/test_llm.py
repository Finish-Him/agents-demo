"""Tests for shared/llm.py — provider auto-detection and LLM factory."""

import os
from unittest.mock import patch

import pytest

from shared.llm import _detect_provider, get_llm, OPENROUTER_BASE_URL


class TestDetectProvider:
    """Test provider detection from model name prefix."""

    @pytest.mark.parametrize(
        "model,expected",
        [
            ("gpt-4o-mini", "openai"),
            ("gpt-4o", "openai"),
            ("openai/gpt-4o", "openai"),
            ("o1", "openai"),
            ("claude-sonnet-4-20250514", "anthropic"),
            ("claude-3-opus-20240229", "anthropic"),
            ("anthropic/claude-3-haiku", "anthropic"),
            ("gemini-2.0-flash", "google"),
            ("google/gemini-pro", "google"),
            ("hf/Qwen/Qwen2.5-7B-Instruct", "huggingface"),
            ("huggingface/meta-llama/Llama-3.2-3B-Instruct", "huggingface"),
            ("azure/gpt-4o-deployment", "azure"),
            ("deepseek/deepseek-chat-v3-0324", "openrouter"),
            ("qwen/qwen3-235b-a22b", "openrouter"),
            ("meta-llama/llama-3-70b", "openrouter"),
            ("unknown-model", "openrouter"),
        ],
    )
    def test_detect_provider(self, model: str, expected: str):
        assert _detect_provider(model) == expected


class TestGetLLM:
    """Test get_llm() returns correct LLM class for each provider."""

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_openai_provider(self):
        from langchain_openai import ChatOpenAI
        llm = get_llm("gpt-4o-mini")
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4o-mini"

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_openai_strips_prefix(self):
        from langchain_openai import ChatOpenAI
        llm = get_llm("openai/gpt-4o")
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4o"

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_anthropic_provider(self):
        from langchain_anthropic import ChatAnthropic
        llm = get_llm("claude-sonnet-4-20250514")
        assert isinstance(llm, ChatAnthropic)

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_google_provider(self):
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = get_llm("gemini-2.0-flash")
        assert isinstance(llm, ChatGoogleGenerativeAI)

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_openrouter_provider(self):
        from langchain_openai import ChatOpenAI
        llm = get_llm("qwen/qwen3-235b-a22b")
        assert isinstance(llm, ChatOpenAI)
        assert str(llm.openai_api_base) == OPENROUTER_BASE_URL or OPENROUTER_BASE_URL in str(getattr(llm, 'openai_api_base', '') or getattr(llm, 'base_url', ''))

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_forced_provider(self):
        from langchain_anthropic import ChatAnthropic
        llm = get_llm("gpt-4o-mini", provider="anthropic")
        assert isinstance(llm, ChatAnthropic)

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_default_model_used(self):
        llm = get_llm()
        assert llm is not None

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "sk-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
    })
    def test_temperature_passed(self):
        llm = get_llm("gpt-4o-mini", temperature=0.7)
        assert llm.temperature == 0.7

    @patch.dict(os.environ, {
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-azure-key",
        "AZURE_OPENAI_API_VERSION": "2024-08-01-preview",
    })
    def test_azure_provider(self):
        from langchain_openai import AzureChatOpenAI
        llm = get_llm("azure/gpt-4o-deployment")
        assert isinstance(llm, AzureChatOpenAI)

    @patch.dict(os.environ, {"HF_TOKEN": "hf_test_token"})
    def test_huggingface_provider(self):
        from langchain_huggingface import ChatHuggingFace
        llm = get_llm("hf/Qwen/Qwen2.5-7B-Instruct", temperature=0.5)
        assert isinstance(llm, ChatHuggingFace)
