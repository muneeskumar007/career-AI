from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import DashboardResponse
from app.schemas.user import UserResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Candidate Dashboard"])


@router.get("", response_model=SuccessResponse[DashboardResponse])
async def get_dashboard(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = DashboardService(db)
    result = await service.get_dashboard(current_user.id)
    return SuccessResponse(data=result)
