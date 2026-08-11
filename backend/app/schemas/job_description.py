from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobDescriptionCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    company: Optional[str] = Field(default=None, max_length=200)
    raw_text: str = Field(min_length=20, max_length=20000)


class JobDescriptionResponse(BaseModel):
    id: str
    title: Optional[str]
    company: Optional[str]
    raw_text: str
    created_at: datetime
