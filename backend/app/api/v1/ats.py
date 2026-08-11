from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.ats_result import ATSCompareRequest, ATSResultResponse
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse
from app.services.ats_service import ATSService

router = APIRouter(prefix="/ats", tags=["ATS Analysis"])


@router.post("/compare", response_model=SuccessResponse[ATSResultResponse])
async def compare_resume_to_jd(
    payload: ATSCompareRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ATSService(db)
    result = await service.compare(current_user.id, payload.resume_id, payload.job_description_id)
    return SuccessResponse(message="ATS comparison complete", data=result)


@router.get("/{resume_id}/{job_description_id}", response_model=SuccessResponse[ATSResultResponse])
async def get_ats_result(
    resume_id: str,
    job_description_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ATSService(db)
    result = await service.get(resume_id, job_description_id, current_user.id)
    return SuccessResponse(data=result)
