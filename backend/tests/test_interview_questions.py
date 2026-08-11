from pathlib import Path

from app.api.deps import get_llm_provider_dep
from app.main import app
from tests.fake_llm_provider import FAKE_QUESTION_SET_RESPONSE, FakeLLMProvider

FIXTURES = Path(__file__).parent / "fixtures"


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


async def test_generate_questions_returns_all_categories(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(json_responses=FAKE_QUESTION_SET_RESPONSE)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(
            "/api/interview/questions", json={"resume_id": resume_id, "difficulty": "mid"}, headers=_auth_header(token)
        )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    assert resp.status_code == 200
    data = resp.json()["data"]
    for category in ["hr_questions", "technical_questions", "project_questions", "scenario_questions", "behavioral_questions", "coding_questions"]:
        assert len(data[category]) > 0


async def test_generate_questions_rejects_invalid_difficulty(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    # This endpoint always needs the LLM provider for its actual work, so
    # FastAPI resolves that dependency regardless of body validity — provide
    # a working fake so the *difficulty* validation is what's actually being
    # tested here, not provider availability.
    fake = FakeLLMProvider(json_responses=FAKE_QUESTION_SET_RESPONSE)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(
            "/api/interview/questions", json={"resume_id": resume_id, "difficulty": "expert"}, headers=_auth_header(token)
        )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]
    assert resp.status_code == 422


async def test_generate_questions_incomplete_response_rejected(client, registered_user):
    """If the model drops a required category, that should be a clean 502,
    not a partially-broken response silently returned to the user."""
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    incomplete = {k: v for k, v in FAKE_QUESTION_SET_RESPONSE.items() if k != "coding_questions"}
    fake = FakeLLMProvider(json_responses=incomplete)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(
            "/api/interview/questions", json={"resume_id": resume_id, "difficulty": "mid"}, headers=_auth_header(token)
        )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    assert resp.status_code == 502


async def test_generate_questions_with_job_description_includes_jd_in_prompt(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)
    jd_resp = await client.post(
        "/api/job",
        json={"raw_text": "We need a Senior Backend Engineer with Kubernetes and GraphQL experience."},
        headers=_auth_header(token),
    )
    jd_id = jd_resp.json()["data"]["id"]

    fake = FakeLLMProvider(json_responses=FAKE_QUESTION_SET_RESPONSE)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(
            "/api/interview/questions",
            json={"resume_id": resume_id, "job_description_id": jd_id, "difficulty": "senior"},
            headers=_auth_header(token),
        )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    assert resp.status_code == 200
    assert "GraphQL" in fake.last_user_prompt
