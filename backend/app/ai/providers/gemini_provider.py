"""
Gemini API provider. Uses Google's generative-language REST API directly
(no google-genai SDK dependency, to keep the footprint small) via httpx.

NOT LIVE-TESTED in this build — there is no API key available in the build
environment. The request/response shapes below match Gemini's documented
generateContent endpoint as of this writing; verify against
https://ai.google.dev/api/generate-content once you have a key, in case the
API has changed since. Structured-output mode (response_mime_type +
response_schema) is Gemini-specific and is why generate_json validates the
result rather than trusting the mime type alone.
"""

import json
import logging

import httpx

from app.ai.providers.base import LLMProvider, LLMProviderError
from app.config.settings import settings

logger = logging.getLogger(__name__)

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self.model = model or settings.GEMINI_MODEL
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise LLMProviderError("GEMINI_API_KEY is not set")

    async def _call(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        url = f"{API_BASE}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                **({"responseMimeType": "application/json"} if json_mode else {}),
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("Gemini API call failed: %s", exc)
                raise LLMProviderError(f"Gemini request failed: {exc}") from exc

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise LLMProviderError(f"Unexpected Gemini response shape: {data}") from exc

    async def generate_json(self, system_prompt: str, user_prompt: str, schema_hint: str) -> dict:
        full_prompt = f"{user_prompt}\n\nRespond with JSON matching this shape:\n{schema_hint}"
        raw = await self._call(system_prompt, full_prompt, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Gemini did not return valid JSON: {raw[:200]}") from exc

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return await self._call(system_prompt, user_prompt, json_mode=False)
