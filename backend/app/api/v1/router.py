from fastapi import APIRouter

from app.api.v1 import (
    ats,
    auth,
    dashboard,
    interview_questions,
    interviews,
    job_description,
    profile,
    reports,
    resume,
    resume_analysis,
    resume_improvement,
    skill_gap,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(users.router)
api_router.include_router(resume.router)
api_router.include_router(resume_analysis.router)
api_router.include_router(job_description.router)
api_router.include_router(ats.router)
api_router.include_router(skill_gap.router)
api_router.include_router(resume_improvement.router)
api_router.include_router(interview_questions.router)
api_router.include_router(interviews.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
