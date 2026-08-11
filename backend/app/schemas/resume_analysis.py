from datetime import datetime

from pydantic import BaseModel

from app.models.resume_analysis import EducationEntry, ExperienceEntry, ProfileLinks, ProjectEntry, SkillsBreakdown


class ResumeAnalysisResponse(BaseModel):
    id: str
    resume_id: str
    skills: SkillsBreakdown
    links: ProfileLinks
    education: list[EducationEntry]
    experience: list[ExperienceEntry]
    projects: list[ProjectEntry]
    summary: str | None
    created_at: datetime
