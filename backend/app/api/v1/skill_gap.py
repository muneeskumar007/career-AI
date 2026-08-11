from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.schemas.common import SuccessResponse
from app.schemas.skill_gap import SkillGapResponse
from app.schemas.user import UserResponse
from app.services.job_description_service import JobDescriptionService
from app.services.resume_analysis_service import ResumeAnalysisService
from app.services.skill_gap_service import analyze_skill_gap

router = APIRouter(prefix="/skill-gap", tags=["Skill Gap Analysis"])


@router.get("/{resume_id}/{job_description_id}", response_model=SuccessResponse[SkillGapResponse])
async def get_skill_gap(
    resume_id: str,
    job_description_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    analysis_service = ResumeAnalysisService(db)
    jd_service = JobDescriptionService(db)

    analysis = await analysis_service.get_latest(resume_id, current_user.id)  # enforces resume ownership
    jd_doc = await jd_service.get_owned(job_description_id, current_user.id)

    result = analyze_skill_gap(analysis.skills.model_dump(), jd_doc["raw_text"])
    return SuccessResponse(
        data=SkillGapResponse(resume_id=resume_id, job_description_id=job_description_id, **result)
    )
