from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.resume import BasicInfo, ResumeStatus


class ResumeResponse(BaseModel):
    id: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    basic_info: BasicInfo
    status: ResumeStatus
    created_at: datetime


class ResumeDetailResponse(ResumeResponse):
    raw_text: str


class ResumeListResponse(BaseModel):
    items: list[ResumeResponse]
    total: int
