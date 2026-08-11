from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.ats_result import ATSResultResponse
from app.services.ats.ats_scorer import score_resume_against_jd
from app.services.job_description_service import JobDescriptionService
from app.services.resume_analysis_service import ResumeAnalysisService
from app.services.resume_service import ResumeService
from app.utils.exceptions import AppException


class ATSResultNotFoundException(AppException):
    status_code = 404
    message = "No ATS comparison found for this resume/job description pair — run POST /api/ats/compare first"


def _to_response(doc: dict) -> ATSResultResponse:
    return ATSResultResponse(
        id=str(doc["_id"]),
        resume_id=doc["resume_id"],
        job_description_id=doc["job_description_id"],
        ats_score=doc["ats_score"],
        skill_match_percent=doc["skill_match_percent"],
        semantic_similarity_percent=doc["semantic_similarity_percent"],
        matched_skills=doc["matched_skills"],
        missing_skills=doc["missing_skills"],
        missing_keywords=doc["missing_keywords"],
        strengths=doc["strengths"],
        weak_areas=doc["weak_areas"],
        formatting_suggestions=doc["formatting_suggestions"],
        project_suggestions=doc["project_suggestions"],
        certification_suggestions=doc["certification_suggestions"],
        experience_suggestions=doc["experience_suggestions"],
        created_at=doc["created_at"],
    )


class ATSService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.results = db.ats_results
        self.resume_service = ResumeService(db)
        self.analysis_service = ResumeAnalysisService(db)
        self.jd_service = JobDescriptionService(db)

    async def compare(self, user_id: str, resume_id: str, job_description_id: str) -> ATSResultResponse:
        resume_doc = await self.resume_service.get_owned(resume_id, user_id)
        jd_doc = await self.jd_service.get_owned(job_description_id, user_id)

        # Reuse an existing parse if there is one; otherwise parse now so
        # comparing doesn't force the caller to remember to call /parse first.
        try:
            analysis = await self.analysis_service.get_latest(resume_id, user_id)
            analysis_dict = analysis.model_dump()
        except Exception:
            analysis = await self.analysis_service.parse_and_store(resume_id, user_id)
            analysis_dict = analysis.model_dump()

        scored = score_resume_against_jd(analysis_dict, resume_doc["raw_text"], jd_doc["raw_text"])

        # Replace any prior comparison for this exact resume+JD pair rather than accumulating duplicates.
        await self.results.delete_many({"resume_id": resume_id, "job_description_id": job_description_id})

        doc = {
            "resume_id": resume_id,
            "job_description_id": job_description_id,
            "user_id": user_id,
            **scored,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.results.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_response(doc)

    async def get(self, resume_id: str, job_description_id: str, user_id: str) -> ATSResultResponse:
        await self.resume_service.get_owned(resume_id, user_id)
        doc = await self.results.find_one(
            {"resume_id": resume_id, "job_description_id": job_description_id, "user_id": user_id},
            sort=[("created_at", -1)],
        )
        if not doc:
            raise ATSResultNotFoundException()
        return _to_response(doc)
