from typing import Optional

from pydantic import BaseModel


class ResumeImprovementRequest(BaseModel):
    target_role: Optional[str] = None  # optional context, e.g. "Senior Backend Engineer"


class ImprovedEntry(BaseModel):
    original: str
    improved: str
    changes: str  # brief explanation of what changed and why


class ResumeImprovementResponse(BaseModel):
    improved_summary: Optional[str]
    improved_experience: list[ImprovedEntry]
    improved_projects: list[ImprovedEntry]
    grammar_fixes: list[str]
    general_suggestions: list[str]
