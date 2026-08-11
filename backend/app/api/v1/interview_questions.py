from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.providers.base import LLMProvider
from app.api.deps import get_current_user, get_db, get_llm_provider_dep
from app.schemas.common import SuccessResponse
from app.schemas.interview import GenerateQuestionsRequest, QuestionSetResponse
from app.schemas.user import UserResponse
from app.services.interview_question_service import InterviewQuestionService

router = APIRouter(prefix="/interview/questions", tags=["Interview Questions"])


@router.post("", response_model=SuccessResponse[QuestionSetResponse])
async def generate_questions(
    payload: GenerateQuestionsRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider_dep),
):
    service = InterviewQuestionService(db, llm_provider=llm_provider)
    result = await service.generate(current_user.id, payload)
    return SuccessResponse(message="Interview questions generated", data=result)
