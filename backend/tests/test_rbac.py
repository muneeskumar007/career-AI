async def test_candidate_cannot_list_users(client, registered_user):
    _, _, token = registered_user
    resp = await client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ForbiddenException"


async def test_admin_can_list_and_manage_users(client, test_db, registered_user):
    candidate_email, _, candidate_token = registered_user

    # Promote a second, freshly-created user to admin directly in the test DB
    # (simulates a seeded admin — there is no public "become admin" endpoint).
    await client.post(
        "/api/auth/register",
        json={"name": "Admin User", "email": "admin@example.com", "password": "StrongPass1!"},
    )
    await test_db.users.update_one({"email": "admin@example.com"}, {"$set": {"role": "admin"}})
    admin_login = await client.post("/api/auth/login", json={"email": "admin@example.com", "password": "StrongPass1!"})
    admin_token = admin_login.json()["data"]["access_token"]

    list_resp = await client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_resp.status_code == 200
    assert list_resp.json()["data"]["total"] >= 2

    candidate_doc = await test_db.users.find_one({"email": candidate_email})
    candidate_id = str(candidate_doc["_id"])

    role_resp = await client.patch(
        f"/api/users/{candidate_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "recruiter"},
    )
    assert role_resp.status_code == 200
    assert role_resp.json()["data"]["role"] == "recruiter"

    status_resp = await client.patch(
        f"/api/users/{candidate_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["is_active"] is False

    # Deactivated user can no longer log in
    blocked_login = await client.post(
        "/api/auth/login", json={"email": candidate_email, "password": "StrongPass1!"}
    )
    assert blocked_login.status_code == 403
