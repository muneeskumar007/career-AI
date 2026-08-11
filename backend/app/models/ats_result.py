from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SkillsByCategory(BaseModel):
    programming_languages: list[str] = []
    frameworks: list[str] = []
    databases: list[str] = []
    cloud: list[str] = []
    soft_skills: list[str] = []
    certifications: list[str] = []


class ATSResultInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    resume_id: str
    job_description_id: str
    user_id: str
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
