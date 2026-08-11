from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool


class PaginatedUsers(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
