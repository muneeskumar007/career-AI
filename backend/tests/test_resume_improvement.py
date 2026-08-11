from pathlib import Path

from app.api.deps import get_llm_provider_dep
from app.main import app
from tests.fake_llm_provider import FAKE_RESUME_IMPROVEMENT_RESPONSE, FakeLLMProvider

FIXTURES = Path(__file__).parent / "fixtures"


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def _upload_and_parse_resume(client, token):
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    upload_resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=_auth_header(token),
    )
    resume_id = upload_resp.json()["data"]["id"]
    await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    return resume_id


async def test_improve_resume_returns_rewritten_content(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(json_responses=FAKE_RESUME_IMPROVEMENT_RESPONSE)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(f"/api/resume/{resume_id}/improve", json={}, headers=_auth_header(token))
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["improved_summary"] == FAKE_RESUME_IMPROVEMENT_RESPONSE["improved_summary"]
    assert len(data["improved_experience"]) == 1
    assert fake.call_count == 1


async def test_improve_resume_prompt_includes_never_fabricate_rule(client, registered_user):
    """The 'never invent experience' constraint has to actually reach the
    model — verify it's really in the system prompt sent, not just declared
    in a docstring somewhere."""
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(json_responses=FAKE_RESUME_IMPROVEMENT_RESPONSE)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        await client.post(f"/api/resume/{resume_id}/improve", json={}, headers=_auth_header(token))
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    assert "never invent experience" in fake.last_system_prompt.lower()


async def test_improve_resume_includes_actual_resume_content_in_prompt(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(json_responses=FAKE_RESUME_IMPROVEMENT_RESPONSE)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        await client.post(f"/api/resume/{resume_id}/improve", json={}, headers=_auth_header(token))
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    # The candidate's real experience should end up in the prompt, not a placeholder
    assert "Acme Corporation" in fake.last_user_prompt


async def test_improve_resume_handles_malformed_llm_response(client, registered_user):
    """If the model returns JSON that doesn't match the expected schema, this
    should surface as a clean 502, not an unhandled 500."""
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(json_responses={"totally": "wrong shape"})
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(f"/api/resume/{resume_id}/improve", json={}, headers=_auth_header(token))
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    assert resp.status_code == 502


async def test_improve_resume_handles_provider_failure(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)

    fake = FakeLLMProvider(raise_error=True)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(f"/api/resume/{resume_id}/improve", json={}, headers=_auth_header(token))
    finally:
        del app.dependency_overrides[get_llm_provider_dep]

    assert resp.status_code == 502


async def test_improve_resume_requires_parsed_analysis(client, registered_user):
    """Improving before parsing should fail cleanly, not crash."""
    _, _, token = registered_user
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    upload_resp = await client.post(
        "/api/resume/upload", files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}, headers=_auth_header(token)
    )
    resume_id = upload_resp.json()["data"]["id"]  # deliberately not parsed

    # This endpoint always needs the LLM provider, so — same reasoning as
    # test_generate_questions_rejects_invalid_difficulty — give it a working
    # fake so the "not parsed yet" business-logic error is what's tested.
    fake = FakeLLMProvider(json_responses=FAKE_RESUME_IMPROVEMENT_RESPONSE)
    app.dependency_overrides[get_llm_provider_dep] = lambda: fake
    try:
        resp = await client.post(f"/api/resume/{resume_id}/improve", json={}, headers=_auth_header(token))
    finally:
        del app.dependency_overrides[get_llm_provider_dep]
    assert resp.status_code == 404
