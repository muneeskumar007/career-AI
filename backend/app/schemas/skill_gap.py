from typing import Optional

from pydantic import BaseModel


class KnownSkill(BaseModel):
    skill: str
    category: str


class SkillGapItem(BaseModel):
    skill: str
    category: str
    priority: str  # "High" | "Medium"
    difficulty: str  # "Beginner" | "Intermediate" | "Advanced"
    recommended_resource: Optional[str]
    estimated_learning_time: str


class SkillGapResponse(BaseModel):
    resume_id: str
    job_description_id: str
    known_skills: list[KnownSkill]
    missing_skills: list[SkillGapItem]
