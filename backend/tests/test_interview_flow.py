from pathlib import Path

from app.api.deps import get_llm_provider_dep
from app.main import app
from tests.fake_llm_provider import FAKE_EVALUATION_RESPONSE, FAKE_NEXT_QUESTION_RESPONSE, FakeLLMProvider

FIXTURES = Path(__file__).parent / "fixtures"

# Distinguishes the two response shapes AdaptiveQuestionService and
# AnswerEvaluatorService expect, since both share one injected provider
# and their calls interleave through a single interview.
INTERVIEW_RESPONSE_MAP = {"overall_score": FAKE_EVALUATION_RESPONSE, "reasoning": FAKE_NEXT_QUESTION_RESPONSE}


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def _upload_and_parse_resume(client, token):
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    upload_resp = await client.post(
        "/api/resume/upload", files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}, headers=_auth_header(token)
    )
    resume_id = upload_resp.json()["data"]["id"]
    await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    return resume_id


def _override_llm():
    fake = FakeLLMProvider(response_map=INTERVIEW_RESPONSE_MAP)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    return fake


def _clear_llm_override():
    del app.dependency_overrides[get_llm_provider_dep]


async def test_start_interview_returns_first_question(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    _override_llm()
    try:
        resp = await client.post(
            "/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token)
        )
    finally:
        _clear_llm_override()

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["question"] == FAKE_NEXT_QUESTION_RESPONSE["question"]
    assert data["question_number"] == 1
    assert data["is_complete"] is False


async def test_submit_answer_evaluates_and_advances(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = _override_llm()
    try:
        start_resp = await client.post(
            "/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token)
        )
        interview_id = start_resp.json()["data"]["interview_id"]

        answer_resp = await client.post(
            f"/api/interview/{interview_id}/answer",
            json={"question": "Tell me about yourself.", "category": "hr", "answer_text": "I'm a backend engineer with 5 years of experience."},
            headers=_auth_header(token),
        )
    finally:
        _clear_llm_override()

    assert answer_resp.status_code == 200
    data = answer_resp.json()["data"]
    assert data["overall_score"] == FAKE_EVALUATION_RESPONSE["overall_score"]
    assert data["feedback"] == FAKE_EVALUATION_RESPONSE["feedback"]

    # Interview should have advanced to question 2
    current = await client.get(f"/api/interview/{interview_id}/current-question", headers=_auth_header(token))
    assert current.json()["data"]["question_number"] == 2
    assert current.json()["data"]["is_complete"] is False


async def test_interview_completes_after_max_questions(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = _override_llm()
    try:
        start_resp = await client.post(
            "/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token)
        )
        interview_id = start_resp.json()["data"]["interview_id"]

        # MAX_QUESTIONS_PER_INTERVIEW = 8; the start already used question 1,
        # so answering 8 times total should complete it.
        for _ in range(8):
            resp = await client.post(
                f"/api/interview/{interview_id}/answer",
                json={"question": "Q", "category": "hr", "answer_text": "A reasonably complete answer."},
                headers=_auth_header(token),
            )
            assert resp.status_code == 200
    finally:
        _clear_llm_override()

    interview = await client.get(f"/api/interview/{interview_id}", headers=_auth_header(token))
    assert interview.json()["data"]["status"] == "completed"
    assert interview.json()["data"]["completed_at"] is not None

    current = await client.get(f"/api/interview/{interview_id}/current-question", headers=_auth_header(token))
    assert current.json()["data"]["is_complete"] is True


async def test_cannot_answer_completed_interview(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = _override_llm()
    try:
        start_resp = await client.post(
            "/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token)
        )
        interview_id = start_resp.json()["data"]["interview_id"]
        for _ in range(8):
            await client.post(
                f"/api/interview/{interview_id}/answer",
                json={"question": "Q", "category": "hr", "answer_text": "A"},
                headers=_auth_header(token),
            )
        extra_resp = await client.post(
            f"/api/interview/{interview_id}/answer",
            json={"question": "Q", "category": "hr", "answer_text": "One too many"},
            headers=_auth_header(token),
        )
    finally:
        _clear_llm_override()

    assert extra_resp.status_code == 409


async def test_list_answers_returns_full_transcript(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = _override_llm()
    try:
        start_resp = await client.post(
            "/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token)
        )
        interview_id = start_resp.json()["data"]["interview_id"]
        await client.post(
            f"/api/interview/{interview_id}/answer",
            json={"question": "Q1", "category": "hr", "answer_text": "A1"},
            headers=_auth_header(token),
        )
        await client.post(
            f"/api/interview/{interview_id}/answer",
            json={"question": "Q2", "category": "technical", "answer_text": "A2"},
            headers=_auth_header(token),
        )
        answers_resp = await client.get(f"/api/interview/{interview_id}/answers", headers=_auth_header(token))
    finally:
        _clear_llm_override()

    answers = answers_resp.json()["data"]
    assert len(answers) == 2
    assert answers[0]["question"] == "Q1"
    assert answers[1]["question"] == "Q2"


async def test_interview_ownership_enforced(client, registered_user):
    _, _, owner_token = registered_user
    resume_id = await _upload_and_parse_resume(client, owner_token)

    fake = _override_llm()
    try:
        start_resp = await client.post(
            "/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(owner_token)
        )
    finally:
        _clear_llm_override()
    interview_id = start_resp.json()["data"]["interview_id"]

    await client.post(
        "/api/auth/register",
        json={"name": "Snoop", "email": "interviewsnoop@example.com", "password": "StrongPass1!"},
    )
    other_login = await client.post("/api/auth/login", json={"email": "interviewsnoop@example.com", "password": "StrongPass1!"})
    other_token = other_login.json()["data"]["access_token"]

    resp = await client.get(f"/api/interview/{interview_id}", headers=_auth_header(other_token))
    assert resp.status_code == 403
