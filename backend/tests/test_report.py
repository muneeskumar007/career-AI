from pathlib import Path

from app.api.deps import get_llm_provider_dep
from app.main import app
from tests.fake_llm_provider import FAKE_EVALUATION_RESPONSE, FAKE_NEXT_QUESTION_RESPONSE, FakeLLMProvider

FIXTURES = Path(__file__).parent / "fixtures"
INTERVIEW_RESPONSE_MAP = {"overall_score": FAKE_EVALUATION_RESPONSE, "reasoning": FAKE_NEXT_QUESTION_RESPONSE}

JD_TEXT = """Senior Backend Engineer

REQUIREMENTS
- Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes

PREFERRED
- GraphQL, Terraform
"""


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


async def test_report_requires_at_least_a_resume(client, registered_user):
    _, _, token = registered_user
    resp = await client.get("/api/report", headers=_auth_header(token))
    assert resp.status_code == 404


async def test_report_includes_resume_score_after_parsing(client, registered_user):
    _, _, token = registered_user
    await _upload_and_parse_resume(client, token)

    resp = await client.get("/api/report", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["resume_score"] is not None
    assert data["resume_score"] > 0
    assert data["ats_score"] is None  # no ATS comparison run yet
    assert data["interview_score"] is None  # no interview yet


async def test_report_includes_ats_score_after_comparison(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(token=token, client=client)
    jd_resp = await client.post("/api/job", json={"raw_text": JD_TEXT}, headers=_auth_header(token))
    jd_id = jd_resp.json()["data"]["id"]
    await client.post("/api/ats/compare", json={"resume_id": resume_id, "job_description_id": jd_id}, headers=_auth_header(token))

    resp = await client.get("/api/report", headers=_auth_header(token))
    data = resp.json()["data"]
    assert data["ats_score"] is not None
    assert len(data["strong_skills"]) > 0
    assert len(data["weak_skills"]) > 0


async def test_report_includes_interview_scores_after_completed_interview(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(response_map=INTERVIEW_RESPONSE_MAP)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        start_resp = await client.post("/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token))
        interview_id = start_resp.json()["data"]["interview_id"]
        for _ in range(8):
            await client.post(
                f"/api/interview/{interview_id}/answer",
                json={"question": "Q", "category": "hr", "answer_text": "A reasonable answer."},
                headers=_auth_header(token),
            )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    resp = await client.get("/api/report", headers=_auth_header(token))
    data = resp.json()["data"]
    assert data["interview_score"] == FAKE_EVALUATION_RESPONSE["overall_score"]
    assert data["technical_score"] == FAKE_EVALUATION_RESPONSE["technical_accuracy"]
    assert data["communication_score"] == FAKE_EVALUATION_RESPONSE["communication"]


async def test_progress_history_tracks_completed_interviews(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(response_map=INTERVIEW_RESPONSE_MAP)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        start_resp = await client.post("/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token))
        interview_id = start_resp.json()["data"]["interview_id"]
        for _ in range(8):
            await client.post(
                f"/api/interview/{interview_id}/answer",
                json={"question": "Q", "category": "hr", "answer_text": "A"},
                headers=_auth_header(token),
            )
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    resp = await client.get("/api/report/progress", headers=_auth_header(token))
    assert resp.status_code == 200
    points = resp.json()["data"]["points"]
    assert len(points) == 1
    assert points[0]["interview_id"] == interview_id


async def test_progress_history_excludes_in_progress_interviews(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(response_map=INTERVIEW_RESPONSE_MAP)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        await client.post("/api/interview/start", json={"resume_id": resume_id, "mode": "text"}, headers=_auth_header(token))
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    resp = await client.get("/api/report/progress", headers=_auth_header(token))
    assert resp.json()["data"]["points"] == []


async def test_export_pdf_returns_valid_pdf(client, registered_user):
    _, _, token = registered_user
    await _upload_and_parse_resume(client, token)

    resp = await client.get("/api/report/export-pdf", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")


async def test_report_scoped_to_specific_resume(client, registered_user):
    _, _, token = registered_user
    resume_id_1 = await _upload_and_parse_resume(client, token)
    resume_id_2 = await _upload_and_parse_resume(client, token)
    assert resume_id_1 != resume_id_2

    resp = await client.get(f"/api/report?resume_id={resume_id_1}", headers=_auth_header(token))
    assert resp.json()["data"]["resume_id"] == resume_id_1
