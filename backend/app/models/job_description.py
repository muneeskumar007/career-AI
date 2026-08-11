from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class JobDescriptionInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    title: Optional[str] = None
    company: Optional[str] = None
    raw_text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
