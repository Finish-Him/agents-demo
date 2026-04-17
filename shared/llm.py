import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-chat-v3-0324")

# Provider prefix → factory mapping
_PROVIDER_PREFIXES = {
    "openai/": "openai",
    "gpt-": "openai",
    "o1": "openai",
    "anthropic/": "anthropic",
    "claude-": "anthropic",
    "gemini": "google",
    "google/": "google",
}


def _detect_provider(model: str) -> str:
    """Detect LLM provider from model name prefix."""
    model_lower = model.lower()
    for prefix, provider in _PROVIDER_PREFIXES.items():
        if model_lower.startswith(prefix):
            return provider
    return "openrouter"  # default fallback


def get_llm(
    model: str | None = None,
    temperature: float = 0.0,
    provider: str | None = None,
    **kwargs,
):
    """Create an LLM instance, auto-detecting provider from model name.

    Supports: OpenRouter (default), OpenAI, Anthropic, Google Gemini.

    Args:
        model: Model identifier. Provider auto-detected from prefix.
        temperature: Sampling temperature.
        provider: Force a specific provider ('openrouter', 'openai', 'anthropic', 'google').
    """
    model = model or DEFAULT_MODEL
    provider = provider or _detect_provider(model)

    if provider == "openai":
        clean_model = model.removeprefix("openai/")
        return ChatOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            model=clean_model,
            temperature=temperature,
            **kwargs,
        )
    elif provider == "anthropic":
        clean_model = model.removeprefix("anthropic/")
        return ChatAnthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model_name=clean_model,
            temperature=temperature,
            max_tokens=4096,
            **kwargs,
        )
    elif provider == "google":
        clean_model = model.removeprefix("google/")
        return ChatGoogleGenerativeAI(
            google_api_key=os.environ["GOOGLE_API_KEY"],
            model=clean_model,
            temperature=temperature,
            **kwargs,
        )
    else:  # openrouter (default)
        return ChatOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=os.environ["OPENROUTER_API_KEY"],
            model=model,
            temperature=temperature,
            **kwargs,
        )
