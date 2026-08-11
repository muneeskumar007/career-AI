"""
Every LLM call in CareerAI goes through this interface, never through a
provider SDK directly from a route or service. That's the entire point of
the abstraction: swapping Gemini for Ollama (or adding a third provider
later) is a one-line env var change, not a code change anywhere else.
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProviderError(Exception):
    """Raised for any provider failure (network, auth, rate limit, bad response)."""


class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, system_prompt: str, user_prompt: str, schema_hint: str) -> dict[str, Any]:
        """Return a parsed JSON object. schema_hint is a plain-English description
        of the expected shape, included in the prompt — callers still validate
        the result against a Pydantic schema; this is not a substitute for that."""
        ...

    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Free-form text generation (e.g. a rewritten bullet point)."""
        ...
