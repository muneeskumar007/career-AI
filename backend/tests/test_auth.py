async def test_register_success(client):
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Jane Doe", "email": "jane@example.com", "password": "StrongPass1!"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == "jane@example.com"
    assert body["data"]["role"] == "candidate"
    assert body["data"]["is_verified"] is False
    assert "password" not in body["data"]
    assert "password_hash" not in body["data"]


async def test_register_duplicate_email_rejected(client):
    payload = {"name": "Jane Doe", "email": "dup@example.com", "password": "StrongPass1!"}
    first = await client.post("/api/auth/register", json=payload)
    second = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "UserAlreadyExistsException"


async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Jane Doe", "email": "weak@example.com", "password": "weakpass"},
    )
    assert resp.status_code == 422


async def test_register_cannot_inject_role(client):
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Sneaky", "email": "sneaky@example.com", "password": "StrongPass1!", "role": "admin"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["role"] == "candidate"


async def test_login_success_and_profile_access(client):
    await client.post(
        "/api/auth/register",
        json={"name": "John Smith", "email": "john@example.com", "password": "StrongPass1!"},
    )
    login_resp = await client.post(
        "/api/auth/login", json={"email": "john@example.com", "password": "StrongPass1!"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    assert "careerai_refresh_token" in login_resp.cookies

    me_resp = await client.get("/api/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "john@example.com"


async def test_login_wrong_password_rejected(client):
    await client.post(
        "/api/auth/register",
        json={"name": "Amy", "email": "amy@example.com", "password": "StrongPass1!"},
    )
    resp = await client.post("/api/auth/login", json={"email": "amy@example.com", "password": "WrongPass1!"})
    assert resp.status_code == 401


async def test_login_unknown_email_rejected(client):
    resp = await client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "StrongPass1!"})
    assert resp.status_code == 401


async def test_profile_requires_auth(client):
    resp = await client.get("/api/profile/me")
    assert resp.status_code == 401


async def test_profile_rejects_garbage_token(client):
    resp = await client.get("/api/profile/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


async def test_refresh_issues_new_access_token(client):
    await client.post(
        "/api/auth/register",
        json={"name": "Refresher", "email": "refresh@example.com", "password": "StrongPass1!"},
    )
    login = await client.post("/api/auth/login", json={"email": "refresh@example.com", "password": "StrongPass1!"})
    old_token = login.json()["data"]["access_token"]

    refresh_resp = await client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 200
    new_token = refresh_resp.json()["data"]["access_token"]
    assert new_token != old_token

    me = await client.get("/api/profile/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me.status_code == 200


async def test_logout_invalidates_refresh_token(client):
    await client.post(
        "/api/auth/register",
        json={"name": "Loggy", "email": "logout@example.com", "password": "StrongPass1!"},
    )
    login = await client.post("/api/auth/login", json={"email": "logout@example.com", "password": "StrongPass1!"})
    token = login.json()["data"]["access_token"]

    logout_resp = await client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # cookie jar still has the old refresh cookie value client-side; server
    # should now reject it since refresh_token_version was incremented.
    refresh_resp = await client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 401


async def test_change_password_flow(client, registered_user):
    email, old_password, token = registered_user
    resp = await client.post(
        "/api/profile/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": old_password, "new_password": "NewStrongPass1!"},
    )
    assert resp.status_code == 200

    old_login = await client.post("/api/auth/login", json={"email": email, "password": old_password})
    assert old_login.status_code == 401

    new_login = await client.post("/api/auth/login", json={"email": email, "password": "NewStrongPass1!"})
    assert new_login.status_code == 200


async def test_forgot_password_does_not_leak_account_existence(client):
    known = await client.post("/api/auth/forgot-password", json={"email": "candidate@example.com"})
    unknown = await client.post("/api/auth/forgot-password", json={"email": "ghost@example.com"})
    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]


async def test_update_profile(client, registered_user):
    _, _, token = registered_user
    resp = await client.put(
        "/api/profile/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Name", "phone": "+1-555-0100"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Updated Name"
    assert resp.json()["data"]["phone"] == "+1-555-0100"
