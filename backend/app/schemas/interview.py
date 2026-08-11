from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.interview import InterviewMode, InterviewStatus, QuestionCategory


class GenerateQuestionsRequest(BaseModel):
    resume_id: str
    job_description_id: Optional[str] = None
    difficulty: str = Field(default="mid", pattern="^(entry|mid|senior)$")


class QuestionSetResponse(BaseModel):
    id: str
    resume_id: str
    job_description_id: Optional[str]
    hr_questions: list[str]
    technical_questions: list[str]
    project_questions: list[str]
    scenario_questions: list[str]
    behavioral_questions: list[str]
    coding_questions: list[str]
    created_at: datetime


class StartInterviewRequest(BaseModel):
    resume_id: str
    job_description_id: Optional[str] = None
    mode: InterviewMode


class InterviewResponse(BaseModel):
    id: str
    resume_id: str
    job_description_id: Optional[str]
    mode: InterviewMode
    status: InterviewStatus
    question_count: int
    created_at: datetime
    completed_at: Optional[datetime]


class CurrentQuestionResponse(BaseModel):
    interview_id: str
    question: str
    category: QuestionCategory
    question_number: int
    is_complete: bool = False


class SubmitAnswerRequest(BaseModel):
    question: str
    category: QuestionCategory
    answer_text: str = Field(min_length=1, max_length=10000)


class AnswerEvaluationResponse(BaseModel):
    id: str
    interview_id: str
    question: str
    category: QuestionCategory
    answer_text: str
    technical_accuracy: Optional[float]
    completeness: Optional[float]
    communication: Optional[float]
    grammar: Optional[float]
    problem_solving: Optional[float]
    overall_score: Optional[float]
    feedback: Optional[str]
    speech_analysis: Optional[dict] = None
    video_analysis: Optional[dict] = None
    created_at: datetime
