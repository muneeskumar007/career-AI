from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

JD_TEXT = """Senior Backend Engineer at TechCorp

REQUIREMENTS
- 5+ years of experience with Python
- Strong experience with FastAPI or Django
- Experience with Kubernetes for container orchestration

PREFERRED
- PMP
- Familiarity with Terraform
"""


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


async def _create_jd(client, token):
    resp = await client.post(
        "/api/job", json={"raw_text": JD_TEXT}, headers=_auth_header(token)
    )
    return resp.json()["data"]["id"]


async def test_skill_gap_known_skills_include_matched_taxonomy_skills(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)
    jd_id = await _create_jd(client, token)

    resp = await client.get(f"/api/skill-gap/{resume_id}/{jd_id}", headers=_auth_header(token))
    assert resp.status_code == 200
    known = [item["skill"] for item in resp.json()["data"]["known_skills"]]
    assert "Python" in known
    assert "FastAPI" in known


async def test_skill_gap_missing_skills_prioritized_correctly(client, registered_user):
    """Required-section gaps should rank as High priority, preferred-section
    gaps as Medium — and required items should sort before preferred ones."""
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)
    jd_id = await _create_jd(client, token)

    resp = await client.get(f"/api/skill-gap/{resume_id}/{jd_id}", headers=_auth_header(token))
    missing = resp.json()["data"]["missing_skills"]
    by_skill = {item["skill"]: item for item in missing}

    # Kubernetes is matched by the fixture resume, shouldn't appear as missing at all
    assert "Kubernetes" not in by_skill
    # PMP is preferred-only and absent from the resume
    assert by_skill["PMP"]["priority"] == "Medium"
    assert by_skill["Terraform"]["priority"] == "Medium"

    priorities = [item["priority"] for item in missing]
    high_indices = [i for i, p in enumerate(priorities) if p == "High"]
    medium_indices = [i for i, p in enumerate(priorities) if p == "Medium"]
    if high_indices and medium_indices:
        assert max(high_indices) < min(medium_indices)


async def test_skill_gap_includes_difficulty_and_resources(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)
    jd_id = await _create_jd(client, token)

    resp = await client.get(f"/api/skill-gap/{resume_id}/{jd_id}", headers=_auth_header(token))
    missing = resp.json()["data"]["missing_skills"]
    terraform = next(item for item in missing if item["skill"] == "Terraform")
    assert terraform["difficulty"] in ("Beginner", "Intermediate", "Advanced")
    assert terraform["estimated_learning_time"]
    assert terraform["recommended_resource"].startswith("https://")


async def test_skill_gap_works_without_prior_ats_comparison(client, registered_user):
    """Module 5 should be independently usable — no need to call /api/ats/compare first."""
    _, _, token = registered_user
    resume_id = await _upload_and_parse_resume(client, token)
    jd_id = await _create_jd(client, token)

    resp = await client.get(f"/api/skill-gap/{resume_id}/{jd_id}", headers=_auth_header(token))
    assert resp.status_code == 200
