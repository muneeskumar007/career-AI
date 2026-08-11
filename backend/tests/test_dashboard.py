from pathlib import Path

from app.api.deps import get_llm_provider_dep
from app.main import app
from tests.fake_llm_provider import FAKE_EVALUATION_RESPONSE, FAKE_NEXT_QUESTION_RESPONSE, FakeLLMProvider

FIXTURES = Path(__file__).parent / "fixtures"
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


async def test_dashboard_empty_state(client, registered_user):
    _, _, token = registered_user
    resp = await client.get("/api/dashboard", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["practice_count"] == 0
    assert data["recent_interviews"] == []
    assert data["resume_history"] == []
    assert all(not a["unlocked"] for a in data["achievements"])


async def test_dashboard_reflects_resume_upload(client, registered_user):
    _, _, token = registered_user
    await _upload_and_parse_resume(client, token)

    resp = await client.get("/api/dashboard", headers=_auth_header(token))
    data = resp.json()["data"]
    assert len(data["resume_history"]) == 1
    assert data["current_skill_counts"]["programming_languages"] > 0
    achievements_by_id = {a["id"]: a["unlocked"] for a in data["achievements"]}
    assert achievements_by_id["first_resume"] is True
    assert achievements_by_id["first_interview"] is False


async def test_dashboard_practice_count_only_counts_completed(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(response_map=INTERVIEW_RESPONSE_MAP)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        # Interview 1: started but not completed
        await client.post("/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token))

        # Interview 2: fully completed
        start2 = await client.post("/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token))
        interview_id_2 = start2.json()["data"]["interview_id"]
        for _ in range(8):
            await client.post(
                f"/api/interview/{interview_id_2}/answer",
                json={"question": "Q", "category": "hr", "answer_text": "A"},
                headers=_auth_header(token),
            )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    resp = await client.get("/api/dashboard", headers=_auth_header(token))
    data = resp.json()["data"]
    assert data["practice_count"] == 1  # only the completed one counts
    assert len(data["recent_interviews"]) == 2  # but both show in history
    achievements_by_id = {a["id"]: a["unlocked"] for a in data["achievements"]}
    assert achievements_by_id["first_interview"] is True


async def test_dashboard_recent_interview_shows_average_score(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(response_map=INTERVIEW_RESPONSE_MAP)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        start = await client.post("/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token))
        interview_id = start.json()["data"]["interview_id"]
        await client.post(
            f"/api/interview/{interview_id}/answer",
            json={"question": "Q", "category": "hr", "answer_text": "A"},
            headers=_auth_header(token),
        )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    resp = await client.get("/api/dashboard", headers=_auth_header(token))
    recent = resp.json()["data"]["recent_interviews"][0]
    assert recent["overall_score"] == FAKE_EVALUATION_RESPONSE["overall_score"]


async def test_dashboard_isolated_per_user(client, registered_user):
    _, _, token = registered_user
    await _upload_and_parse_resume(client, token)

    await client.post(
        "/api/auth/register",
        json={"name": "Other Dash User", "email": "otherdash@example.com", "password": "StrongPass1!"},
    )
    other_login = await client.post("/api/auth/login", json={"email": "otherdash@example.com", "password": "StrongPass1!"})
    other_token = other_login.json()["data"]["access_token"]

    resp = await client.get("/api/dashboard", headers=_auth_header(other_token))
    assert resp.json()["data"]["resume_history"] == []
