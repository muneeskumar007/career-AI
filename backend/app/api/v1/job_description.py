from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.common import SuccessResponse
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionResponse
from app.schemas.user import UserResponse
from app.services.job_description_service import JobDescriptionService

router = APIRouter(prefix="/job", tags=["Job Description"])


@router.post("", response_model=SuccessResponse[JobDescriptionResponse], status_code=201)
async def create_job_description(
    payload: JobDescriptionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = JobDescriptionService(db)
    result = await service.create(current_user.id, payload)
    return SuccessResponse(message="Job description saved", data=result)


@router.get("", response_model=SuccessResponse[list[JobDescriptionResponse]])
async def list_job_descriptions(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = JobDescriptionService(db)
    result = await service.list_for_user(current_user.id)
    return SuccessResponse(data=result)


@router.get("/{jd_id}", response_model=SuccessResponse[JobDescriptionResponse])
async def get_job_description(
    jd_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = JobDescriptionService(db)
    result = await service.get_response(jd_id, current_user.id)
    return SuccessResponse(data=result)
