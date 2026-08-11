"""Generates ONE next question at a time, informed by the conversation so
far — this is what makes the interview 'adaptive' rather than a fixed
question list read out in order (that's what Module 7's QuestionGeneratorService
is for). Same injectable-provider pattern as the rest of the AI-backed services."""

import logging

from app.ai.prompts import NEXT_QUESTION_SCHEMA_HINT, build_next_question_prompt
from app.ai.providers.base import LLMProvider, LLMProviderError
from app.ai.providers.factory import get_llm_provider
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

INTERVIEWER_SYSTEM_PROMPT = (
    "You are conducting a live interview. Ask exactly one question at a time, "
    "grounded in the candidate's resume and (if provided) the job description. "
    "Adapt based on their previous answers — if an answer was strong, you can "
    "probe deeper or move to a new area; if it was thin, consider a clarifying "
    "follow-up. Never repeat a question already asked in this conversation."
)


class NextQuestionError(AppException):
    status_code = 502
    message = "The AI interviewer is unavailable right now. Please try again shortly."


class AdaptiveQuestionService:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()

    async def generate_next(self, resume_context: str, jd_context: str, history: list[dict]) -> dict:
        prompt = build_next_question_prompt(history, resume_context, jd_context)
        try:
            raw = await self.llm_provider.generate_json(
                system_prompt=INTERVIEWER_SYSTEM_PROMPT, user_prompt=prompt, schema_hint=NEXT_QUESTION_SCHEMA_HINT
            )
        except LLMProviderError as exc:
            logger.error("Next-question generation failed: %s", exc)
            raise NextQuestionError() from exc

        if "question" not in raw or "category" not in raw:
            raise NextQuestionError("The AI response was missing the question or category.")
        return raw
