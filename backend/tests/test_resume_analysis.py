from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def _upload_fixture(client, token):
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=_auth_header(token),
    )
    return resp.json()["data"]["id"]


async def test_parse_extracts_skills_across_all_categories(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)

    resp = await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    assert resp.status_code == 200
    skills = resp.json()["data"]["skills"]

    assert "Python" in skills["programming_languages"]
    assert "TypeScript" in skills["programming_languages"]
    assert "React" in skills["frameworks"]
    assert "FastAPI" in skills["frameworks"]
    assert "PostgreSQL" in skills["databases"]
    assert "AWS" in skills["cloud"]
    assert "Kubernetes" in skills["cloud"]
    assert "Leadership" in skills["soft_skills"]
    assert "AWS Certified Solutions Architect" in skills["certifications"]


async def test_parse_extracts_links(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)

    resp = await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    links = resp.json()["data"]["links"]
    assert links["github"] == "https://github.com/janedoe"
    assert links["linkedin"] == "https://linkedin.com/in/janedoe"


async def test_parse_extracts_experience_with_correct_boundaries(client, registered_user):
    """Regression test for the entry-boundary bug caught during manual
    verification: dates must close the entry that precedes them, not open
    the next one."""
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)

    resp = await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    experience = resp.json()["data"]["experience"]
    assert len(experience) == 2

    assert experience[0]["title"] == "Senior Software Engineer"
    assert experience[0]["company"] == "Acme Corporation"
    assert experience[0]["duration"] == "Jan 2022 - Present"
    assert "microservices" in experience[0]["description"]

    assert experience[1]["title"] == "Software Engineer"
    assert experience[1]["company"] == "Globex Inc"
    assert experience[1]["duration"] == "Jun 2019 - Dec 2021"


async def test_parse_extracts_education(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)

    resp = await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    education = resp.json()["data"]["education"]
    assert len(education) == 1
    assert education[0]["degree"] == "B.S"
    assert education[0]["institution"] == "Stanford University"
    assert education[0]["duration"] == "2015 - 2019"


async def test_parse_extracts_projects_and_summary(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)

    resp = await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    data = resp.json()["data"]
    assert len(data["projects"]) == 1
    assert data["projects"][0]["name"] == "Personal Finance Tracker"
    assert "scalable APIs" in data["summary"]


async def test_analysis_requires_parse_first(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)

    resp = await client.get(f"/api/resume/{resume_id}/analysis", headers=_auth_header(token))
    assert resp.status_code == 404


async def test_get_analysis_after_parsing(client, registered_user):
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)
    await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))

    resp = await client.get(f"/api/resume/{resume_id}/analysis", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["resume_id"] == resume_id


async def test_reparsing_replaces_rather_than_duplicates(client, registered_user, test_db):
    _, _, token = registered_user
    resume_id = await _upload_fixture(client, token)

    await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))
    await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(token))

    count = await test_db.resume_analysis.count_documents({"resume_id": resume_id})
    assert count == 1


async def test_parse_requires_ownership(client, registered_user):
    _, _, owner_token = registered_user
    resume_id = await _upload_fixture(client, owner_token)

    await client.post(
        "/api/auth/register",
        json={"name": "Intruder", "email": "intruder@example.com", "password": "StrongPass1!"},
    )
    intruder_login = await client.post("/api/auth/login", json={"email": "intruder@example.com", "password": "StrongPass1!"})
    intruder_token = intruder_login.json()["data"]["access_token"]

    resp = await client.post(f"/api/resume/{resume_id}/parse", headers=_auth_header(intruder_token))
    assert resp.status_code == 403
