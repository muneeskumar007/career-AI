"""
Module 6: LLM-based resume rewriting. The LLM provider is injected
(constructor parameter, defaulting to the configured real one) specifically
so tests can substitute a FakeLLMProvider and verify the full request-
building → call → response-validation → error-handling flow without a real
API key. What can't be tested this way is whether the *rewritten text is
actually good* — that's a live-LLM judgment call, documented as such in the
README rather than glossed over.
"""

import json
import logging

from app.ai.prompts import RESUME_IMPROVEMENT_SCHEMA_HINT, RESUME_IMPROVEMENT_SYSTEM_PROMPT
from app.ai.providers.base import LLMProvider, LLMProviderError
from app.ai.providers.factory import get_llm_provider
from app.schemas.resume_analysis import ResumeAnalysisResponse
from app.schemas.resume_improvement import ResumeImprovementRequest, ResumeImprovementResponse
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)


class ResumeImprovementError(AppException):
    status_code = 502
    message = "The AI rewriting service is unavailable right now. Please try again shortly."


def _build_user_prompt(analysis: ResumeAnalysisResponse, target_role: str | None) -> str:
    experience_text = "\n".join(
        f"- {e.title or '(untitled role)'} at {e.company or '(unknown company)'}: {e.description or '(no description provided)'}"
        for e in analysis.experience
    ) or "(no experience entries provided)"
    projects_text = "\n".join(f"- {p.name}: {p.description or '(no description provided)'}" for p in analysis.projects) or "(no projects provided)"

    role_context = f"\nThe candidate is targeting this role: {target_role}" if target_role else ""

    return (
        f"Current summary:\n{analysis.summary or '(none provided)'}\n\n"
        f"Current experience entries:\n{experience_text}\n\n"
        f"Current projects:\n{projects_text}\n{role_context}\n\n"
        "Rewrite the summary, each experience entry, and each project description to be "
        "stronger and more specific, using only the facts already given. Also list any "
        "grammar issues you noticed and any general suggestions."
    )


class ResumeImprovementService:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()

    async def improve(
        self, analysis: ResumeAnalysisResponse, payload: ResumeImprovementRequest
    ) -> ResumeImprovementResponse:
        user_prompt = _build_user_prompt(analysis, payload.target_role)
        try:
            raw = await self.llm_provider.generate_json(
                system_prompt=RESUME_IMPROVEMENT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema_hint=RESUME_IMPROVEMENT_SCHEMA_HINT,
            )
        except LLMProviderError as exc:
            logger.error("Resume improvement LLM call failed: %s", exc)
            raise ResumeImprovementError() from exc

        try:
            return ResumeImprovementResponse.model_validate(raw)
        except Exception as exc:
            logger.error("LLM response failed schema validation: %s | raw=%s", exc, json.dumps(raw)[:500])
            raise ResumeImprovementError("The AI response was malformed. Please try again.") from exc
