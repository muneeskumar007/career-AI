from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.config.settings import settings
from app.schemas.common import SuccessResponse
from app.schemas.resume import ResumeDetailResponse, ResumeListResponse, ResumeResponse
from app.schemas.user import UserResponse
from app.services.resume_service import ResumeService
from app.utils.file_validation import FileTooLargeException

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/upload", response_model=SuccessResponse[ResumeResponse], status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=422, detail="No filename provided")

    # Read fully before validating — we need real byte length, not the
    # client-declared Content-Length header, which can't be trusted.
    content = await file.read()
    # Cheap upfront guard so an absurdly large upload doesn't sit fully
    # buffered in memory before validate_upload() rejects it anyway.
    if len(content) > settings.max_upload_size_bytes:
        raise FileTooLargeException(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    service = ResumeService(db)
    resume = await service.upload(current_user.id, file.filename, content)
    return SuccessResponse(message="Resume uploaded and text extracted", data=resume)


@router.get("", response_model=SuccessResponse[ResumeListResponse])
async def list_resumes(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.list_for_user(current_user.id)
    return SuccessResponse(data=result)


@router.get("/{resume_id}", response_model=SuccessResponse[ResumeDetailResponse])
async def get_resume(
    resume_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ResumeService(db)
    result = await service.get_detail(resume_id, current_user.id)
    return SuccessResponse(data=result)


@router.delete("/{resume_id}", response_model=SuccessResponse[None])
async def delete_resume(
    resume_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = ResumeService(db)
    await service.delete(resume_id, current_user.id)
    return SuccessResponse(message="Resume deleted")
