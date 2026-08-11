from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RecentInterviewItem(BaseModel):
    id: str
    mode: str
    status: str
    question_count: int
    overall_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]


class ResumeHistoryItem(BaseModel):
    id: str
    original_filename: str
    status: str
    created_at: datetime


class Achievement(BaseModel):
    id: str
    label: str
    description: str
    unlocked: bool


class DashboardResponse(BaseModel):
    practice_count: int
    recent_interviews: list[RecentInterviewItem]
    resume_history: list[ResumeHistoryItem]
    current_skill_counts: dict[str, int]
    achievements: list[Achievement]
