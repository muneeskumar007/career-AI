from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.common import SuccessResponse
from app.schemas.resume_analysis import ResumeAnalysisResponse
from app.schemas.user import UserResponse
from app.services.resume_analysis_service import ResumeAnalysisService

router = APIRouter(prefix="/resume", tags=["Resume Parser"])


@router.post("/{resume_id}/parse", response_model=SuccessResponse[ResumeAnalysisResponse])
async def parse_resume_endpoint(
    resume_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ResumeAnalysisService(db)
    result = await service.parse_and_store(resume_id, current_user.id)
    return SuccessResponse(message="Resume parsed", data=result)


@router.get("/{resume_id}/analysis", response_model=SuccessResponse[ResumeAnalysisResponse])
async def get_resume_analysis(
    resume_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ResumeAnalysisService(db)
    result = await service.get_latest(resume_id, current_user.id)
    return SuccessResponse(data=result)
