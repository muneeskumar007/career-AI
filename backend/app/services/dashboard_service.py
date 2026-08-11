from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.dashboard import Achievement, DashboardResponse, RecentInterviewItem, ResumeHistoryItem
from app.services.achievements import compute_achievements
from app.services.report.resume_score import compute_resume_completeness_score

RECENT_LIMIT = 10


class DashboardService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_dashboard(self, user_id: str) -> DashboardResponse:
        interviews_cursor = self.db.interviews.find({"user_id": user_id}).sort("created_at", -1).limit(RECENT_LIMIT)
        recent_interviews = []
        async for interview in interviews_cursor:
            answers = [a async for a in self.db.interview_answers.find({"interview_id": str(interview["_id"])})]
            scores = [a["overall_score"] for a in answers if a.get("overall_score") is not None]
            recent_interviews.append(
                RecentInterviewItem(
                    id=str(interview["_id"]), mode=interview["mode"], status=interview["status"],
                    question_count=interview["question_count"],
                    overall_score=round(sum(scores) / len(scores), 1) if scores else None,
                    created_at=interview["created_at"], completed_at=interview.get("completed_at"),
                )
            )

        resumes_cursor = self.db.resumes.find({"user_id": user_id}).sort("created_at", -1).limit(RECENT_LIMIT)
        resume_history = [
            ResumeHistoryItem(id=str(r["_id"]), original_filename=r["original_filename"], status=r["status"], created_at=r["created_at"])
            async for r in resumes_cursor
        ]

        latest_analysis = await self.db.resume_analysis.find_one(
            {"user_id": user_id, "job_description_id": None}, sort=[("created_at", -1)]
        )
        current_skill_counts = {}
        if latest_analysis:
            current_skill_counts = {category: len(skills) for category, skills in latest_analysis.get("skills", {}).items()}

        stats = await self._aggregate_stats(user_id)
        achievements = [Achievement(**a) for a in compute_achievements(stats)]

        return DashboardResponse(
            practice_count=stats["completed_interview_count"],
            recent_interviews=recent_interviews,
            resume_history=resume_history,
            current_skill_counts=current_skill_counts,
            achievements=achievements,
        )

    async def _aggregate_stats(self, user_id: str) -> dict:
        resume_count = await self.db.resumes.count_documents({"user_id": user_id})
        completed_interview_count = await self.db.interviews.count_documents({"user_id": user_id, "status": "completed"})
        ats_comparison_count = await self.db.ats_results.count_documents({"user_id": user_id})

        best_resume_score = None
        async for analysis in self.db.resume_analysis.find({"user_id": user_id, "job_description_id": None}):
            score = compute_resume_completeness_score(analysis)["score"]
            best_resume_score = score if best_resume_score is None else max(best_resume_score, score)

        best_interview_score = None
        async for interview in self.db.interviews.find({"user_id": user_id, "status": "completed"}):
            answers = [a async for a in self.db.interview_answers.find({"interview_id": str(interview["_id"])})]
            scores = [a["overall_score"] for a in answers if a.get("overall_score") is not None]
            if scores:
                avg = sum(scores) / len(scores)
                best_interview_score = avg if best_interview_score is None else max(best_interview_score, avg)

        return {
            "resume_count": resume_count,
            "completed_interview_count": completed_interview_count,
            "ats_comparison_count": ats_comparison_count,
            "best_resume_score": best_resume_score,
            "best_interview_score": best_interview_score,
        }
