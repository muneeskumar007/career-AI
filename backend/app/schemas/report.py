from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScoreCheck(BaseModel):
    label: str
    passed: bool


class PerformanceReportResponse(BaseModel):
    resume_id: Optional[str]
    interview_id: Optional[str]
    resume_score: Optional[float]
    resume_score_checks: list[ScoreCheck]
    ats_score: Optional[float]
    interview_score: Optional[float]
    communication_score: Optional[float]
    technical_score: Optional[float]
    confidence_score: Optional[float]
    strong_skills: list[str]
    weak_skills: list[str]
    recommendations: list[str]
    generated_at: datetime


class ProgressPoint(BaseModel):
    date: datetime
    interview_id: str
    interview_score: Optional[float]
    communication_score: Optional[float]
    technical_score: Optional[float]


class ProgressHistoryResponse(BaseModel):
    points: list[ProgressPoint]
