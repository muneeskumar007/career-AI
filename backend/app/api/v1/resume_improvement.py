from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.providers.base import LLMProvider
from app.api.deps import get_current_user, get_db, get_llm_provider_dep
from app.schemas.common import SuccessResponse
from app.schemas.resume_improvement import ResumeImprovementRequest, ResumeImprovementResponse
from app.schemas.user import UserResponse
from app.services.resume_analysis_service import ResumeAnalysisService
from app.services.resume_improvement_service import ResumeImprovementService

router = APIRouter(prefix="/resume", tags=["Resume Improvement"])


@router.post("/{resume_id}/improve", response_model=SuccessResponse[ResumeImprovementResponse])
async def improve_resume(
    resume_id: str,
    payload: ResumeImprovementRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider_dep),
):
    analysis_service = ResumeAnalysisService(db)
    analysis = await analysis_service.get_latest(resume_id, current_user.id)  # enforces ownership

    service = ResumeImprovementService(llm_provider=llm_provider)
    result = await service.improve(analysis, payload)
    return SuccessResponse(message="Resume improvement suggestions generated", data=result)
