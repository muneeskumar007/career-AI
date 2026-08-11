"""
Module 8: the interview session state machine. Orchestrates start → current
question → submit answer (evaluate + advance) → complete, delegating actual
generation/evaluation to AdaptiveQuestionService / AnswerEvaluatorService so
this class stays focused on state transitions and persistence, not prompting.
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.providers.base import LLMProvider
from app.models.interview import InterviewMode, InterviewStatus
from app.schemas.interview import (
    AnswerEvaluationResponse,
    CurrentQuestionResponse,
    InterviewResponse,
    StartInterviewRequest,
    SubmitAnswerRequest,
)
from app.services.interview.adaptive_question_service import AdaptiveQuestionService
from app.services.interview.evaluator import AnswerEvaluatorService
from app.services.job_description_service import JobDescriptionService
from app.services.parsing.context_builder import build_resume_context
from app.services.resume_analysis_service import ResumeAnalysisService
from app.utils.exceptions import AppException, ForbiddenException, InvalidTokenException, UserNotFoundException

MAX_QUESTIONS_PER_INTERVIEW = 8


class InterviewAlreadyCompleteException(AppException):
    status_code = 409
    message = "This interview has already been completed"


def _to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise InvalidTokenException("Invalid interview id")


def _interview_response(doc: dict) -> InterviewResponse:
    return InterviewResponse(
        id=str(doc["_id"]), resume_id=doc["resume_id"], job_description_id=doc.get("job_description_id"),
        mode=doc["mode"], status=doc["status"], question_count=doc["question_count"],
        created_at=doc["created_at"], completed_at=doc.get("completed_at"),
    )


def _answer_response(doc: dict) -> AnswerEvaluationResponse:
    return AnswerEvaluationResponse(
        id=str(doc["_id"]), interview_id=doc["interview_id"], question=doc["question"], category=doc["category"],
        answer_text=doc["answer_text"], technical_accuracy=doc.get("technical_accuracy"),
        completeness=doc.get("completeness"), communication=doc.get("communication"), grammar=doc.get("grammar"),
        problem_solving=doc.get("problem_solving"), overall_score=doc.get("overall_score"),
        feedback=doc.get("feedback"), speech_analysis=doc.get("speech_analysis"),
        video_analysis=doc.get("video_analysis"), created_at=doc["created_at"],
    )


class InterviewService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        llm_provider: LLMProvider | None = None,
    ):
        self.db = db
        self.interviews = db.interviews
        self.answers = db.interview_answers
        self.analysis_service = ResumeAnalysisService(db)
        self.jd_service = JobDescriptionService(db)
        self._llm_provider = llm_provider
        self._question_service: AdaptiveQuestionService | None = None
        self._evaluator: AnswerEvaluatorService | None = None

    @property
    def question_service(self) -> AdaptiveQuestionService:
        # Built lazily so read-only operations (list/get/current-question)
        # never need an LLM provider configured at all — only start() and
        # submit_answer() actually call the model.
        if self._question_service is None:
            self._question_service = AdaptiveQuestionService(llm_provider=self._llm_provider)
        return self._question_service

    @property
    def evaluator(self) -> AnswerEvaluatorService:
        if self._evaluator is None:
            self._evaluator = AnswerEvaluatorService(llm_provider=self._llm_provider)
        return self._evaluator

    async def _get_owned(self, interview_id: str, user_id: str) -> dict:
        doc = await self.interviews.find_one({"_id": _to_object_id(interview_id)})
        if not doc:
            raise UserNotFoundException("Interview not found")
        if doc["user_id"] != user_id:
            raise ForbiddenException("You don't have access to this interview")
        return doc

    async def _contexts(self, resume_id: str, job_description_id: str | None, user_id: str) -> tuple[str, str]:
        analysis = await self.analysis_service.get_latest(resume_id, user_id)
        resume_context = build_resume_context(analysis)
        jd_context = ""
        if job_description_id:
            jd_doc = await self.jd_service.get_owned(job_description_id, user_id)
            jd_context = jd_doc["raw_text"]
        return resume_context, jd_context

    async def start(self, user_id: str, payload: StartInterviewRequest) -> CurrentQuestionResponse:
        resume_context, jd_context = await self._contexts(payload.resume_id, payload.job_description_id, user_id)
        first = await self.question_service.generate_next(resume_context, jd_context, history=[])

        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id, "resume_id": payload.resume_id, "job_description_id": payload.job_description_id,
            "mode": payload.mode.value, "status": InterviewStatus.IN_PROGRESS.value, "question_count": 1,
            "current_question": first["question"], "current_category": first["category"],
            "created_at": now, "completed_at": None,
        }
        result = await self.interviews.insert_one(doc)

        return CurrentQuestionResponse(
            interview_id=str(result.inserted_id), question=first["question"], category=first["category"], question_number=1
        )

    async def get_current_question(self, interview_id: str, user_id: str) -> CurrentQuestionResponse:
        doc = await self._get_owned(interview_id, user_id)
        if doc["status"] == InterviewStatus.COMPLETED.value:
            return CurrentQuestionResponse(
                interview_id=interview_id, question="", category=doc.get("current_category") or "hr",
                question_number=doc["question_count"], is_complete=True,
            )
        return CurrentQuestionResponse(
            interview_id=interview_id, question=doc["current_question"], category=doc["current_category"],
            question_number=doc["question_count"],
        )

    async def submit_answer(self, interview_id: str, user_id: str, payload: SubmitAnswerRequest) -> AnswerEvaluationResponse:
        interview = await self._get_owned(interview_id, user_id)
        if interview["status"] == InterviewStatus.COMPLETED.value:
            raise InterviewAlreadyCompleteException()

        return await self._evaluate_and_advance(
            interview, payload.question, payload.category.value, payload.answer_text, user_id
        )

    async def submit_audio_answer(
        self, interview_id: str, user_id: str, question: str, category: str, audio_path: str
    ) -> AnswerEvaluationResponse:
        """Module 9 wired into the interview flow: transcribe -> analyze
        delivery -> evaluate the transcript as the answer -> advance, same as
        text mode from there. NOT LIVE-TESTED — see transcription.py."""
        from app.services.speech.speech_analyzer import analyze_speech
        from app.services.speech.transcription import transcribe_audio

        interview = await self._get_owned(interview_id, user_id)
        if interview["status"] == InterviewStatus.COMPLETED.value:
            raise InterviewAlreadyCompleteException()

        transcript, duration, word_timestamps = transcribe_audio(audio_path)
        speech_metrics = analyze_speech(transcript, duration, word_timestamps)

        return await self._evaluate_and_advance(
            interview, question, category, transcript, user_id, extra_fields={"speech_analysis": speech_metrics}
        )

    async def submit_video_answer(
        self, interview_id: str, user_id: str, question: str, category: str, video_path: str,
        face_model_path: str, pose_model_path: str,
    ) -> AnswerEvaluationResponse:
        """Module 10 (+ Module 9 for the audio track) wired into the
        interview flow. NOT LIVE-TESTED — see transcription.py and
        frame_processor.py for why."""
        from app.services.speech.speech_analyzer import analyze_speech
        from app.services.speech.transcription import transcribe_audio
        from app.services.video.frame_processor import process_frame
        from app.services.video.video_analyzer import aggregate_session, analyze_frame

        interview = await self._get_owned(interview_id, user_id)
        if interview["status"] == InterviewStatus.COMPLETED.value:
            raise InterviewAlreadyCompleteException()

        transcript, duration, word_timestamps = transcribe_audio(video_path)  # whisper reads the audio track directly
        speech_metrics = analyze_speech(transcript, duration, word_timestamps)

        import cv2

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        sample_every_n_frames = max(int(fps), 1)  # ~1 frame per second is plenty for posture/gaze trends
        frame_results, frame_index = [], 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % sample_every_n_frames == 0:
                analysis = process_frame(frame, face_model_path, pose_model_path)
                frame_results.append(analyze_frame(analysis))
            frame_index += 1
        cap.release()

        video_metrics = aggregate_session(frame_results)

        return await self._evaluate_and_advance(
            interview, question, category, transcript, user_id,
            extra_fields={"speech_analysis": speech_metrics, "video_analysis": video_metrics},
        )

    async def _evaluate_and_advance(
        self, interview: dict, question: str, category: str, answer_text: str, user_id: str, extra_fields: dict | None = None
    ) -> AnswerEvaluationResponse:
        interview_id = str(interview["_id"])
        resume_context, jd_context = await self._contexts(
            interview["resume_id"], interview.get("job_description_id"), user_id
        )
        evaluation = await self.evaluator.evaluate(question, answer_text, resume_context)

        now = datetime.now(timezone.utc)
        answer_doc = {
            "interview_id": interview_id, "user_id": user_id, "question": question,
            "category": category, "answer_text": answer_text, **evaluation,
            "speech_analysis": None, "video_analysis": None,
            **(extra_fields or {}), "created_at": now,
        }
        result = await self.answers.insert_one(answer_doc)
        answer_doc["_id"] = result.inserted_id

        history_cursor = self.answers.find({"interview_id": interview_id}).sort("created_at", 1)
        history = [{"question": a["question"], "answer": a["answer_text"]} async for a in history_cursor]

        if len(history) >= MAX_QUESTIONS_PER_INTERVIEW:
            await self.interviews.update_one(
                {"_id": interview["_id"]},
                {"$set": {"status": InterviewStatus.COMPLETED.value, "completed_at": now, "current_question": None}},
            )
        else:
            next_q = await self.question_service.generate_next(resume_context, jd_context, history)
            await self.interviews.update_one(
                {"_id": interview["_id"]},
                {
                    "$set": {"current_question": next_q["question"], "current_category": next_q["category"]},
                    "$inc": {"question_count": 1},
                },
            )

        return _answer_response(answer_doc)

    async def get(self, interview_id: str, user_id: str) -> InterviewResponse:
        return _interview_response(await self._get_owned(interview_id, user_id))

    async def list_answers(self, interview_id: str, user_id: str) -> list[AnswerEvaluationResponse]:
        await self._get_owned(interview_id, user_id)
        cursor = self.answers.find({"interview_id": interview_id}).sort("created_at", 1)
        return [_answer_response(doc) async for doc in cursor]

    async def list_for_user(self, user_id: str) -> list[InterviewResponse]:
        cursor = self.interviews.find({"user_id": user_id}).sort("created_at", -1)
        return [_interview_response(doc) async for doc in cursor]
