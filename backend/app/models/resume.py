from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ResumeStatus(str, Enum):
    UPLOADED = "uploaded"       # stored + raw text extracted
    PARSED = "parsed"           # Module 3 structured parse completed
    FAILED = "failed"


class BasicInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ResumeInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    original_filename: str
    storage_key: str
    file_type: str  # "pdf" | "docx"
    file_size_bytes: int
    raw_text: str
    basic_info: BasicInfo
    status: ResumeStatus = ResumeStatus.UPLOADED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
