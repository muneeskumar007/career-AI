from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

JD_TEXT = """Senior Backend Engineer at TechCorp

We are looking for a Senior Backend Engineer to join our growing team.

REQUIREMENTS
- 5+ years of experience with Python
- Strong experience with FastAPI or Django
- Experience with PostgreSQL and MongoDB
- Experience with AWS and Docker
- Experience with Kubernetes for container orchestration
- Strong communication and leadership skills

PREFERRED
- Experience with React
- AWS certification
- Experience with GraphQL
- Familiarity with Terraform
"""


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def _upload_resume(client, token):
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=_auth_header(token),
    )
    return resp.json()["data"]["id"]


async def _create_jd(client, token, text=JD_TEXT):
    resp = await client.post(
        "/api/job",
        json={"title": "Senior Backend Engineer", "company": "TechCorp", "raw_text": text},
        headers=_auth_header(token),
    )
    return resp.json()["data"]["id"]


async def test_create_and_list_job_descriptions(client, registered_user):
    _, _, token = registered_user
    jd_id = await _create_jd(client, token)
    assert jd_id

    list_resp = await client.get("/api/job", headers=_auth_header(token))
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1


async def test_job_description_too_short_rejected(client, registered_user):
    _, _, token = registered_user
    resp = await client.post(
        "/api/job", json={"raw_text": "too short"}, headers=_auth_header(token)
    )
    assert resp.status_code == 422


async def test_ats_compare_auto_parses_unparsed_resume(client, registered_user):
    """Comparing shouldn't require the caller to remember to call /parse first."""
    _, _, token = registered_user
    resume_id = await _upload_resume(client, token)
    jd_id = await _create_jd(client, token)

    resp = await client.post(
        "/api/ats/compare",
        json={"resume_id": resume_id, "job_description_id": jd_id},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert 0 <= data["ats_score"] <= 100
    assert data["skill_match_percent"] > 50  # the fixture resume genuinely matches most of this JD


async def test_ats_compare_matches_expected_skills(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_resume(client, token)
    jd_id = await _create_jd(client, token)

    resp = await client.post(
        "/api/ats/compare",
        json={"resume_id": resume_id, "job_description_id": jd_id},
        headers=_auth_header(token),
    )
    data = resp.json()["data"]
    assert "Python" in data["matched_skills"]["programming_languages"]
    assert "FastAPI" in data["matched_skills"]["frameworks"]
    assert "AWS" in data["matched_skills"]["cloud"]
    # GraphQL and Terraform are only in the PREFERRED section and absent from the resume
    assert "GraphQL" in data["missing_skills"]["frameworks"]
    assert "Terraform" in data["missing_skills"]["cloud"]


async def test_ats_result_is_retrievable_after_compare(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_resume(client, token)
    jd_id = await _create_jd(client, token)

    await client.post(
        "/api/ats/compare", json={"resume_id": resume_id, "job_description_id": jd_id}, headers=_auth_header(token)
    )
    resp = await client.get(f"/api/ats/{resume_id}/{jd_id}", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["resume_id"] == resume_id


async def test_ats_result_not_found_before_comparing(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_resume(client, token)
    jd_id = await _create_jd(client, token)

    resp = await client.get(f"/api/ats/{resume_id}/{jd_id}", headers=_auth_header(token))
    assert resp.status_code == 404


async def test_ats_compare_recompute_replaces_not_duplicates(client, registered_user, test_db):
    _, _, token = registered_user
    resume_id = await _upload_resume(client, token)
    jd_id = await _create_jd(client, token)

    await client.post("/api/ats/compare", json={"resume_id": resume_id, "job_description_id": jd_id}, headers=_auth_header(token))
    await client.post("/api/ats/compare", json={"resume_id": resume_id, "job_description_id": jd_id}, headers=_auth_header(token))

    count = await test_db.ats_results.count_documents({"resume_id": resume_id, "job_description_id": jd_id})
    assert count == 1


async def test_jd_ownership_enforced_for_comparison(client, registered_user):
    _, _, owner_token = registered_user
    resume_id = await _upload_resume(client, owner_token)
    jd_id = await _create_jd(client, owner_token)

    await client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "jdintruder@example.com", "password": "StrongPass1!"},
    )
    other_login = await client.post("/api/auth/login", json={"email": "jdintruder@example.com", "password": "StrongPass1!"})
    other_token = other_login.json()["data"]["access_token"]
    other_resume_id = await _upload_resume(client, other_token)

    # Other user has their own resume but tries to compare against the owner's JD
    resp = await client.post(
        "/api/ats/compare",
        json={"resume_id": other_resume_id, "job_description_id": jd_id},
        headers=_auth_header(other_token),
    )
    assert resp.status_code == 403
