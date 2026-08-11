from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.providers.base import LLMProvider
from app.api.deps import get_current_user, get_db, get_llm_provider_dep
from app.config.settings import settings
from app.models.interview import QuestionCategory
from app.schemas.common import SuccessResponse
from app.schemas.interview import (
    AnswerEvaluationResponse,
    CurrentQuestionResponse,
    InterviewResponse,
    StartInterviewRequest,
    SubmitAnswerRequest,
)
from app.schemas.user import UserResponse
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["AI Interview"])


@router.post("/start", response_model=SuccessResponse[CurrentQuestionResponse], status_code=201)
async def start_interview(
    payload: StartInterviewRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider_dep),
):
    service = InterviewService(db, llm_provider=llm_provider)
    result = await service.start(current_user.id, payload)
    return SuccessResponse(message="Interview started", data=result)


@router.get("", response_model=SuccessResponse[list[InterviewResponse]])
async def list_interviews(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = InterviewService(db)
    result = await service.list_for_user(current_user.id)
    return SuccessResponse(data=result)


@router.get("/{interview_id}", response_model=SuccessResponse[InterviewResponse])
async def get_interview(
    interview_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = InterviewService(db)
    result = await service.get(interview_id, current_user.id)
    return SuccessResponse(data=result)


@router.get("/{interview_id}/current-question", response_model=SuccessResponse[CurrentQuestionResponse])
async def get_current_question(
    interview_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = InterviewService(db)
    result = await service.get_current_question(interview_id, current_user.id)
    return SuccessResponse(data=result)


@router.post("/{interview_id}/answer", response_model=SuccessResponse[AnswerEvaluationResponse])
async def submit_answer(
    interview_id: str,
    payload: SubmitAnswerRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider_dep),
):
    service = InterviewService(db, llm_provider=llm_provider)
    result = await service.submit_answer(interview_id, current_user.id, payload)
    return SuccessResponse(message="Answer evaluated", data=result)


@router.post("/{interview_id}/answer/audio", response_model=SuccessResponse[AnswerEvaluationResponse])
async def submit_audio_answer(
    interview_id: str,
    question: str = Form(...),
    category: QuestionCategory = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider_dep),
):
    """Module 9 (Speech Analysis) wired into the interview flow — voice mode.
    NOT LIVE-TESTED end-to-end: Whisper transcription can't run in this build
    environment (see app/services/speech/transcription.py for why)."""
    import os
    import tempfile

    content = await file.read()
    if len(content) > settings.MAX_MEDIA_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Audio file exceeds {settings.MAX_MEDIA_UPLOAD_SIZE_MB}MB")

    suffix = "." + (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "wav")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = InterviewService(db, llm_provider=llm_provider)
        result = await service.submit_audio_answer(interview_id, current_user.id, question, category.value, tmp_path)
    finally:
        os.unlink(tmp_path)

    return SuccessResponse(message="Audio answer transcribed and evaluated", data=result)


@router.post("/{interview_id}/answer/video", response_model=SuccessResponse[AnswerEvaluationResponse])
async def submit_video_answer(
    interview_id: str,
    question: str = Form(...),
    category: QuestionCategory = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider_dep),
):
    """Modules 9+10 wired into the interview flow — video mode. NOT LIVE-
    TESTED end-to-end: needs both Whisper and the MediaPipe model files (see
    SETUP.md to download those, and transcription.py / frame_processor.py
    for why they can't be verified from this build environment)."""
    import os
    import tempfile

    content = await file.read()
    if len(content) > settings.MAX_MEDIA_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Video file exceeds {settings.MAX_MEDIA_UPLOAD_SIZE_MB}MB")

    suffix = "." + (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "mp4")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = InterviewService(db, llm_provider=llm_provider)
        result = await service.submit_video_answer(
            interview_id, current_user.id, question, category.value, tmp_path,
            settings.FACE_LANDMARKER_MODEL_PATH, settings.POSE_LANDMARKER_MODEL_PATH,
        )
    finally:
        os.unlink(tmp_path)

    return SuccessResponse(message="Video answer analyzed and evaluated", data=result)


@router.get("/{interview_id}/answers", response_model=SuccessResponse[list[AnswerEvaluationResponse]])
async def list_answers(
    interview_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = InterviewService(db)
    result = await service.list_answers(interview_id, current_user.id)
    return SuccessResponse(data=result)
