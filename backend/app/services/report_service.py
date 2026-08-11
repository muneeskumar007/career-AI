"""
Module 12: pulls together everything computed by Modules 3, 4, 8-11 into one
dashboard view. Deliberately computed on demand from the underlying
collections (resumes, resume_analysis, ats_results, interviews,
interview_answers) rather than a separately-maintained snapshot — those are
already timestamped and queryable, so a stored duplicate would just be
another thing to keep in sync and risk going stale.
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.report import PerformanceReportResponse, ProgressHistoryResponse, ProgressPoint, ScoreCheck
from app.services.report.resume_score import compute_resume_completeness_score
from app.utils.exceptions import AppException, ForbiddenException, InvalidTokenException


class NoDataForReportException(AppException):
    status_code = 404
    message = "Not enough data yet to generate a report — upload and parse a resume first"


def _to_object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise InvalidTokenException("Invalid id")


def _avg(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 1) if clean else None


class ReportService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def _latest_resume_and_analysis(self, user_id: str, resume_id: str | None) -> tuple[dict | None, dict | None]:
        query = {"user_id": user_id}
        if resume_id:
            resume = await self.db.resumes.find_one({"_id": _to_object_id(resume_id), "user_id": user_id})
        else:
            resume = await self.db.resumes.find_one(query, sort=[("created_at", -1)])
        if not resume:
            return None, None

        analysis = await self.db.resume_analysis.find_one(
            {"resume_id": str(resume["_id"]), "job_description_id": None}, sort=[("created_at", -1)]
        )
        return resume, analysis

    async def _latest_ats_result(self, user_id: str, resume_id: str | None) -> dict | None:
        query = {"user_id": user_id}
        if resume_id:
            query["resume_id"] = resume_id
        return await self.db.ats_results.find_one(query, sort=[("created_at", -1)])

    async def _interview_scores(self, user_id: str, interview_id: str | None) -> tuple[dict | None, list[dict]]:
        if interview_id:
            interview = await self.db.interviews.find_one({"_id": _to_object_id(interview_id), "user_id": user_id})
        else:
            interview = await self.db.interviews.find_one({"user_id": user_id}, sort=[("created_at", -1)])
        if not interview:
            return None, []

        cursor = self.db.interview_answers.find({"interview_id": str(interview["_id"])})
        answers = [a async for a in cursor]
        return interview, answers

    async def generate(self, user_id: str, resume_id: str | None = None, interview_id: str | None = None) -> PerformanceReportResponse:
        resume, analysis = await self._latest_resume_and_analysis(user_id, resume_id)
        if not resume:
            raise NoDataForReportException()

        resume_score, resume_checks = None, []
        strong_skills, weak_skills = [], []
        if analysis:
            completeness = compute_resume_completeness_score(analysis)
            resume_score = completeness["score"]
            resume_checks = [ScoreCheck(**c) for c in completeness["checks"]]
            strong_skills = [s for cat in analysis.get("skills", {}).values() for s in cat]

        ats_result = await self._latest_ats_result(user_id, resume_id or (str(resume["_id"]) if resume else None))
        ats_score = ats_result["ats_score"] if ats_result else None
        if ats_result:
            weak_skills = [s for cat in ats_result.get("missing_skills", {}).values() for s in cat]

        interview, answers = await self._interview_scores(user_id, interview_id)
        interview_score = _avg([a.get("overall_score") for a in answers])
        technical_score = _avg([a.get("technical_accuracy") for a in answers])
        grammar_score = _avg([a.get("grammar") for a in answers])

        # Communication/confidence blend text-eval scores with speech/video
        # signals when the interview used voice/video mode.
        communication_candidates = [a.get("communication") for a in answers]
        communication_candidates += [
            a["speech_analysis"]["communication_score"] for a in answers if a.get("speech_analysis")
        ]
        communication_score = _avg(communication_candidates)

        confidence_candidates = [
            a["speech_analysis"]["confidence_score"] for a in answers if a.get("speech_analysis")
        ]
        confidence_candidates += [
            a["video_analysis"]["confidence_score"]
            for a in answers
            if a.get("video_analysis") and a["video_analysis"].get("confidence_score") is not None
        ]
        confidence_score = _avg(confidence_candidates)

        recommendations = []
        if ats_result:
            recommendations.extend(ats_result.get("formatting_suggestions", [])[:2])
            recommendations.extend(ats_result.get("weak_areas", [])[:2])
        if resume_checks:
            recommendations.extend(f"Resume: {c.label.lower()}" for c in resume_checks if not c.passed)
        if technical_score is not None and technical_score < 60:
            recommendations.append("Interview: technical answers scored low on average — review core concepts for this role")
        if grammar_score is not None and grammar_score < 70:
            recommendations.append("Interview: grammar/clarity scored low — practice structuring answers before speaking")

        return PerformanceReportResponse(
            resume_id=str(resume["_id"]) if resume else None,
            interview_id=str(interview["_id"]) if interview else None,
            resume_score=resume_score, resume_score_checks=resume_checks, ats_score=ats_score,
            interview_score=interview_score, communication_score=communication_score,
            technical_score=technical_score, confidence_score=confidence_score,
            strong_skills=sorted(set(strong_skills))[:20], weak_skills=sorted(set(weak_skills))[:20],
            recommendations=recommendations[:8],
            generated_at=datetime.now(timezone.utc),
        )

    async def progress_history(self, user_id: str) -> ProgressHistoryResponse:
        cursor = self.db.interviews.find({"user_id": user_id, "status": "completed"}).sort("completed_at", 1)
        points = []
        async for interview in cursor:
            answers = [a async for a in self.db.interview_answers.find({"interview_id": str(interview["_id"])})]
            points.append(
                ProgressPoint(
                    date=interview["completed_at"],
                    interview_id=str(interview["_id"]),
                    interview_score=_avg([a.get("overall_score") for a in answers]),
                    communication_score=_avg([a.get("communication") for a in answers]),
                    technical_score=_avg([a.get("technical_accuracy") for a in answers]),
                )
            )
        return ProgressHistoryResponse(points=points)
