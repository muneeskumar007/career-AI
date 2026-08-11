from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def test_upload_pdf_extracts_text_and_basic_info(client, registered_user):
    _, _, token = registered_user
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()

    resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["file_type"] == "pdf"
    assert data["status"] == "uploaded"
    assert data["basic_info"]["email"] == "jane.doe@example.com"
    assert data["basic_info"]["name"] == "Jane Doe"


async def test_upload_docx_extracts_text(client, registered_user):
    _, _, token = registered_user
    docx_bytes = (FIXTURES / "sample_resume.docx").read_bytes()

    resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["file_type"] == "docx"


async def test_upload_requires_auth(client):
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    resp = await client.post("/api/resume/upload", files={"file": ("resume.pdf", pdf_bytes, "application/pdf")})
    assert resp.status_code == 401


async def test_upload_rejects_disallowed_extension(client, registered_user):
    _, _, token = registered_user
    resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.txt", b"just some text", "text/plain")},
        headers=_auth_header(token),
    )
    assert resp.status_code == 415


async def test_upload_rejects_oversized_file(client, registered_user):
    _, _, token = registered_user
    # 11MB of PDF-prefixed junk — extension and magic bytes pass, size doesn't
    oversized = b"%PDF-1.4\n" + b"0" * (11 * 1024 * 1024)
    resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", oversized, "application/pdf")},
        headers=_auth_header(token),
    )
    assert resp.status_code == 413


async def test_upload_rejects_content_mismatching_extension(client, registered_user):
    _, _, token = registered_user
    # .pdf extension, but the bytes are plainly not a PDF (no %PDF- magic header)
    fake_pdf = b"this is definitely not a real pdf file"
    resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


async def test_list_and_get_resume(client, registered_user):
    _, _, token = registered_user
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    upload_resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=_auth_header(token),
    )
    resume_id = upload_resp.json()["data"]["id"]

    list_resp = await client.get("/api/resume", headers=_auth_header(token))
    assert list_resp.status_code == 200
    assert list_resp.json()["data"]["total"] == 1

    detail_resp = await client.get(f"/api/resume/{resume_id}", headers=_auth_header(token))
    assert detail_resp.status_code == 200
    assert "Jane Doe" in detail_resp.json()["data"]["raw_text"]


async def test_resume_ownership_is_enforced(client, registered_user):
    _, _, owner_token = registered_user
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    upload_resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=_auth_header(owner_token),
    )
    resume_id = upload_resp.json()["data"]["id"]

    await client.post(
        "/api/auth/register",
        json={"name": "Other User", "email": "other@example.com", "password": "StrongPass1!"},
    )
    other_login = await client.post("/api/auth/login", json={"email": "other@example.com", "password": "StrongPass1!"})
    other_token = other_login.json()["data"]["access_token"]

    resp = await client.get(f"/api/resume/{resume_id}", headers=_auth_header(other_token))
    assert resp.status_code == 403


async def test_delete_resume(client, registered_user):
    _, _, token = registered_user
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    upload_resp = await client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=_auth_header(token),
    )
    resume_id = upload_resp.json()["data"]["id"]

    delete_resp = await client.delete(f"/api/resume/{resume_id}", headers=_auth_header(token))
    assert delete_resp.status_code == 200

    get_resp = await client.get(f"/api/resume/{resume_id}", headers=_auth_header(token))
    assert get_resp.status_code == 404
