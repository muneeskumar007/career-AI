from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.providers.base import LLMProvider
from app.ai.providers.factory import get_llm_provider
from app.database.mongodb import get_database
from app.models.user import UserRole
from app.schemas.user import UserResponse
from app.utils.exceptions import ForbiddenException, InvalidTokenException, UserNotFoundException
from app.utils.jwt_handler import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIOMotorDatabase:
    return get_database()


async def get_llm_provider_dep() -> LLMProvider:
    """Routes depend on this rather than calling get_llm_provider() directly,
    the same reason routes depend on get_db() rather than importing the Mongo
    client directly — it's the seam tests override to inject a FakeLLMProvider."""
    return get_llm_provider()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> UserResponse:
    if credentials is None:
        raise InvalidTokenException("Not authenticated")

    payload = decode_token(credentials.credentials, expected_type="access")
    try:
        user_id = ObjectId(payload["sub"])
    except (InvalidId, TypeError):
        raise InvalidTokenException()

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise UserNotFoundException()
    if not user.get("is_active", True):
        raise ForbiddenException("This account has been deactivated")

    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"],
        is_verified=user["is_verified"],
        phone=user.get("phone"),
        avatar_url=user.get("avatar_url"),
        created_at=user["created_at"],
        last_login_at=user.get("last_login_at"),
    )


def require_roles(*allowed_roles: UserRole):
    """Usage: Depends(require_roles(UserRole.ADMIN))"""

    async def role_checker(
        current_user: Annotated[UserResponse, Depends(get_current_user)],
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise ForbiddenException("You do not have permission to perform this action")
        return current_user

    return role_checker
