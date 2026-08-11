"""Scores a single interview answer. Same injectable-provider pattern as
every other AI-backed service here, for the same testing reason."""

import logging

from app.ai.prompts import EVALUATION_SCHEMA_HINT, EVALUATION_SYSTEM_PROMPT
from app.ai.providers.base import LLMProvider, LLMProviderError
from app.ai.providers.factory import get_llm_provider
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

REQUIRED_SCORE_KEYS = {"technical_accuracy", "completeness", "communication", "grammar", "problem_solving", "overall_score"}


class EvaluationError(AppException):
    status_code = 502
    message = "The AI evaluator is unavailable right now. Please try again shortly."


class AnswerEvaluatorService:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()

    async def evaluate(self, question: str, answer_text: str, resume_context: str) -> dict:
        prompt = (
            f"Candidate background:\n{resume_context}\n\n"
            f"Question asked: {question}\n\nCandidate's answer:\n{answer_text}\n\n"
            "Score this answer on each dimension (0-100) and give specific feedback."
        )
        try:
            raw = await self.llm_provider.generate_json(
                system_prompt=EVALUATION_SYSTEM_PROMPT, user_prompt=prompt, schema_hint=EVALUATION_SCHEMA_HINT
            )
        except LLMProviderError as exc:
            logger.error("Answer evaluation failed: %s", exc)
            raise EvaluationError() from exc

        if not REQUIRED_SCORE_KEYS.issubset(raw.keys()):
            raise EvaluationError("The AI response was missing expected score fields.")
        for key in REQUIRED_SCORE_KEYS:
            try:
                raw[key] = max(0.0, min(100.0, float(raw[key])))
            except (TypeError, ValueError):
                raise EvaluationError(f"The AI returned a non-numeric score for {key}.")
        return raw
