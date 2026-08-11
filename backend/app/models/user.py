from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"  # future: recruiter-facing screening dashboard
    ADMIN = "admin"


class UserInDB(BaseModel):
    """Shape of a user document as stored in MongoDB.

    Distinct from schemas/user.py's UserResponse: this can carry sensitive
    fields (password_hash, reset tokens) that must never reach an API
    response.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.CANDIDATE
    is_active: bool = True
    is_verified: bool = False
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    reset_password_token_hash: Optional[str] = None
    reset_password_expires_at: Optional[datetime] = None
    refresh_token_version: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
