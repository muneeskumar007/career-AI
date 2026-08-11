from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.auth import ChangePasswordRequest
from app.schemas.common import SuccessResponse
from app.schemas.user import UserProfileUpdate, UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    return SuccessResponse(data=current_user)


@router.put("/me", response_model=SuccessResponse[UserResponse])
async def update_my_profile(
    payload: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = UserService(db)
    updated = await service.update_profile(current_user.id, payload)
    return SuccessResponse(message="Profile updated successfully", data=updated)


@router.post("/change-password", response_model=SuccessResponse[None])
async def change_password(
    payload: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = AuthService(db)
    await service.change_password(current_user.id, payload.current_password, payload.new_password)
    return SuccessResponse(message="Password changed successfully")
