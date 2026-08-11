from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.resume import ResumeStatus
from app.schemas.resume_analysis import ResumeAnalysisResponse
from app.services.parsing.resume_parser import parse_resume
from app.services.resume_service import ResumeService
from app.utils.exceptions import AppException


class AnalysisNotFoundException(AppException):
    status_code = 404
    message = "This resume hasn't been parsed yet — call POST /api/resume/{id}/parse first"


def _to_response(doc: dict) -> ResumeAnalysisResponse:
    return ResumeAnalysisResponse(
        id=str(doc["_id"]),
        resume_id=doc["resume_id"],
        skills=doc["skills"],
        links=doc["links"],
        education=doc["education"],
        experience=doc["experience"],
        projects=doc["projects"],
        summary=doc.get("summary"),
        created_at=doc["created_at"],
    )


class ResumeAnalysisService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.analyses = db.resume_analysis
        self.resumes = db.resumes
        self.resume_service = ResumeService(db)

    async def parse_and_store(self, resume_id: str, user_id: str) -> ResumeAnalysisResponse:
        resume_doc = await self.resume_service.get_owned(resume_id, user_id)
        parsed = parse_resume(resume_doc["raw_text"])

        # Re-parsing (e.g. after a resume edit) replaces the prior standalone
        # analysis rather than accumulating duplicates. JD-linked analyses
        # (job_description_id set, from Module 4) are untouched.
        await self.analyses.delete_many({"resume_id": resume_id, "job_description_id": None})

        doc = {
            "resume_id": resume_id,
            "user_id": user_id,
            "job_description_id": None,
            "skills": parsed["skills"],
            "links": parsed["links"],
            "education": parsed["education"],
            "experience": parsed["experience"],
            "projects": parsed["projects"],
            "summary": parsed["summary"],
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.analyses.insert_one(doc)
        doc["_id"] = result.inserted_id

        await self.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {"$set": {"status": ResumeStatus.PARSED.value, "updated_at": datetime.now(timezone.utc)}},
        )
        return _to_response(doc)

    async def get_latest(self, resume_id: str, user_id: str) -> ResumeAnalysisResponse:
        await self.resume_service.get_owned(resume_id, user_id)  # enforces ownership
        doc = await self.analyses.find_one(
            {"resume_id": resume_id, "job_description_id": None}, sort=[("created_at", -1)]
        )
        if not doc:
            raise AnalysisNotFoundException()
        return _to_response(doc)
