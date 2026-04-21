"""Multi-provider LLM factory used by every agent.

Providers auto-detected by model-name prefix:

    openai/ gpt- o1      -> OpenAI
    anthropic/ claude-   -> Anthropic
    gemini / google/     -> Google Generative AI
    hf/ huggingface/     -> HuggingFace Inference API (serverless)
    azure/               -> Azure OpenAI
    (anything else)      -> OpenRouter (default)

All providers accept the same ``get_llm(model=..., temperature=...)`` call
signature and return a LangChain BaseChatModel. Tool binding
(``llm.bind_tools``) works uniformly, so agents don't need to know which
backend is serving them.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-chat-v3-0324")

# Provider prefix → factory mapping. Longer prefixes first so 'azure/' wins
# before the generic openrouter fallback.
_PROVIDER_PREFIXES: dict[str, str] = {
    "azure/": "azure",
    "openai/": "openai",
    "gpt-": "openai",
    "o1": "openai",
    "anthropic/": "anthropic",
    "claude-": "anthropic",
    "gemini": "google",
    "google/": "google",
    "hf/": "huggingface",
    "huggingface/": "huggingface",
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

    Supported: OpenRouter (default), OpenAI, Anthropic, Google Gemini,
    HuggingFace Inference API, Azure OpenAI.

    Args:
        model: Model identifier. Provider auto-detected from prefix.
        temperature: Sampling temperature.
        provider: Force a specific provider, overriding prefix detection.
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
    elif provider == "azure":
        # Format: azure/<deployment-name>. Endpoint + API version come from env.
        clean_model = model.removeprefix("azure/")
        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        api_key = os.environ["AZURE_OPENAI_API_KEY"]
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        return AzureChatOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            azure_deployment=clean_model,
            temperature=temperature,
            **kwargs,
        )
    elif provider == "huggingface":
        clean_model = model.removeprefix("huggingface/").removeprefix("hf/")
        # Chat-tuned wrapper around the HF Inference API. Requires
        # HF_TOKEN in the environment.
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

        endpoint = HuggingFaceEndpoint(
            repo_id=clean_model,
            task="text-generation",
            max_new_tokens=int(os.getenv("HF_MAX_NEW_TOKENS", "512")),
            temperature=max(temperature, 0.01),  # HF rejects temperature==0
            huggingfacehub_api_token=os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGINGFACEHUB_API_TOKEN"),
            **kwargs,
        )
        return ChatHuggingFace(llm=endpoint, model_id=clean_model)
    else:  # openrouter (default)
        return ChatOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=os.environ["OPENROUTER_API_KEY"],
            model=model,
            temperature=temperature,
            **kwargs,
        )
