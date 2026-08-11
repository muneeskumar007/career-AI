from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InterviewMode(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    VIDEO = "video"


class InterviewStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuestionCategory(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"
    PROJECT = "project"
    SCENARIO = "scenario"
    BEHAVIORAL = "behavioral"
    CODING = "coding"


class InterviewQuestionSetInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    resume_id: str
    job_description_id: Optional[str] = None
    user_id: str
    hr_questions: list[str] = []
    technical_questions: list[str] = []
    project_questions: list[str] = []
    scenario_questions: list[str] = []
    behavioral_questions: list[str] = []
    coding_questions: list[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InterviewInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    resume_id: str
    job_description_id: Optional[str] = None
    mode: InterviewMode
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    question_count: int = 0
    current_question: Optional[str] = None
    current_category: Optional[QuestionCategory] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class InterviewAnswerInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    interview_id: str
    user_id: str
    question: str
    category: QuestionCategory
    answer_text: str
    technical_accuracy: Optional[float] = None
    completeness: Optional[float] = None
    communication: Optional[float] = None
    grammar: Optional[float] = None
    problem_solving: Optional[float] = None
    overall_score: Optional[float] = None
    feedback: Optional[str] = None
    # Populated only for voice/video answers (Modules 9-10) — None for text mode
    speech_analysis: Optional[dict] = None
    video_analysis: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
