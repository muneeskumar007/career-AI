from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db, require_roles
from app.models.user import UserRole
from app.schemas.common import SuccessResponse
from app.schemas.user import PaginatedUsers, UserResponse, UserRoleUpdate, UserStatusUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users (Admin)"])

admin_only = require_roles(UserRole.ADMIN)


@router.get("", response_model=SuccessResponse[PaginatedUsers])
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: UserResponse = Depends(admin_only),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = UserService(db)
    result = await service.list_users(page, page_size)
    return SuccessResponse(data=result)


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: str, _: UserResponse = Depends(admin_only), db: AsyncIOMotorDatabase = Depends(get_db)
):
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    return SuccessResponse(data=user)


@router.patch("/{user_id}/role", response_model=SuccessResponse[UserResponse])
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    _: UserResponse = Depends(admin_only),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = UserService(db)
    user = await service.update_role(user_id, payload.role)
    return SuccessResponse(message="User role updated", data=user)


@router.patch("/{user_id}/status", response_model=SuccessResponse[UserResponse])
async def update_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    _: UserResponse = Depends(admin_only),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = UserService(db)
    user = await service.update_status(user_id, payload.is_active)
    return SuccessResponse(message="User status updated", data=user)
