"""Module 7: generates a full question set (HR/technical/project/scenario/
behavioral/coding) from resume + JD context in one LLM call. Same injectable-
provider pattern as resume_improvement_service.py for the same testing reason."""

import logging

from app.ai.prompts import INTERVIEW_QUESTION_SCHEMA_HINT, INTERVIEW_QUESTION_SYSTEM_PROMPT
from app.ai.providers.base import LLMProvider, LLMProviderError
from app.ai.providers.factory import get_llm_provider
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

DIFFICULTY_GUIDANCE = {
    "entry": "Keep questions appropriate for an entry-level candidate — fundamentals over edge cases.",
    "mid": "Aim for mid-level depth — expect solid fundamentals plus some real-world judgment.",
    "senior": "Probe for senior-level judgment — tradeoffs, system design thinking, mentorship, ambiguity.",
}


class QuestionGenerationError(AppException):
    status_code = 502
    message = "The AI question generator is unavailable right now. Please try again shortly."


def _build_prompt(resume_context: str, jd_context: str, role: str, difficulty: str) -> str:
    return (
        f"Candidate's resume summary:\n{resume_context}\n\n"
        f"Target job description:\n{jd_context or '(no specific job description provided — ask general questions for a ' + role + ' role)'}\n\n"
        f"Difficulty level: {difficulty}. {DIFFICULTY_GUIDANCE.get(difficulty, '')}\n\n"
        "Generate 3-5 questions in each category (HR, technical, project-specific based on "
        "their actual projects, scenario/situational, behavioral, and coding). Ground the "
        "technical and project questions in the specific skills and projects mentioned above "
        "rather than asking generic questions."
    )


class QuestionGeneratorService:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()

    async def generate(self, resume_context: str, jd_context: str, role: str, difficulty: str) -> dict:
        prompt = _build_prompt(resume_context, jd_context, role, difficulty)
        try:
            raw = await self.llm_provider.generate_json(
                system_prompt=INTERVIEW_QUESTION_SYSTEM_PROMPT,
                user_prompt=prompt,
                schema_hint=INTERVIEW_QUESTION_SCHEMA_HINT,
            )
        except LLMProviderError as exc:
            logger.error("Question generation LLM call failed: %s", exc)
            raise QuestionGenerationError() from exc

        required_keys = {
            "hr_questions", "technical_questions", "project_questions",
            "scenario_questions", "behavioral_questions", "coding_questions",
        }
        if not required_keys.issubset(raw.keys()):
            raise QuestionGenerationError("The AI response was missing expected question categories.")
        return raw
