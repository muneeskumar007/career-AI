"""
Ollama provider — talks to a local (or self-hosted) Ollama server. Free,
private, no per-token cost, but needs your own compute; quality depends
heavily on which local model you pull (llama3.1, qwen2.5, etc.).

NOT LIVE-TESTED in this build — there is no Ollama server reachable from the
sandbox this was built in. The /api/generate request/response shape matches
Ollama's documented API as of this writing (https://github.com/ollama/ollama/
blob/main/docs/api.md); if Ollama has changed its API since, this may need
small updates.
"""

import json
import logging

import httpx

from app.ai.providers.base import LLMProvider, LLMProviderError
from app.config.settings import settings

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")

    async def _call(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": 0.2},
            **({"format": "json"} if json_mode else {}),
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("Ollama call failed: %s", exc)
                raise LLMProviderError(
                    f"Ollama request failed — is `ollama serve` running at {self.base_url}? ({exc})"
                ) from exc

        data = resp.json()
        if "response" not in data:
            raise LLMProviderError(f"Unexpected Ollama response shape: {data}")
        return data["response"]

    async def generate_json(self, system_prompt: str, user_prompt: str, schema_hint: str) -> dict:
        full_prompt = f"{user_prompt}\n\nRespond with ONLY valid JSON matching this shape, no other text:\n{schema_hint}"
        raw = await self._call(system_prompt, full_prompt, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Ollama did not return valid JSON: {raw[:200]}") from exc

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return await self._call(system_prompt, user_prompt, json_mode=False)
