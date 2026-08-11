from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.providers.base import LLMProvider
from app.schemas.interview import GenerateQuestionsRequest, QuestionSetResponse
from app.services.interview.question_generator import QuestionGeneratorService
from app.services.job_description_service import JobDescriptionService
from app.services.parsing.context_builder import build_resume_context
from app.services.resume_analysis_service import ResumeAnalysisService


def _to_response(doc: dict) -> QuestionSetResponse:
    return QuestionSetResponse(
        id=str(doc["_id"]), resume_id=doc["resume_id"], job_description_id=doc.get("job_description_id"),
        hr_questions=doc["hr_questions"], technical_questions=doc["technical_questions"],
        project_questions=doc["project_questions"], scenario_questions=doc["scenario_questions"],
        behavioral_questions=doc["behavioral_questions"], coding_questions=doc["coding_questions"],
        created_at=doc["created_at"],
    )


class InterviewQuestionService:
    def __init__(self, db: AsyncIOMotorDatabase, llm_provider: LLMProvider | None = None):
        self.db = db
        self.question_sets = db.interview_questions
        self.analysis_service = ResumeAnalysisService(db)
        self.jd_service = JobDescriptionService(db)
        self.generator = QuestionGeneratorService(llm_provider=llm_provider)

    async def generate(self, user_id: str, payload: GenerateQuestionsRequest) -> QuestionSetResponse:
        analysis = await self.analysis_service.get_latest(payload.resume_id, user_id)
        resume_context = build_resume_context(analysis)

        jd_context = ""
        if payload.job_description_id:
            jd_doc = await self.jd_service.get_owned(payload.job_description_id, user_id)
            jd_context = jd_doc["raw_text"]

        generated = await self.generator.generate(resume_context, jd_context, role="candidate", difficulty=payload.difficulty)

        doc = {
            "resume_id": payload.resume_id,
            "job_description_id": payload.job_description_id,
            "user_id": user_id,
            **generated,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.question_sets.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_response(doc)
