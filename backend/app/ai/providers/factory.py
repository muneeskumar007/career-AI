from functools import lru_cache

from app.ai.providers.base import LLMProvider
from app.config.settings import settings


@lru_cache
def get_llm_provider() -> LLMProvider:
    """The one place that knows which provider is active. Everything else
    in the app depends on LLMProvider, never on a concrete provider class."""
    if settings.LLM_PROVIDER == "gemini":
        from app.ai.providers.gemini_provider import GeminiProvider

        return GeminiProvider()
    if settings.LLM_PROVIDER == "ollama":
        from app.ai.providers.ollama_provider import OllamaProvider

        return OllamaProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER!r} (expected 'gemini' or 'ollama')")
