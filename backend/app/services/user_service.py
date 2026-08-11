from datetime import datetime, timezone
from math import ceil

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserRole
from app.schemas.user import PaginatedUsers, UserProfileUpdate, UserResponse
from app.utils.exceptions import InvalidTokenException, UserNotFoundException


def _to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise InvalidTokenException("Invalid user id")


def _to_response(doc: dict) -> UserResponse:
    return UserResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        role=doc["role"],
        is_active=doc["is_active"],
        is_verified=doc["is_verified"],
        phone=doc.get("phone"),
        avatar_url=doc.get("avatar_url"),
        created_at=doc["created_at"],
        last_login_at=doc.get("last_login_at"),
    )


class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.users = db.users

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        user = await self.users.find_one({"_id": _to_object_id(user_id)})
        if not user:
            raise UserNotFoundException()
        return _to_response(user)

    async def update_profile(self, user_id: str, payload: UserProfileUpdate) -> UserResponse:
        updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        if updates:
            updates["updated_at"] = datetime.now(timezone.utc)
            await self.users.update_one({"_id": _to_object_id(user_id)}, {"$set": updates})
        return await self.get_user_by_id(user_id)

    async def list_users(self, page: int, page_size: int) -> PaginatedUsers:
        skip = (page - 1) * page_size
        total = await self.users.count_documents({})
        cursor = self.users.find().sort("created_at", -1).skip(skip).limit(page_size)
        items = [_to_response(doc) async for doc in cursor]
        return PaginatedUsers(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(ceil(total / page_size), 1) if total else 1,
        )

    async def update_role(self, user_id: str, role: UserRole) -> UserResponse:
        await self.users.update_one(
            {"_id": _to_object_id(user_id)},
            {"$set": {"role": role.value, "updated_at": datetime.now(timezone.utc)}},
        )
        return await self.get_user_by_id(user_id)

    async def update_status(self, user_id: str, is_active: bool) -> UserResponse:
        await self.users.update_one(
            {"_id": _to_object_id(user_id)},
            {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc)}},
        )
        return await self.get_user_by_id(user_id)
