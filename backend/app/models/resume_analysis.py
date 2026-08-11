from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SkillsBreakdown(BaseModel):
    programming_languages: list[str] = []
    frameworks: list[str] = []
    databases: list[str] = []
    cloud: list[str] = []
    soft_skills: list[str] = []
    certifications: list[str] = []


class ProfileLinks(BaseModel):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    duration: Optional[str] = None
    raw_text: str


class ExperienceEntry(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class ProjectEntry(BaseModel):
    name: str
    description: Optional[str] = None


class ResumeAnalysisInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    resume_id: str
    user_id: str
    job_description_id: Optional[str] = None  # set once Module 4 runs a JD comparison against this
    skills: SkillsBreakdown
    links: ProfileLinks
    education: list[EducationEntry] = []
    experience: list[ExperienceEntry] = []
    projects: list[ProjectEntry] = []
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
