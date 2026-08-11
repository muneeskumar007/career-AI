from datetime import datetime

from pydantic import BaseModel

from app.models.ats_result import SkillsByCategory


class ATSCompareRequest(BaseModel):
    resume_id: str
    job_description_id: str


class ATSResultResponse(BaseModel):
    id: str
    resume_id: str
    job_description_id: str
    ats_score: float
    skill_match_percent: float
    semantic_similarity_percent: float
    matched_skills: SkillsByCategory
    missing_skills: SkillsByCategory
    missing_keywords: list[str]
    strengths: list[str]
    weak_areas: list[str]
    formatting_suggestions: list[str]
    project_suggestions: list[str]
    certification_suggestions: list[str]
    experience_suggestions: list[str]
    created_at: datetime
